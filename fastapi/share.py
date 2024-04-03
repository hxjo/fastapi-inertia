from fastapi import Request

__all__ = ['share']

class InertiaShare:
    def __init__(self):
        self.props = {}

    def set(self, **kwargs):
        self.props = {
            **self.props,
            **kwargs,
        }

    def all(self):
        return self.props

def share(request: Request, **kwargs):
    if not hasattr(request.state, 'inertia'):
        request.state.inertia = InertiaShare()

    request.state.inertia.set(**kwargs)
