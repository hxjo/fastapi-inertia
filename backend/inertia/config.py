from typing import Literal, Type
from .utils import InertiaJsonEncoder
from dataclasses import dataclass


@dataclass
class InertiaConfig:
    ENV: Literal["development", "production"] = "development"
    VERSION: str = "1.0"
    JSON_ENCODER: Type[InertiaJsonEncoder] = InertiaJsonEncoder
    MANIFEST_JSON_PATH: str = ""
    DEV_URL: str = "http://localhost:5173"
    SSR_URL: str = "http://localhost:13714"
    SSR_ENABLED: bool = False
