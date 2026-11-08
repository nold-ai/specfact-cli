from __future__ import annotations

import ctypes
import hashlib
import ipaddress
import json
import os
import re
import shutil
import ssl
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import typing_extensions
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from specfact_cli.analyzers.code_analyzer import _build_semgrep_env


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Actual Windows native curl execution is required")
ROOT = Path(__file__).resolve().parents[3]
_CURLOPT_URL = 10002
_CURLOPT_PROXY = 10004
_CURLOPT_WRITEFUNCTION = 20011
_CURLOPT_POSTFIELDS = 10015
_CURLOPT_POSTFIELDSIZE = 60
_CURLOPT_CAINFO = 10065
_CURLOPT_TIMEOUT_MS = 155
_CURLE_PEER_FAILED_VERIFICATION = 60
_CURLE_SSL_CACERT_BADFILE = 77


class _Version(ctypes.Structure):
    version: bytes | None
    ssl_version: bytes | None
    protocols: ctypes._Pointer[ctypes.c_char_p]
    _fields_ = [
        ("age", ctypes.c_int),
        ("version", ctypes.c_char_p),
        ("version_num", ctypes.c_uint),
        ("host", ctypes.c_char_p),
        ("features", ctypes.c_int),
        ("ssl_version", ctypes.c_char_p),
        ("ssl_version_num", ctypes.c_long),
        ("libz_version", ctypes.c_char_p),
        ("protocols", ctypes.POINTER(ctypes.c_char_p)),
    ]


class _Curl:
    def __init__(self, filename: str) -> None:
        self.library = ctypes.CDLL(filename)
        self.library.curl_global_init.argtypes = [ctypes.c_long]
        self.library.curl_global_init.restype = ctypes.c_int
        self.library.curl_global_cleanup.argtypes = []
        self.library.curl_global_cleanup.restype = None
        self.library.curl_easy_init.argtypes = []
        self.library.curl_easy_init.restype = ctypes.c_void_p
        self.library.curl_easy_cleanup.argtypes = [ctypes.c_void_p]
        self.library.curl_easy_cleanup.restype = None
        self.library.curl_easy_perform.argtypes = [ctypes.c_void_p]
        self.library.curl_easy_perform.restype = ctypes.c_int
        self.library.curl_version_info.argtypes = [ctypes.c_int]
        self.library.curl_version_info.restype = ctypes.POINTER(_Version)
        for name in ("curl_escape", "curl_unescape"):
            function = getattr(self.library, name)
            function.argtypes = [ctypes.c_char_p, ctypes.c_int]
            function.restype = ctypes.c_void_p
        self.pointer_option = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p)(
            ("curl_easy_setopt", self.library)
        )
        self.long_option = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_long)(
            ("curl_easy_setopt", self.library)
        )
        assert self.library.curl_global_init(3) == 0

    def close(self) -> None:
        self.library.curl_global_cleanup()

    def post(self, url: str, body: bytes, ca: Path | None = None) -> tuple[int, bytes]:
        response = bytearray()
        callback_type = ctypes.CFUNCTYPE(
            ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p
        )

        def receive(pointer: int, size: int, count: int, _context: int | None) -> int:
            length = size * count
            if len(response) + length > 8192:
                return 0
            response.extend(ctypes.string_at(pointer, length))
            return length

        callback = callback_type(receive)
        handle = ctypes.c_void_p(self.library.curl_easy_init())
        assert handle.value is not None
        strings = [(url.encode(), _CURLOPT_URL), (b"", _CURLOPT_PROXY), (body, _CURLOPT_POSTFIELDS)]
        if ca is not None:
            strings.append((str(ca).encode("utf-8"), _CURLOPT_CAINFO))
        buffers = [ctypes.create_string_buffer(value) for value, _ in strings]
        try:
            for buffer, (_, option) in zip(buffers, strings, strict=True):
                assert self.pointer_option(handle, option, ctypes.cast(buffer, ctypes.c_void_p)) == 0
            assert self.pointer_option(handle, _CURLOPT_WRITEFUNCTION, ctypes.cast(callback, ctypes.c_void_p)) == 0
            assert self.long_option(handle, _CURLOPT_POSTFIELDSIZE, len(body)) == 0
            assert self.long_option(handle, _CURLOPT_TIMEOUT_MS, 5000) == 0
            return int(self.library.curl_easy_perform(handle)), bytes(response)
        finally:
            self.library.curl_easy_cleanup(handle)


