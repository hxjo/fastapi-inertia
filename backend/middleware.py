from starlette.middleware.base import BaseHTTPMiddleware
from .settings import settings
from fastapi import Request
from fastapi.responses import Response, JSONResponse

class InertiaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not self.is_inertia_request(request):
            return response

        if self.is_non_post_redirect(request, response):
            response.status_code = 303

        if self.is_stale(request):
            return self.force_refresh(request)

        return response

    def is_non_post_redirect(self, request: Request, response: Response):
        return self.is_redirect_request(response) and request.method in ['PUT', 'PATCH', 'DELETE']

    def is_inertia_request(self, request: Request):
        return 'X-Inertia' in request.headers

    def is_redirect_request(self, response: Response):
        return response.status_code in [301, 302]

    def is_stale(self, request: Request):
        return request.headers.get('X-Inertia-Version', settings.INERTIA_VERSION) != settings.INERTIA_VERSION

    def force_refresh(self, request: Request):
        return JSONResponse(content={}, status_code=409, headers={
            'X-Inertia-Location': str(request.url),
        })
