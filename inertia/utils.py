from dataclasses import dataclass
from json import JSONEncoder, load as json_load
from functools import lru_cache
from fastapi.encoders import jsonable_encoder
from typing import (
    Literal,
    Callable,
    Optional,
    TypedDict,
    Dict,
    Union,
    cast,
    Any,
    Awaitable,
)


class InertiaJsonEncoder(JSONEncoder):
    """
    Custom JSONEncoder to handle Inertia.js response data
    You can extend this class to add custom encoders for your models
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Constructor
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

    def encode(self, value: Any) -> Any:
        """
        Encode the value
        Uses the jsonable_encoder from FastAPI to encode the value
        :param value: Value to encode
        :return: Encoded value
        """
        return jsonable_encoder(value)


class IgnoreOnFirstLoadProp:
    """
    Marker class to indicate that a property should be ignored on the first load

    Note: Internal use only. Not part of the public API. It is internal for now
    and will be released as part of the public API in a future version. The
    behavior of this utility may change before its public release.
    """

    def __init__(self, prop: Union[Callable[[], Union[Any, Awaitable[Any]]], Any]):
        """
        Constructor
        :param prop: Property to evaluate, can be a callable or a value
        """
        self.prop = prop

    async def __call__(self) -> Any:
        """
        Call the property
        :return: Value of the property
        """
        if not callable(self.prop):
            return self.prop

        result = self.prop()
        if hasattr(result, "__await__"):
            return await result
        return result


class LazyProp(IgnoreOnFirstLoadProp):
    """
    Lazy property that can be used to defer the evaluation of a property
    """

    pass


class DeferredProp(IgnoreOnFirstLoadProp):
    """
    A property that will be deferred and loaded later via a subsequent
    request, this allows for lazy loading of expensive props.

    Note: Internal use only. Not part of the public API. It is internal for now
    and will be released as part of the public API in a future version. The
    behavior of this utility may change before its public release.
    """

    def __init__(
        self,
        prop: Union[Callable[[], Union[Any, Awaitable[Any]]], Any],
        group: str = "default",
    ):
        """
        Constructor
        :param prop: Property to evaluate, can be a callable (sync or async) or a value
        :param group: Group name for batch loading
        """
        super().__init__(prop)
        self.group = group


def lazy(prop: Union[Callable[[], Union[Any, Awaitable[Any]]], Any]) -> LazyProp:
    """
    Create a lazy property
    :param prop: The property to evaluate, can be a callable or a value
    :return: Lazy property
    """
    return LazyProp(prop)


def defer(
    prop: Union[Callable[[], Union[Any, Awaitable[Any]]], Any],
    group: str = "default",
) -> DeferredProp:
    """
    Create a deferred property
    :param prop: The property to evaluate, can be a callable (sync or async) or a value
    :param group: Group name for batch loading
    :return: Deferred property

    Note: Internal use only. Not part of the public API. It is internal for now
    and will be released as part of the public API in a future version. The
    behavior of this utility may change before its public release.
    """
    return DeferredProp(prop, group)


class ViteManifestChunk(TypedDict):
    file: str
    src: Optional[str]
    isEntry: Optional[bool]
    isDynamicEntry: Optional[bool]
    dynamicImports: Optional[list[str]]
    css: Optional[list[str]]
    assets: Optional[list[str]]
    imports: Optional[list[str]]


ViteManifest = Dict[str, ViteManifestChunk]


@lru_cache
def _read_manifest_file(path: str) -> ViteManifest:
    with open(path, "r") as manifest_file:
        return cast(ViteManifest, json_load(manifest_file))


@dataclass()
class InertiaContext:
    """
    The jinja template context to pass to render the html for the first request.
    """

    environment: Literal["development", "production"]
    dev_url: str
    css: list[str]
    js: str
    is_ssr: bool
    data: Optional[str] = None
    ssr_head: Optional[str] = None
    ssr_body: Optional[str] = None