@contextmanager
def _server(handler: type[BaseHTTPRequestHandler], context: ssl.SSLContext | None = None) -> Iterator[str]:
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        server.daemon_threads = True
        if context is not None:
            server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        try:
            yield f"{'https' if context is not None else 'http'}://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join(timeout=5)
            assert not thread.is_alive()


def _handler(crl: dict[str, bytes]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            assert 0 <= length <= 4096
            data = self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            assert self.path == "/issuer.crl"
            data = crl["data"]
            self.send_response(200)
            self.send_header("Content-Type", "application/pkix-crl")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        @typing_extensions.override
        def log_message(self, format: str, *args: object) -> None:
            return None

    return Handler


@pytest.fixture(scope="module")
def curl() -> Iterator[_Curl]:
    engine = shutil.which("osemgrep.exe")
    assert engine is not None, "The actual frozen Windows SDK must be provisioned"
    directory = Path(engine).resolve().parent
    selected = json.loads((ROOT / "ci/security-tool-minimum-versions.json").read_text())["native_semgrep"]["platforms"][
        "windows-x86_64"
    ]
    expected = selected["curl_fix"]["members"][0]
    filename = directory / expected["installed_path"]
    assert filename.stat().st_size == expected["size"]
    assert hashlib.sha256(filename.read_bytes()).hexdigest() == expected["sha256"]
    assert not (directory / "libssh2-1.dll").exists()
    api = _Curl(str(filename))
    kernel = ctypes.CDLL(str(Path(os.environ["SYSTEMROOT"]) / "System32/kernel32.dll"))
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong]
    kernel.GetModuleFileNameW.restype = ctypes.c_ulong
    actual = ctypes.create_unicode_buffer(1024)
    size = kernel.GetModuleFileNameW(ctypes.c_void_p(api.library._handle), actual, len(actual))
    assert 0 < size < len(actual)
    assert Path(actual.value).resolve() == filename
    try:
        yield api
    finally:
        api.close()


def _fixture_ca(
    directory: Path, label: str, distribution: x509.CRLDistributionPoints
) -> tuple[rsa.RSAPrivateKey, x509.Name, Path]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "PR786 ephemeral " + label)])
    now = datetime.now(UTC)
    ca = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False)
        .add_extension(distribution, False)
        .sign(key, hashes.SHA256())
    )
    path = directory / (label + ".pem")
    path.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    return key, subject, path


