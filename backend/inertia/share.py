from typing import Any

from fastapi import Request

__all__ = ["share"]


class InertiaShare:
    props: dict[str, Any]

    def __init__(self) -> None:
        self.props = {}

    def set(self, **kwargs: Any) -> None:
        self.props = {
            **self.props,
            **kwargs,
        }

    def all(self) -> dict[str, Any]:
        return self.props


def share(request: Request, **kwargs: Any) -> None:
    if not hasattr(request.state, "inertia"):
        request.state.inertia = InertiaShare()

    request.state.inertia.set(**kwargs)
