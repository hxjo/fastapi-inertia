from json import JSONEncoder
from fastapi import Request

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import Callable, Any, cast, TypedDict


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(exclude={"password"})


class InertiaJsonEncoder(JSONEncoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def encode(self, value: Any) -> Any:
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


class FlashMessage(TypedDict):
    message: str
    category: str


def flash_message(request: Request, message: str, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []

    message_: FlashMessage = {"message": message, "category": category}
    request.session["_messages"].append(message_)


def get_flashed_messages(request: Request) -> list[FlashMessage]:
    return (
        cast(list[FlashMessage], request.session.pop("_messages"))
        if "_messages" in request.session
        else []
    )
