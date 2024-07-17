from functools import lru_cache
import json
from typing import Literal, Type, Optional, TypedDict, Dict, cast
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
    manifest_json_path: str = "dist/.vite/manifest.json"
    root_directory: str = "src"
    entrypoint_filename: str = "main.js"
    use_flash_messages: bool = False
    use_flash_errors: bool = False
    flash_message_key: str = "messages"
    flash_error_key: str = "errors"
    assets_prefix: str = ""


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
