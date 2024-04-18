import json
import os
from typing import Type
from pydantic_settings import BaseSettings
from jinja2 import Environment, PackageLoader
from .utils import InertiaJsonEncoder


class InertiaSettings(BaseSettings):
    INERTIA_VERSION: str = "1.0"
    PACKAGE_NAME: str = "backend"
    INERTIA_JSON_ENCODER: Type[InertiaJsonEncoder] = InertiaJsonEncoder
    INERTIA_URL: str = "http://localhost:5173"
    INERTIA_ENV: str = "dev"
    INERTIA_TEMPLATE_DIR: str = "inertia/templates"
    INERTIA_MANIFEST_JSON: str = os.path.join(os.path.dirname(__file__), "..", "..", "vue", "dist", "client", "manifest.json")
    INERTIA_SSR_URL: str = 'http://localhost:13714'
    INERTIA_SSR_ENABLED: bool = True

    @property
    def INERTIA_TEMPLATE_ENV(self) -> Environment:
        env = Environment(loader=PackageLoader(self.PACKAGE_NAME, self.INERTIA_TEMPLATE_DIR))
        with open(settings.INERTIA_MANIFEST_JSON, "r") as manifest_file:
            manifest = json.load(manifest_file)

        js_file = manifest["src/main.js"]["file"]
        env.globals["script_url"] = (
            f"{self.INERTIA_URL}/src/main.js"
            if self.INERTIA_ENV == "dev"
            else f"/src/{js_file}"
        )
        env.globals['css_url'] = (
            f"{self.INERTIA_URL}/src/main.css"
            if self.INERTIA_ENV == "dev"
            else f"/src/{manifest['src/main.js']['css'][0]}"
        )
        return env


settings = InertiaSettings()
