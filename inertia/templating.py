from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.parser import Parser
from jinja2.runtime import Context
from markupsafe import Markup

from .utils import InertiaContext


class InertiaExtension(Extension):
    """
    Jinja2 extension for Inertia.js that adds the inertia_head and inertia_body tags
    to a jinja environment to render the head and body of the Inertia.js page.
    """

    tags = set(["inertia_head", "inertia_body"])

    def parse(self, parser: Parser) -> nodes.Node:
        tag_name = next(parser.stream).value
        lineno = parser.stream.current.lineno
        ctx_ref = nodes.ContextReference()

        node = self.call_method(f"_render_{tag_name}", [ctx_ref], lineno=lineno)
        return nodes.Output([node]).set_lineno(lineno)

    def _render_inertia_head(self, context: Context) -> Markup:
        fragments: list[str] = []
        inertia: InertiaContext = context["inertia"]

        if inertia.environment == "development":
            fragments.append(
                f'<script type="module" src="{inertia.dev_url}/@vite/client"></script>'
            )

        if inertia.is_ssr:
            if inertia.ssr_head is None:
                raise ValueError("SSR is enabled but no SSR head was provided")
            fragments.append(inertia.ssr_head)

        if inertia.css:
            for css_file in inertia.css:
                fragments.append(f'<link rel="stylesheet" href="{css_file}">')

        return Markup("\n".join(fragments))

    def _render_inertia_body(self, context: Context) -> Markup:
        fragments: list[str] = []
        inertia: InertiaContext = context["inertia"]
        if inertia.is_ssr:
            if inertia.ssr_body is None:
                raise ValueError("SSR is enabled but no SSR body was provided")
            fragments.append(inertia.ssr_body)
        else:
            if inertia.data is None:
                raise ValueError("No data was provided for the Inertia page")
            fragments.append(f"<div id=\"app\" data-page='{inertia.data}'></div>")

        fragments.append(f'<script type="module" src="{inertia.js}"></script>')
        return Markup("\n".join(fragments))
