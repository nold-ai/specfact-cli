from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


_CURL_OPTIONS = (
    "BUILD_SHARED_LIBS=ON",
    "BUILD_STATIC_LIBS=OFF",
    "BUILD_CURL_EXE=OFF",
    "BUILD_TESTING=OFF",
    "BUILD_EXAMPLES=OFF",
    "CURL_USE_SCHANNEL=ON",
    "CURL_USE_OPENSSL=OFF",
    "CURL_USE_MBEDTLS=OFF",
    "CURL_USE_WOLFSSL=OFF",
    "CURL_USE_GNUTLS=OFF",
    "CURL_USE_RUSTLS=OFF",
    "CURL_USE_LIBSSH2=OFF",
    "CURL_USE_LIBSSH=OFF",
    "CURL_USE_LIBPSL=OFF",
    "CURL_USE_PKGCONFIG=OFF",
    "CURL_USE_CMAKECONFIG=OFF",
    "CURL_ZLIB=OFF",
    "CURL_BROTLI=OFF",
    "CURL_ZSTD=OFF",
    "USE_LIBIDN2=OFF",
    "USE_WIN32_IDN=ON",
    "USE_NGHTTP2=OFF",
    "USE_NGHTTP3=OFF",
    "USE_NGTCP2=OFF",
    "CURL_USE_GSSAPI=OFF",
    "CURL_DISABLE_PROXY=OFF",
    "CURL_DISABLE_DICT=ON",
    "CURL_DISABLE_FILE=ON",
    "CURL_DISABLE_FTP=ON",
    "CURL_DISABLE_GOPHER=ON",
    "CURL_DISABLE_IMAP=ON",
    "CURL_DISABLE_LDAP=ON",
    "CURL_DISABLE_LDAPS=ON",
    "CURL_DISABLE_MQTT=ON",
    "CURL_DISABLE_POP3=ON",
    "CURL_DISABLE_RTSP=ON",
    "CURL_DISABLE_SMTP=ON",
    "CURL_DISABLE_TELNET=ON",
    "CURL_DISABLE_TFTP=ON",
    "CURL_TARGET_WINDOWS_VERSION=0x0601",
    "CURL_DISABLE_IPFS=ON",
    "CURL_DISABLE_WEBSOCKETS=ON",
)
_CURL_LIBRARIES = ("normaliz", "bcrypt", "advapi32", "crypt32", "secur32", "ws2_32", "iphlpapi")
_LINK_LIBRARIES = (
    "mingw32.lib",
    "mingwex.lib",
    "msvcrt-os.lib",
    "uuid.lib",
    "ssp.lib",
    "compiler_rt.lib",
    *(name + ".lib" for name in _CURL_LIBRARIES),
    "kernel32.lib",
    "msvcrt.lib",
    "ntdll.lib",
    "shell32.lib",
    "user32.lib",
)


def _run(arguments: list[str], directory: Path, environment: dict[str, str]) -> None:
    subprocess.run(
        arguments,
        cwd=directory,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=sys.stderr,
        stderr=sys.stderr,
        timeout=300,
        check=True,
    )


def _response(path: Path, arguments: list[str]) -> str:
    path.write_text(subprocess.list2cmdline(arguments), encoding="utf-8")
    return "@" + path.as_posix()


def _cache_file(cache: Path, name: str) -> str:
    paths = list(cache.rglob(name))
    if not paths or any(path.is_symlink() or not path.is_file() for path in paths):
        raise ValueError("Windows curl build cache has ambiguous or missing link inputs")
    digests: set[str] = set()
    for path in paths:
        with path.open("rb") as source:
            digests.add(hashlib.file_digest(source, "sha256").hexdigest())
    if len(digests) != 1:
        raise ValueError("Windows curl build cache has conflicting link inputs")
    return min(paths).as_posix()


