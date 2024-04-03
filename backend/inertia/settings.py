from typing import Type
from pydantic_settings import BaseSettings
from jinja2 import Environment, PackageLoader
from .utils import InertiaJsonEncoder


class InertiaSettings(BaseSettings):
    INERTIA_VERSION: str = "1.0"
    INERTIA_JSON_ENCODER: Type[InertiaJsonEncoder] = InertiaJsonEncoder
    INERTIA_URL: str = "http://localhost:5173"
    INERTIA_ENV: str = "dev"
    INERTIA_TEMPLATE_DIR: str = "inertia/templates"

    @property
    def INERTIA_TEMPLATE_ENV(self) -> Environment:
        env = Environment(loader=PackageLoader("backend", self.INERTIA_TEMPLATE_DIR))
        env.globals["script_url"] = (
            f"{self.INERTIA_URL}/src/main.js"
            if self.INERTIA_ENV == "dev"
            else "/src/assets/index.js"
        )
        return env


settings = InertiaSettings()