@contextmanager
def _tls_material(
    directory: Path,
) -> Iterator[tuple[Path, Path, dict[str, ssl.SSLContext], type[BaseHTTPRequestHandler]]]:
    crl: dict[str, bytes] = {}
    handler = _handler(crl)
    now = datetime.now(UTC)
    with _server(handler) as issuer:
        distribution = x509.CRLDistributionPoints(
            [
                x509.DistributionPoint(
                    full_name=[x509.UniformResourceIdentifier(issuer + "/issuer.crl")],
                    relative_name=None,
                    reasons=None,
                    crl_issuer=None,
                )
            ]
        )
        key, subject, ca_path = _fixture_ca(directory, "trusted CA", distribution)
        _, _, other_path = _fixture_ca(directory, "unrelated CA", distribution)
        contexts: dict[str, ssl.SSLContext] = {}
        revoked_serial = x509.random_serial_number()
        for name in ["valid", "hostname", "revoked", "expired"]:
            leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            san: list[x509.GeneralName] = (
                [x509.DNSName("wrong.invalid")]
                if name == "hostname"
                else [x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")), x509.DNSName("localhost")]
            )
            certificate = (
                x509.CertificateBuilder()
                .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Loopback fixture")]))
                .issuer_name(subject)
                .public_key(leaf_key.public_key())
                .serial_number(revoked_serial if name == "revoked" else x509.random_serial_number())
                .not_valid_before(now - timedelta(hours=2))
                .not_valid_after(now - timedelta(hours=1) if name == "expired" else now + timedelta(hours=1))
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), True)
                .add_extension(x509.SubjectAlternativeName(san), False)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()), False)
                .add_extension(distribution, False)
                .sign(key, hashes.SHA256())
            )
            cert_path, key_path = directory / (name + ".pem"), directory / (name + ".key")
            cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
            password = os.urandom(32)
            key_path.write_bytes(
                leaf_key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.BestAvailableEncryption(password),
                )
            )
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(cert_path, key_path, password=password)
            contexts[name] = context
        revoked = (
            x509.RevokedCertificateBuilder()
            .serial_number(revoked_serial)
            .revocation_date(now - timedelta(minutes=1))
            .build()
        )
        listing = (
            x509.CertificateRevocationListBuilder()
            .issuer_name(subject)
            .last_update(now - timedelta(minutes=1))
            .next_update(now + timedelta(hours=1))
            .add_revoked_certificate(revoked)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(key.public_key()), False)
            .sign(key, hashes.SHA256())
        )
        crl["data"] = listing.public_bytes(serialization.Encoding.DER)
        yield ca_path, other_path, contexts, handler


def test_windows_curl_version_and_protocols(curl: _Curl) -> None:
    version = curl.library.curl_version_info(0).contents
    assert version.version == b"8.23.0"
    assert version.ssl_version == b"Schannel"
    protocols: set[bytes] = set()
    index = 0
    while version.protocols[index]:
        protocols.add(version.protocols[index])
        index += 1
    assert protocols == {b"http", b"https"}


@pytest.mark.parametrize("value", [b"", b"space and % signs", b"\x00binary", "Unicode: café".encode()])
def test_windows_curl_allocator_matches_engine_runtime(curl: _Curl, value: bytes) -> None:
    runtime = ctypes.CDLL(str(Path(os.environ["SYSTEMROOT"]) / "System32/msvcrt.dll"))
    runtime.free.argtypes = [ctypes.c_void_p]
    runtime.free.restype = None
    for _ in range(16):
        escaped = curl.library.curl_escape(value, len(value))
        assert escaped
        try:
            encoded = ctypes.string_at(escaped)
            unescaped = curl.library.curl_unescape(encoded, len(encoded))
            assert unescaped
            try:
                assert ctypes.string_at(unescaped, len(value)) == value
            finally:
                runtime.free(unescaped)
        finally:
            runtime.free(escaped)


def test_windows_curl_http_post_callback(curl: _Curl) -> None:
    with _server(_handler({})) as url:
        assert curl.post(url, b"native curl POST") == (0, b"native curl POST")


@pytest.mark.parametrize(
    "case", ["valid", "unrelated-ca", "hostname", "revoked", "expired", "malformed-ca", "empty-ca"]
)
def test_windows_curl_explicit_ca_and_tls_rejections(curl: _Curl, tmp_path: Path, case: str) -> None:
    with _tls_material(tmp_path) as (ca, unrelated, contexts, handler):
        context = contexts[case if case in {"hostname", "revoked", "expired"} else "valid"]
        selected = unrelated if case == "unrelated-ca" else ca
        if case in {"malformed-ca", "empty-ca"}:
            selected = tmp_path / "invalid-ca.pem"
            selected.write_bytes(b"invalid certificate" if case == "malformed-ca" else b"")
        with _server(handler, context) as url:
            code, body = curl.post(url, b"verified TLS POST", selected)
    if case == "valid":
        assert (code, body) == (0, b"verified TLS POST")
    elif case in {"malformed-ca", "empty-ca"}:
        assert code in {_CURLE_PEER_FAILED_VERIFICATION, _CURLE_SSL_CACERT_BADFILE}
        assert body == b""
    else:
        assert code == _CURLE_PEER_FAILED_VERIFICATION
        assert body == b""


