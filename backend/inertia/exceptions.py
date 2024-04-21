from fastapi import Request, Response, status


class InertiaVersionConflictException(Exception):
    """
    Exception to raise when the Inertia version is stale
    """

    def __init__(self, url: str) -> None:
        """
        Constructor
        :param url: URL to redirect to
        """
        self.url = url
        super().__init__()


def inertia_exception_handler(
    _: Request, exc: InertiaVersionConflictException
) -> Response:
    """
    Exception handler for InertiaVersionConflictException
    :param _: Request
    :param exc: InertiaVersionConflictException
    :return: Response
    """
    return Response(
        status_code=status.HTTP_409_CONFLICT,
        headers={"X-Inertia-Location": str(exc.url)},
    )
