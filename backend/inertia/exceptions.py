from fastapi import Request, Response, status


class InertiaVersionConflict(Exception):
    def __init__(self, url: str) -> None:
        self.url = url


def inertia_exception_handler(_: Request, exc: InertiaVersionConflict) -> Response:
    return Response(
        status_code=status.HTTP_409_CONFLICT,
        headers={"X-Inertia-Location": str(exc.url)},
    )
