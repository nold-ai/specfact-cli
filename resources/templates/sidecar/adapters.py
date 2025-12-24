# pyright: reportMissingImports=false
"""Sidecar binding adapters."""

from __future__ import annotations

import asyncio
import contextvars
import importlib
import inspect
import os
import sys
from collections.abc import Callable
from typing import Any, Protocol, cast, runtime_checkable


@runtime_checkable
class SupportsGet(Protocol):
    def get(self, key: Any, default: Any = None) -> Any: ...


@runtime_checkable
class SupportsGetItem(Protocol):
    def __getitem__(self, key: Any) -> Any: ...


def call_method_with_factory(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Create an instance via factory and call a method on it."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    method_name = binding.get("method")
    if not method_name:
        raise ValueError("Binding missing method")
    factory_cfg = binding.get("factory") or {}
    factory_target_name = factory_cfg.get("target") or target_name
    factory_target = load_binding(factory_target_name)
    factory_args = [resolve_value(item, request) for item in factory_cfg.get("args", [])]
    factory_kwargs = {key: resolve_value(val, request) for key, val in factory_cfg.get("kwargs", {}).items()}
    instance = factory_target(*factory_args, **factory_kwargs)
    method = getattr(instance, method_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    return call_target(method, call_style, request, args)


def call_constructor_then_method(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Construct an object and call a method on the instance."""
    target_name = binding.get("target") or binding.get("class")
    if not target_name:
        raise ValueError("Binding missing target")
    method_name = binding.get("method")
    if not method_name:
        raise ValueError("Binding missing method")
    init_cfg = binding.get("init") or {}
    ctor = load_binding(target_name)
    ctor_args = [resolve_value(item, request) for item in init_cfg.get("args", [])]
    ctor_kwargs = {key: resolve_value(val, request) for key, val in init_cfg.get("kwargs", {}).items()}
    instance = ctor(*ctor_args, **ctor_kwargs)
    method = getattr(instance, method_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    return call_target(method, call_style, request, args)


def call_classmethod(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Call a classmethod/staticmethod on a target class."""
    target_name = binding.get("target") or binding.get("class")
    if not target_name:
        raise ValueError("Binding missing target")
    method_name = binding.get("method")
    if not method_name:
        raise ValueError("Binding missing method")
    klass = load_binding(target_name)
    method = getattr(klass, method_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    return call_target(method, call_style, request, args)


def call_with_context_manager(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Use a context manager to create a resource, then call an optional method."""
    target_name = binding.get("target")
    if not target_name:
        raise ValueError("Binding missing target")
    method_name = binding.get("method")
    init_cfg = binding.get("init") or {}
    ctor = load_binding(target_name)
    ctor_args = [resolve_value(item, request) for item in init_cfg.get("args", [])]
    ctor_kwargs = {key: resolve_value(val, request) for key, val in init_cfg.get("kwargs", {}).items()}
    with ctor(*ctor_args, **ctor_kwargs) as resource:
        if not method_name:
            return resource
        method = getattr(resource, method_name)
        call_style = binding.get("call_style", "dict")
        args = binding.get("args", [])
        return call_target(method, call_style, request, args)


def call_async(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Call an async function and run the coroutine to completion."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    target = load_binding(target_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    result = call_target(target, call_style, request, args)
    if asyncio.iscoroutine(result):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(result)
        if loop.is_running():
            raise RuntimeError("Async adapter cannot run inside a running event loop")
        return loop.run_until_complete(result)
    return result


def call_with_setup_teardown(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Run setup/teardown around a target call."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    setup_name = binding.get("setup")
    teardown_name = binding.get("teardown")
    setup_args = [resolve_value(item, request) for item in binding.get("setup_args", [])]
    setup_kwargs = {key: resolve_value(val, request) for key, val in binding.get("setup_kwargs", {}).items()}
    teardown_args = [resolve_value(item, request) for item in binding.get("teardown_args", [])]
    teardown_kwargs = {key: resolve_value(val, request) for key, val in binding.get("teardown_kwargs", {}).items()}
    setup_result = None
    if setup_name:
        setup_func = load_binding(setup_name)
        setup_result = setup_func(*setup_args, **setup_kwargs)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    request_payload = request
    setup_key = binding.get("setup_result_key")
    if setup_key and isinstance(request, dict):
        request_payload = dict(request)
        request_payload[setup_key] = setup_result
    target = load_binding(target_name)
    result = None
    try:
        result = call_target(target, call_style, request_payload, args)
    finally:
        if teardown_name:
            teardown_func = load_binding(teardown_name)
            teardown_pass = binding.get("teardown_pass", "none")
            if teardown_pass == "setup":
                teardown_func(setup_result, *teardown_args, **teardown_kwargs)
            elif teardown_pass == "result":
                teardown_func(result, *teardown_args, **teardown_kwargs)
            elif teardown_pass == "both":
                teardown_func(setup_result, result, *teardown_args, **teardown_kwargs)
            else:
                teardown_func(*teardown_args, **teardown_kwargs)
    return result


def call_with_request_transform(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Transform request fields before invoking the target."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    if not isinstance(request, dict):
        raise ValueError("Request transform adapter expects dict request")
    transform = binding.get("transform") or {}
    rename = transform.get("rename", {})
    drop = set(transform.get("drop", []))
    set_values = transform.get("set", {})
    coerce = transform.get("coerce", {})
    payload = dict(request)
    for old_key, new_key in rename.items():
        if old_key in payload:
            payload[new_key] = payload.pop(old_key)
    for key in drop:
        payload.pop(key, None)
    for key, value in set_values.items():
        payload[key] = resolve_value(value, payload)
    for key, cast_name in coerce.items():
        if key not in payload:
            continue
        value = payload[key]
        if cast_name == "int":
            payload[key] = int(value)
        elif cast_name == "float":
            payload[key] = float(value)
        elif cast_name == "str":
            payload[key] = str(value)
        elif cast_name == "bool":
            payload[key] = bool(value)
    target = load_binding(target_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    return call_target(target, call_style, payload, args)


def _consume_iterable(iterable: Any, limit: int | None) -> list[Any]:
    items: list[Any] = []
    for item in iterable:
        items.append(item)
        if limit is not None and len(items) >= limit:
            break
    return items


async def _consume_async_iterable(iterable: Any, limit: int | None) -> list[Any]:
    items: list[Any] = []
    async for item in iterable:
        items.append(item)
        if limit is not None and len(items) >= limit:
            break
    return items


def call_generator(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Consume a generator/iterator and return collected items."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    target = load_binding(target_name)
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    result = call_target(target, call_style, request, args)
    consume = binding.get("consume", "all")
    limit = None if consume in ("all", None) else int(consume)
    if inspect.isasyncgen(result) or hasattr(result, "__aiter__"):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            items = asyncio.run(_consume_async_iterable(result, limit))
        else:
            if loop.is_running():
                raise RuntimeError("Async generator adapter cannot run inside a running event loop")
            items = loop.run_until_complete(_consume_async_iterable(result, limit))
    else:
        items = _consume_iterable(result, limit)
    collect = binding.get("collect", "list")
    if collect == "last":
        return items[-1] if items else None
    if collect == "tuple":
        return tuple(items)
    if collect == "count":
        return len(items)
    return items


def call_from_registry(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Any],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Resolve a callable from a registry and invoke it."""
    registry_target = binding.get("registry")
    if not registry_target:
        raise ValueError("Binding missing registry")
    registry_obj: Any = load_binding(registry_target)
    key = binding.get("key")
    request_key = binding.get("request_key")
    if key is None and request_key and isinstance(request, dict):
        key = request.get(request_key)
    if key is None:
        raise ValueError("Registry key not provided")
    entry = None
    lookup = binding.get("lookup")
    if lookup == "call":
        if not callable(registry_obj):
            raise ValueError("Registry lookup requested call but registry is not callable")
        entry = registry_obj(key)
    elif isinstance(registry_obj, SupportsGet):
        entry = registry_obj.get(key)
    elif isinstance(registry_obj, SupportsGetItem):
        entry = registry_obj[key]
    else:
        raise ValueError("Registry object does not support lookup")
    if entry is None:
        raise ValueError("Registry entry not found")
    if isinstance(entry, str) and ":" in entry:
        entry = load_binding(entry)
    method_name = binding.get("method")
    if method_name:
        entry = getattr(entry, method_name)
    if not callable(entry):
        raise ValueError("Registry entry is not callable")
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    return call_target(cast(Callable[..., Any], entry), call_style, request, args)


def call_with_overrides(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Temporarily override module attributes during the call."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    overrides = binding.get("overrides", [])
    if not isinstance(overrides, list):
        raise ValueError("Overrides must be a list")
    sentinel = object()
    patched: list[tuple[Any, str, Any]] = []
    for override in overrides:
        if not isinstance(override, dict):
            continue
        target = override.get("target")
        if not target:
            raise ValueError("Override missing target")
        module_name, attr_path = target.split(":", 1)
        obj = importlib.import_module(module_name)
        parts = attr_path.split(".")
        for part in parts[:-1]:
            obj = getattr(obj, part)
        attr_name = parts[-1]
        old_value = getattr(obj, attr_name, sentinel)
        new_value = resolve_value(override.get("value"), request)
        setattr(obj, attr_name, new_value)
        patched.append((obj, attr_name, old_value))
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    target = load_binding(target_name)
    try:
        return call_target(target, call_style, request, args)
    finally:
        for obj, attr_name, old_value in reversed(patched):
            if old_value is sentinel:
                delattr(obj, attr_name)
            else:
                setattr(obj, attr_name, old_value)


def call_with_contextvars(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Set context variables for the duration of the call."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    contexts = binding.get("context_vars", []) or binding.get("context", [])
    if not isinstance(contexts, list):
        raise ValueError("context_vars must be a list")
    tokens: list[tuple[contextvars.ContextVar[Any], contextvars.Token[Any]]] = []
    for entry in contexts:
        if not isinstance(entry, dict):
            continue
        var_target = entry.get("var")
        if not var_target:
            raise ValueError("Context var missing var")
        var = load_binding(var_target)
        if not isinstance(var, contextvars.ContextVar):
            raise ValueError("Context var target is not a ContextVar")
        value = resolve_value(entry.get("value"), request)
        context_var = cast(contextvars.ContextVar[Any], var)
        token = context_var.set(value)
        tokens.append((context_var, token))
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    target = load_binding(target_name)
    try:
        return call_target(target, call_style, request, args)
    finally:
        for var, token in reversed(tokens):
            var.reset(token)


def call_with_session(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Create a session/transaction around the target call."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    session_target = binding.get("session") or binding.get("session_factory")
    if not session_target:
        raise ValueError("Binding missing session factory")
    session_ctor = load_binding(session_target)
    session_args = [resolve_value(item, request) for item in binding.get("session_args", [])]
    session_kwargs = {key: resolve_value(val, request) for key, val in binding.get("session_kwargs", {}).items()}
    session = session_ctor(*session_args, **session_kwargs)
    begin_name = binding.get("begin")
    commit_name = binding.get("commit", "commit")
    rollback_name = binding.get("rollback", "rollback")
    close_name = binding.get("close", "close")
    if begin_name:
        getattr(session, begin_name)()
    request_payload = request
    session_key = binding.get("session_key")
    if session_key and isinstance(request, dict):
        request_payload = dict(request)
        request_payload[session_key] = session
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    target = load_binding(target_name)
    result = None
    try:
        result = call_target(target, call_style, request_payload, args)
        if commit_name:
            getattr(session, commit_name)()
        return result
    except Exception:
        if rollback_name:
            getattr(session, rollback_name)()
        raise
    finally:
        if close_name:
            getattr(session, close_name)()


def call_with_callbacks(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """Inject callbacks into the request payload before calling."""
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")
    if not isinstance(request, dict):
        raise ValueError("Callback adapter expects dict request")
    callbacks = binding.get("callbacks", [])
    if not isinstance(callbacks, list):
        raise ValueError("Callbacks must be a list")
    payload = dict(request)
    for entry in callbacks:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            raise ValueError("Callback entry missing name")
        target = entry.get("target")
        if target:
            callback = load_binding(target)
        else:
            return_value = entry.get("return")

            def _noop(*args: Any, _return_value: Any = return_value, **kwargs: Any) -> Any:
                return _return_value

            callback = _noop
        payload[name] = callback
    call_style = binding.get("call_style", "dict")
    args = binding.get("args", [])
    target = load_binding(target_name)
    return call_target(target, call_style, payload, args)


def call_django_view(
    binding: dict[str, Any],
    request: Any,
    load_binding: Callable[[str], Callable[..., Any]],
    call_target: Callable[[Callable[..., Any], str, Any, list[str]], Any],
    resolve_value: Callable[[Any, Any], Any],
) -> Any:
    """
    Convert dict request to Django HttpRequest and call Django view.

    This adapter:
    1. Creates a Django HttpRequest object from the dict
    2. Sets request.method, request.POST, request.GET, request.user
    3. Extracts path parameters from the request dict
    4. Calls the Django view function
    """
    target_name = binding.get("target") or binding.get("function")
    if not target_name:
        raise ValueError("Binding missing target")

    # Import Django components (lazy import to avoid errors if Django not available)
    # Type checker warnings are expected - Django is optional dependency
    # Ensure repo path is in sys.path for Django imports
    repo_path_str = os.environ.get("REPO_PATH")
    if repo_path_str and repo_path_str not in sys.path:
        sys.path.insert(0, repo_path_str)

    # Initialize Django if not already initialized
    django_settings = os.environ.get("DJANGO_SETTINGS_MODULE")
    if django_settings:
        try:
            import django

            if not django.apps.apps.ready:
                django.setup()
        except (ImportError, Exception):
            pass  # Django not available or already configured

    try:
        from django.contrib.auth.models import AnonymousUser  # type: ignore[reportMissingImports]
        from django.test import RequestFactory  # type: ignore[reportMissingImports]
    except ImportError:
        raise ImportError("Django adapter requires Django to be installed") from None

    if not isinstance(request, dict):
        raise ValueError("Django adapter expects dict request")

    # Extract HTTP method (default to POST for form submissions)
    method = request.get("_method", "POST").upper()

    # Extract path parameters (e.g., pk, friend_pk)
    path_params = {k: v for k, v in request.items() if k.startswith("_path_")}
    path_params = {k.replace("_path_", ""): v for k, v in path_params.items()}

    # Extract form data (POST body)
    form_data = {k: v for k, v in request.items() if not k.startswith("_")}

    # Create Django HttpRequest using RequestFactory
    factory = RequestFactory()

    # Build path with parameters
    path = binding.get("path", "/")
    for param_name, param_value in path_params.items():
        path = path.replace(f"{{{param_name}}}", str(param_value))

    # Create request based on method
    if method == "GET":
        django_request = factory.get(path, form_data)
    elif method == "POST":
        django_request = factory.post(path, form_data)
    elif method == "PUT":
        django_request = factory.put(path, form_data)
    elif method == "PATCH":
        django_request = factory.patch(path, form_data)
    elif method == "DELETE":
        django_request = factory.delete(path, form_data)
    else:
        django_request = factory.request(REQUEST_METHOD=method, path=path)

    # Set user if provided
    user_target = binding.get("user") or binding.get("user_factory")
    if user_target:
        user = load_binding(user_target)
        if callable(user):
            user = user()
        django_request.user = user
    else:
        django_request.user = AnonymousUser()

    # Load and call the Django view
    view_func = load_binding(target_name)

    # Django views typically take (request, *args, **kwargs)
    # Extract args from path_params
    view_args = []
    view_kwargs = {}

    # If path_params exist, they become kwargs
    if path_params:
        view_kwargs = path_params
    else:
        # Try to extract from binding args
        args_list = binding.get("args", [])
        for arg_name in args_list:
            if arg_name in request:
                view_args.append(request[arg_name])

    # Call the view
    try:
        result = view_func(django_request, *view_args, **view_kwargs)
        # Convert HttpResponse to dict for CrossHair
        if hasattr(result, "status_code"):
            return {
                "status_code": result.status_code,
                "content": getattr(result, "content", b"").decode("utf-8", errors="ignore"),
            }
        return result
    except Exception as e:
        # Return error info for CrossHair to analyze
        return {
            "error": type(e).__name__,
            "message": str(e),
        }
