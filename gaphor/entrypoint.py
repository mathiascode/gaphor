import functools
import importlib.metadata
import inspect
import logging
from typing import Dict, Type, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def initialize(scope, services=None, **known_services: T) -> Dict[str, T]:
    return init_entry_points(load_entry_points(scope, services), **known_services)


@functools.lru_cache(maxsize=4)
def list_entry_points(group):
    try:
        return importlib.metadata.entry_points(group=group)  # type: ignore[call-arg]
    except TypeError:
        # Fallback for Python < 3.10
        return importlib.metadata.entry_points()[group]


def load_entry_points(scope, services=None) -> Dict[str, Type[T]]:
    """Load services from resources."""
    uninitialized_services = {}
    for ep in list_entry_points(scope):
        cls = ep.load()
        if not services or ep.name in services:
            logger.debug(f'found service entry point "{ep.name}"')
            uninitialized_services[ep.name] = cls
    return uninitialized_services


def init_entry_points(
    uninitialized_services: Dict[str, Type[T]], **known_services: T
) -> Dict[str, T]:
    """Instantiate service definitions, taking into account dependencies
    defined in the constructor.

    Given a dictionary `{name: service-class}`, return a map `{name:
    service-instance}`.
    """
    ready: Dict[str, T] = dict(known_services)

    def pop(name):
        try:
            return uninitialized_services.pop(name)
        except KeyError:
            return None

    def init(name, cls):
        kwargs = {}
        for param_name, param in inspect.signature(cls).parameters.items():
            if param_name not in ready:
                depcls = pop(param_name)
                if depcls:
                    kwargs[param_name] = init(param_name, depcls)
                elif param.default is inspect.Parameter.empty:
                    logger.warn(
                        "Entrypoint %s parameter %s does not reference a resolved dependency",
                        name,
                        param_name,
                    )
            else:
                kwargs[param_name] = ready[param_name]
        srv = cls(**kwargs)
        ready[name] = srv
        return srv

    while uninitialized_services:
        name = next(iter(uninitialized_services.keys()))
        cls = pop(name)
        init(name, cls)

    return ready
