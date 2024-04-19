from fastapi import Request, Response, status


class InertiaVersionConflictException(Exception):
    def __init__(self, url: str) -> None:
        self.url = url
        super().__init__()


def inertia_exception_handler(
    _: Request, exc: InertiaVersionConflictException
) -> Response:
    return Response(
        status_code=status.HTTP_409_CONFLICT,
        headers={"X-Inertia-Location": str(exc.url)},
    )
