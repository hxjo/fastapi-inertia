from jinja2 import Environment, FileSystemLoader
import pytest
from inertia.templating import InertiaExtension
from inertia.utils import InertiaContext
from .utils import template_dir

env = Environment(loader=FileSystemLoader(template_dir))


def test_extension_render_head_ssr_raises_if_no_ssr_head() -> None:
    extension = InertiaExtension(env)
    with pytest.raises(ValueError):
        extension._render_inertia_head(
            {
                "inertia": InertiaContext(
                    environment="development",
                    dev_url="http://localhost:5173",
                    is_ssr=True,
                    css=["/app.css"],
                    js="/app.js",
                )
            }  #  type: ignore
        )


def test_extension_render_body_ssr_raises_if_no_ssr_body() -> None:
    extension = InertiaExtension(env)
    with pytest.raises(ValueError):
        extension._render_inertia_body(
            {
                "inertia": InertiaContext(
                    environment="development",
                    dev_url="http://localhost:5173",
                    is_ssr=True,
                    css=["/app.css"],
                    js="/app.js",
                )
            }  #  type: ignore
        )


def test_extension_render_body_no_ssr_raises_if_no_data() -> None:
    extension = InertiaExtension(env)
    with pytest.raises(ValueError):
        extension._render_inertia_body(
            {
                "inertia": InertiaContext(
                    environment="development",
                    dev_url="http://localhost:5173",
                    is_ssr=False,
                    css=["/app.css"],
                    js="/app.js",
                )
            }  #  type: ignore
        )


def test_extension_render_react_refresh_returns_nothing_if_not_dev() -> None:
    extension = InertiaExtension(env)
    assert (
        extension._render_inertia_react_refresh(
            {
                "inertia": InertiaContext(
                    environment="production",
                    dev_url="http://localhost:5173",
                    is_ssr=False,
                    css=["/app.css"],
                    js="/app.js",
                )
            }  #  type: ignore
        )
        == ""
    )
