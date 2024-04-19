from typing import Callable

from fastapi import Request
from backend.inertia.config import InertiaConfig
from backend.inertia.renderer import InertiaRenderer


def inertia_renderer_factory(
    config_: InertiaConfig,
) -> Callable[[Request], InertiaRenderer]:
    def inertia_dependency(request: Request) -> InertiaRenderer:
        return InertiaRenderer(request, config_)

    return inertia_dependency
