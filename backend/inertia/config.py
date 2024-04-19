from typing import Literal, Type
from .utils import InertiaJsonEncoder
from dataclasses import dataclass


@dataclass
class InertiaConfig:
    environment: Literal["development", "production"] = "development"
    version: str = "1.0"
    json_encoder: Type[InertiaJsonEncoder] = InertiaJsonEncoder
    manifest_json_path: str = ""
    dev_url: str = "http://localhost:5173"
    ssr_url: str = "http://localhost:13714"
    ssr_enabled: bool = False
