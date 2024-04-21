from json import JSONEncoder

from fastapi.encoders import jsonable_encoder
from typing import Callable, Any


class InertiaJsonEncoder(JSONEncoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def encode(self, value: Any) -> Any:
        return jsonable_encoder(value)


class LazyProp:
    def __init__(self, prop: Callable[[], Any] | Any):
        self.prop = prop

    def __call__(self) -> Any:
        return self.prop() if callable(self.prop) else self.prop


def lazy(prop: Callable[[], Any] | Any) -> LazyProp:
    return LazyProp(prop)
