"""The workbench's zones: the inspector's first section is titled after what is selected and
the manufacturer's section shows only for a device; the navigator's views are tabs; buttons that
stay pressed (an area of the rail, a flag, a filter) are drawn in the theme's chosen fill."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from imgui_bundle import imgui

from editor_gui.plugins.base.registry import PanelDefinition
from editor_gui.widgets import choice
from editor_gui.widgets.choice import ChoiceColors, chosen_fill
from editor_gui.widgets.tabs import forget_shown_tab_bars
from editor_gui.workbench import layout
from editor_gui.workbench.group_objects import toggle_button
from editor_gui.workbench.layout import Workbench


@pytest.fixture
def frame() -> Iterator[None]:
    # The tab bars remembered are those of another context.
    forget_shown_tab_bars()
    ctx = imgui.create_context()
    imgui.get_io().display_size = imgui.ImVec2(800, 600)
    imgui.get_io().backend_flags |= imgui.BackendFlags_.renderer_has_textures
    imgui.new_frame()
    imgui.begin("Workbench", None, imgui.WindowFlags_.no_saved_settings)
    yield
    imgui.end()
    imgui.end_frame()
    imgui.destroy_context(ctx)
    forget_shown_tab_bars()


def _workbench(
    rendered: list[str], section: tuple[str, bool] | None = None
) -> Workbench:
    panels = [
        PanelDefinition(name, name, "", lambda name=name: rendered.append(name))
        for name in (
            "device",
            "manufacturer",
            "comment",
            "buildings",
            "group_addresses",
        )
    ]
    labels = {
        "device": lambda: "Device",
        "manufacturer": lambda: "Manufacturer",
        "comment": lambda: "Comment",
        "buildings": lambda: "Buildings",
        "group_addresses": lambda: "Group Addresses",
    }
    return Workbench(panels, labels, (lambda: section) if section is not None else None)


def _headers(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The labels of the inspector's sections drawn (each one shown open)."""
    shown: list[str] = []

    def header(label: str, flags: int = 0) -> bool:
        shown.append(label.split("###")[0])
        return True

    monkeypatch.setattr(layout, "collapsing_header", header)
    return shown


@pytest.mark.usefixtures("frame")
def test_a_device_shows_the_device_and_the_manufacturer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _headers(monkeypatch)
    rendered: list[str] = []
    _workbench(rendered, ("Device", True))._render_inspector()  # pyright: ignore[reportPrivateUsage]
    assert shown == ["Device", "Manufacturer", "Comment"]
    assert rendered == ["device", "manufacturer", "comment"]


@pytest.mark.usefixtures("frame")
def test_another_element_titles_the_section_and_leaves_out_the_manufacturer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _headers(monkeypatch)
    rendered: list[str] = []
    _workbench(rendered, ("Main Group", False))._render_inspector()  # pyright: ignore[reportPrivateUsage]
    assert shown == ["Main Group", "Comment"]
    assert rendered == ["device", "comment"]


@pytest.mark.usefixtures("frame")
def test_without_a_selection_source_the_section_is_the_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown = _headers(monkeypatch)
    _workbench([])._render_inspector()  # pyright: ignore[reportPrivateUsage]
    assert shown == ["Device", "Manufacturer", "Comment"]


@pytest.mark.usefixtures("frame")
def test_the_navigator_shows_its_views_as_tabs(monkeypatch: pytest.MonkeyPatch) -> None:
    tabs: list[str] = []
    begin = imgui.begin_tab_item

    def tab_item(label: str, *args: object) -> tuple[bool, bool | None]:
        tabs.append(label.split("###")[0])
        return begin(label, *args)  # type: ignore[arg-type]

    monkeypatch.setattr(layout.imgui, "begin_tab_item", tab_item)
    rendered: list[str] = []
    workbench = _workbench(rendered)
    workbench.show("group_addresses")
    workbench._render_navigator()  # pyright: ignore[reportPrivateUsage]
    # The topology view has no label here: its name stands in.
    assert tabs == ["Buildings", "topology", "Group Addresses"]
    # The view asked for is the one shown.
    assert rendered == ["group_addresses"]


@pytest.fixture(autouse=True)
def _theme_choice_colors() -> Iterator[None]:
    """The theme's choice colors as they were before each test."""
    before = choice.choice_colors()
    yield
    choice.set_choice_colors(before)


def test_the_chosen_fill_is_the_themes_choice_color() -> None:
    fill = imgui.ImVec4(0.1, 0.2, 0.3, 1.0)
    choice.set_choice_colors(ChoiceColors(fill=fill, list_bg=fill))
    assert chosen_fill() == fill


@pytest.mark.usefixtures("frame")
def test_without_choice_colors_the_chosen_fill_is_the_pressed_button() -> None:
    choice.set_choice_colors(None)
    pressed = imgui.get_style_color_vec4(imgui.Col_.button_active)
    assert chosen_fill() == pressed


@pytest.mark.usefixtures("frame")
def test_a_toggle_that_is_on_is_drawn_in_the_chosen_fill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fills: list[tuple[float, float, float, float]] = []
    button = imgui.button

    def recorded(label: str, size: imgui.ImVec2) -> bool:
        color = imgui.get_style_color_vec4(imgui.Col_.button)
        fills.append((color.x, color.y, color.z, color.w))
        return button(label, size)

    monkeypatch.setattr(imgui, "button", recorded)
    fill = imgui.ImVec4(0.1, 0.2, 0.3, 1.0)
    choice.set_choice_colors(ChoiceColors(fill=fill, list_bg=fill))
    toggle_button("C##on", True)
    toggle_button("R##off", False, dim_off=True)
    normal = imgui.get_style_color_vec4(imgui.Col_.button)
    assert fills == [
        pytest.approx((0.1, 0.2, 0.3, 1.0)),
        pytest.approx((normal.x, normal.y, normal.z, normal.w)),
    ]
