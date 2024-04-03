from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Callable, Any


def model_to_dict(model: BaseModel):
    return model.dict(exclude={'password'})


class InertiaJsonEncoder:
    def __init__(self, *args, **kwargs):
        pass

    def encode(self, value: Any) -> str:
        if isinstance(value, BaseModel):
            return model_to_dict(value)

        return jsonable_encoder(value)


class LazyProp:
    def __init__(self, prop: Callable[[], Any] | Any):
        self.prop = prop

    def __call__(self) -> Any:
        return self.prop() if callable(self.prop) else self.prop


def lazy(prop: Callable[[], Any] | Any) -> LazyProp:
    return LazyProp(prop)
