from functools import lru_cache
import json
from typing import Literal, Type, Optional, TypedDict, Dict, Union, cast
import warnings
from json import JSONEncoder
from .utils import InertiaJsonEncoder
from dataclasses import dataclass


@dataclass
class InertiaConfig:
    """
    Configuration class for Inertia
    """

    environment: Literal["development", "production"] = "development"
    version: str = "1.0"
    json_encoder: Type[JSONEncoder] = InertiaJsonEncoder
    dev_url: str = "http://localhost:5173"
    ssr_url: str = "http://localhost:13714"
    ssr_enabled: bool = False
    manifest_json_path: str = ""
    root_directory: str = "src"
    entrypoint_filename: str = "main.js"
    use_flash_messages: bool = False
    use_flash_errors: bool = False
    flash_message_key: str = "messages"
    flash_error_key: str = "errors"
    assets_prefix: str = ""
    use_typescript: Union[bool, None] = None

    def __post_init__(self) -> None:
        if self.use_typescript is not None:
            warnings.warn(
                "use_typescript is deprecated: Please use entrypoint_filename instead. It will be removed in 1.0.0",
                DeprecationWarning,
                stacklevel=2,
            )
            self.entrypoint_filename = "main.ts" if self.use_typescript else "main.js"


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
        return cast(ViteManifest, json.load(manifest_file))
