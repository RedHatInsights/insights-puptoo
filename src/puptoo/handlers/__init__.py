from .base import BaseHandler

_REGISTRY: dict[str, type[BaseHandler]] = {}


def handler(service: str):
    """Class decorator that registers a handler for a service type."""

    def decorator(cls: type[BaseHandler]) -> type[BaseHandler]:
        _REGISTRY[service] = cls
        return cls

    return decorator


def register(service: str, handler_cls: type[BaseHandler]) -> None:
    _REGISTRY[service] = handler_cls


def get_handler(service: str) -> BaseHandler | None:
    handler_cls = _REGISTRY.get(service)
    if handler_cls is None:
        return None
    return handler_cls()


from . import advisor, compliance  # noqa: E402, F401
