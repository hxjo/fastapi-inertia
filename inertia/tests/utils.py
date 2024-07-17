import json
from typing import Any, List, Optional, Union, cast
from httpx import Response
from bs4 import BeautifulSoup, Tag


def assert_response_content(
    response: Response,
    *,
    expected_component: Optional[str] = None,
    expected_props: Optional[dict[str, Any]] = None,
    expected_url: Optional[str] = None,
    expected_script_asset_url: Optional[str] = None,
    expected_css_asset_urls: Optional[List[str]] = None,
    expected_additional_head_content: Optional[List[str]] = None,
    expected_body_content: Optional[str] = None,
) -> None:
    soup = BeautifulSoup(response.text, "html.parser")
    if not soup:
        raise AssertionError("Response content is not HTML")
    if expected_component or expected_props or expected_url:
        data_page_el = cast(
            Union[Tag, None], soup.find("div", attrs={"data-page": True})
        )
        if not data_page_el:
            raise AssertionError("No data-page element found")
        data_page_raw = data_page_el.attrs.get("data-page")
        if not data_page_raw:
            raise AssertionError("data-page attribute is empty")
        data_page = json.loads(cast(str, data_page_raw))
        if expected_component is not None:
            assert data_page["component"] == expected_component
        if expected_props is not None:
            assert data_page["props"] == expected_props
        if expected_url is not None:
            assert data_page["url"] == expected_url

    if expected_script_asset_url is not None:
        script_tag = soup.find(
            "script", attrs={"src": expected_script_asset_url, "type": "module"}
        )
        assert script_tag is not None

    if expected_css_asset_urls is not None:
        for asset_url in expected_css_asset_urls:
            css_tag = soup.find("link", attrs={"href": asset_url, "rel": "stylesheet"})
            assert css_tag is not None

    if expected_additional_head_content is not None:
        for head_element in expected_additional_head_content:
            head_soup = BeautifulSoup(head_element, "html.parser")
            if not head_soup:
                raise AssertionError("Additional head content is not HTML")
            head_tag = cast(Union[Tag, None], head_soup.find())
            if not head_tag:
                raise AssertionError("No element found in additional head content")
            if not soup.head:
                raise AssertionError("No head element found")
            assert soup.head.find(name=head_tag.name, attrs=head_tag.attrs) is not None

    if expected_body_content is not None:
        body_soup = BeautifulSoup(expected_body_content, "html.parser")
        for body_element in body_soup.find_all():
            if not soup.body:
                raise AssertionError("No body element found")
            assert (
                soup.body.find(
                    name=body_element.name,
                    attrs=body_element.attrs,
                    string=body_element.string,
                )
                is not None
            )