def build_windows_curl(*, source: Path, zig: Path, cmake: Path, ninja: Path, build: Path) -> Path:
    paths = (source, zig, cmake, ninja, build)
    if any(not path.is_absolute() or any(c in path.as_posix() for c in '\r\n";$') for path in paths):
        raise ValueError("Unsupported Windows curl build path")
    build.mkdir(mode=0o700)
    temporary = build / "temp"
    temporary.mkdir()
    environment = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    system = Path(environment["SYSTEMROOT"]) / "System32" if "SYSTEMROOT" in environment else None
    environment.update(
        {
            "PATH": str(system) if system is not None else "/usr/bin:/bin",
            "LC_ALL": "C",
            "TZ": "UTC",
            "SOURCE_DATE_EPOCH": "0",
            "TEMP": str(temporary),
            "TMP": str(temporary),
            "TMPDIR": str(temporary),
            "ZIG_GLOBAL_CACHE_DIR": str(build / "compile-cache"),
            "ZIG_LOCAL_CACHE_DIR": str(build / "local-cache"),
        }
    )
    rules = build / "rules.cmake"
    rules.write_text(
        'set(CMAKE_C_LINK_EXECUTABLE "<CMAKE_C_COMPILER> <FLAGS> <LINK_FLAGS> <OBJECTS> -o <TARGET> <LINK_LIBRARIES>")\n'
        'set(CMAKE_C_VERBOSE_FLAG "")\nset(CMAKE_C_VERBOSE_LINK_FLAG "")\n',
        encoding="utf-8",
    )
    toolchain = build / "toolchain.cmake"
    toolchain.write_text(
        "set(CMAKE_SYSTEM_NAME Windows)\nset(CMAKE_SYSTEM_PROCESSOR AMD64)\nset(CMAKE_SYSTEM_VERSION 6.1)\n"
        f'set(CMAKE_C_COMPILER "{zig.as_posix()}")\n'
        'set(CMAKE_C_COMPILER_ARG1 "cc -target x86_64-windows.win7-gnu")\n'
        f'set(CMAKE_RC_COMPILER "{zig.as_posix()}")\n'
        f'set(CMAKE_USER_MAKE_RULES_OVERRIDE "{rules.as_posix()}")\n'
        "set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)\nset(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)\n"
        "set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)\nset(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)\n",
        encoding="utf-8",
    )
    flags = f'-O2 -g0 "-ffile-prefix-map={build.as_posix()}=/build" "-ffile-prefix-map={source.as_posix()}=/source"'
    configure = [
        str(cmake),
        "-S",
        source.as_posix(),
        "-B",
        build.as_posix(),
        "-G",
        "Ninja",
        "-DCMAKE_MAKE_PROGRAM=" + ninja.as_posix(),
        "-DCMAKE_TOOLCHAIN_FILE=" + toolchain.as_posix(),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_C_FLAGS=" + flags,
        *("-D" + option for option in _CURL_OPTIONS),
    ]
    _run(configure, build, environment)
    _run([str(cmake), "--build", build.as_posix(), "--target", "libcurl_object", "--parallel", "2"], build, environment)
    objects = sorted((build / "lib/CMakeFiles/libcurl_object.dir").rglob("*.obj"))
    if len(objects) != 195 or any(path.is_symlink() or not path.is_file() for path in objects):
        raise ValueError("Windows curl source object set differs from the frozen recipe")
    cache = build / "link-cache"
    environment["ZIG_GLOBAL_CACHE_DIR"] = str(cache)
    environment["ZIG_LOCAL_CACHE_DIR"] = str(build / "link-local-cache")
    driver = [
        "-target",
        "x86_64-windows.win7-gnu",
        "-shared",
        "-s",
        (source / "lib/libcurl.def").as_posix(),
        "-o",
        "unverified.dll",
        *(path.as_posix() for path in objects),
        *("-l" + name for name in _CURL_LIBRARIES),
    ]
    _run([str(zig), "cc", _response(build / "driver.rsp", driver)], build, environment)
    final = [
        "-timestamp:0",
        "-ERRORLIMIT:0",
        "-NOLOGO",
        "-MACHINE:X64",
        "-INCLUDE:_tls_index",
        "-DLL",
        "-OUT:libcurl-4.dll",
        "-IMPLIB:libcurl-4.dll.a",
        *(path.as_posix() for path in objects),
        "-DEF:" + (source / "lib/libcurl.def").as_posix(),
        "-lldmingw",
        "-ALTERNATENAME:__image_base__=__ImageBase",
        _cache_file(cache, "dllcrt2.obj"),
        "-ALTERNATENAME:_DllMainCRTStartup=DllMainCRTStartup",
        *(_cache_file(cache, name) for name in _LINK_LIBRARIES),
    ]
    _run([str(zig), "lld-link", "--rsp-quoting=windows", _response(build / "final.rsp", final)], build, environment)
    return build / "libcurl-4.dll"
