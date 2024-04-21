from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.responses import RedirectResponse


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


async def inertia_version_conflict_exception_handler(
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


async def inertia_request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> Response:
    """
    Exception handler for InertiaValidationException
    :param request: Request
    :param exc: InertiaValidationException
    :return: Response
    """
    is_inertia = request.headers.get("X-Inertia", False)
    if is_inertia:
        fastapi_errors = exc.errors()
        errors = {}
        error_bag = request.headers.get("X-Inertia-Error-Bag", None)
        for error in fastapi_errors:
            error_loc = error["loc"][1] if len(error["loc"]) > 1 else error["loc"][0]

            if error_bag is None:
                errors[error_loc] = error["msg"]
            else:
                if error_bag not in errors:
                    errors[error_bag] = {}

                errors[error_bag][error_loc] = error["msg"]

        request.session["_errors"] = errors

        status_code = (
            status.HTTP_307_TEMPORARY_REDIRECT
            if request.method == "GET"
            else status.HTTP_303_SEE_OTHER
        )
        return RedirectResponse(
            url=request.headers.get("Referer", "/"), status_code=status_code
        )
    else:
        return await request_validation_exception_handler(request, exc)