@pytest.fixture
def native_https_rules(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[tuple[str, Path, list[str]]]:
    requested: list[str] = []
    with _tls_material(tmp_path) as (ca, _unrelated, contexts, _base):

        class _RemoteRules(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                requested.append(self.path)
                payload = (
                    b"rules:\n  - id: loopback-marker\n    languages: [python]\n"
                    b"    pattern: print(...)\n    message: marker\n    severity: INFO\n"
                )
                self.send_response(200)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        with _server(_RemoteRules, contexts["valid"] if request.param == "https" else None) as url:
            yield url.replace("127.0.0.1", "localhost"), ca, requested


@pytest.mark.parametrize(
    ("native_https_rules", "expectation"),
    [
        ("https", ("valid", True, ["/valid.yml"], [(True, 1)], "")),
        ("https", ("malformed", False, [], [], "certificate|ssl|tls|trust")),
        ("https", ("empty", False, [], [], "certificate|ssl|tls|trust")),
        ("https", ("debug-https", True, ["/debug-https.yml"], [(True, 1)], "")),
        ("http", ("debug-http", True, ["/debug-http.yml"], [(True, 1)], "")),
    ],
    ids=["valid", "malformed", "empty", "debug-https", "debug-http"],
    indirect=["native_https_rules"],
)
def test_windows_native_https_config_uses_explicit_ca(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    native_https_rules: tuple[str, Path, list[str]],
    expectation: tuple[str, bool, list[str], list[tuple[bool, int]], str],
) -> None:
    case, success, expected_requests, expected_findings, diagnostic = expectation
    url, ca, requested = native_https_rules
    source = tmp_path / "example.py"
    source.write_text("print('marker')\n", encoding="utf-8")
    invalid = tmp_path / "invalid-ca.pem"
    invalid.write_text("not a certificate", encoding="utf-8")
    monkeypatch.setenv(
        "SSL_CERT_FILE",
        {"valid": str(ca), "malformed": str(invalid), "empty": "", "debug-https": str(ca), "debug-http": str(ca)}[case],
    )
    environment = {
        name: value
        for name, value in _build_semgrep_env(tmp_path).items()
        if name.upper() not in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}
    }
    try:
        result = subprocess.run(
            [
                "osemgrep",
                "scan",
                "--experimental",
                *{"valid": [], "malformed": [], "empty": [], "debug-https": ["--debug"], "debug-http": ["--debug"]}[
                    case
                ],
                "--metrics=off",
                "--disable-version-check",
                "--config",
                f"{url}/{case}.yml",
                "--json",
                str(source),
            ],
            env=environment,
            capture_output=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        log_file = Path(environment["SEMGREP_LOG_FILE"])
        pytest.fail(
            f"native config {url} {case} timed out after {error.timeout}s; "
            f"stdout={error.stdout!r}; stderr={error.stderr!r}; requests={requested!r}; "
            f"semgrep.log={log_file.read_bytes() if log_file.exists() else None!r}"
        )
    assert (result.returncode == 0) is success, result.stderr
    assert requested == expected_requests
    findings = json.loads(result.stdout or "{}").get("results", [])
    assert [
        (entry["check_id"].endswith("loopback-marker"), entry["start"]["line"]) for entry in findings
    ] == expected_findings
    assert re.search(diagnostic, result.stdout + result.stderr, re.IGNORECASE)
