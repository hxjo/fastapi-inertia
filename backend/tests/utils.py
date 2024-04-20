import json
from string import Template
from typing import Any


def get_stripped_html(
        *,
        component_name: str,
        props: dict[str, Any],
        url: str,
        script_asset_url: str = "http://localhost:5173/src/main.js",
        css_asset_url: str = "",
        additional_head_content: str = ""
) -> str:
    css_link = f"<link rel=\"stylesheet\" href=\"{css_asset_url}\">" if css_asset_url else ""
    return Template("""
                   <!DOCTYPE html>
                   <html>
                       <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            $head
                            $css_link
                        </head>
                        <body>
                            <div id='app' data-page='{"component": "$component_name", "props": $props, "url": "$url", "version": "1.0"}'></div>
                            <script type="module" src="$script_asset_url"></script>
                       </body>
                   </html>
            """).substitute(
        component_name=component_name,
        props=json.dumps(props),
        url=url,
        head=additional_head_content,
        css_link=css_link,
        script_asset_url=script_asset_url
    ).strip()
