"""The workbench follows the width of the window: "wide" has all zones docked, "mid" (a tablet in
landscape) folds the navigator's list away and shows the inspector over the workspace, "narrow" (a
tablet in portrait) shows the navigator's list over it too."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from imgui_bundle import imgui

from editor_gui.plugins.base.registry import PanelDefinition
from editor_gui.widgets.tabs import forget_shown_tab_bars
from editor_gui.workbench import layout
from editor_gui.workbench.layout import Workbench, layout_mode, overlay_rect


@pytest.fixture
def frame() -> Iterator[None]:
    forget_shown_tab_bars()
    ctx = imgui.create_context()
    imgui.get_io().display_size = imgui.ImVec2(800, 1000)
    imgui.get_io().backend_flags |= imgui.BackendFlags_.renderer_has_textures
    imgui.new_frame()
    imgui.begin("Workbench", None, imgui.WindowFlags_.no_saved_settings)
    yield
    imgui.end()
    imgui.end_frame()
    imgui.destroy_context(ctx)
    forget_shown_tab_bars()


def _workbench(rendered: list[str], selection: list[object] | None = None) -> Workbench:
    names = ("device", "manufacturer", "comment", "buildings", "group_addresses")
    panels = [
        PanelDefinition(name, name, "", lambda name=name: rendered.append(name))
        for name in names
    ]
    labels = {name: (lambda name=name: name) for name in names}
    bench = Workbench(
        panels,
        labels,
        None,
        (lambda: selection[0]) if selection is not None else None,
    )
    # No docking runner in a test: the layout is not built again.
    bench._relayout = lambda: None  # pyright: ignore[reportPrivateUsage]
    return bench


@pytest.mark.parametrize(
    ("width", "current", "wanted"),
    [
        (1440, None, "wide"),
        (1280, None, "wide"),
        (1279, None, "mid"),
        (1000, None, "mid"),
        (999, None, "narrow"),
        (744, None, "narrow"),
        # A window shown wide stays wide a little below the limit, and the other way round.
        (1250, "wide", "wide"),
        (1250, "mid", "mid"),
        (1310, "mid", "mid"),
        (1330, "mid", "wide"),
        (970, "mid", "mid"),
        (970, "narrow", "narrow"),
        (1050, "narrow", "mid"),
        (1030, "narrow", "narrow"),
        # Below 600 it is a phone.
        (599, None, "phone"),
        (600, None, "narrow"),
        (590, "narrow", "narrow"),
        (550, "narrow", "phone"),
        (620, "phone", "phone"),
        (650, "phone", "narrow"),
        (390, "wide", "phone"),
    ],
)
def test_the_layout_follows_the_width_with_a_margin(
    width: float, current: str | None, wanted: str
) -> None:
    assert layout_mode(width, current) == wanted


def test_the_overlays_lie_over_the_workspace() -> None:
    area = (100.0, 50.0, 700.0, 900.0)
    # The inspector comes from the right edge in "mid", from below as a sheet in "narrow".
    x, y, width, height = overlay_rect("mid", "inspector", area, 1.0)
    assert (x + width, y, height) == (800.0, 50.0, 900.0)
    assert width == 360.0
    x, y, width, height = overlay_rect("narrow", "inspector", area, 1.0)
    assert (x, width, y + height) == (100.0, 700.0, 950.0)
    assert height == pytest.approx(495.0)
    # The navigator's list from the left edge, never wider than the workspace.
    assert overlay_rect("narrow", "navigator", area, 1.0) == (100.0, 50.0, 340.0, 900.0)
    narrow = (0.0, 0.0, 300.0, 500.0)
    assert overlay_rect("narrow", "navigator", narrow, 1.0)[2] == pytest.approx(255.0)
    # The phone's sheet is higher.
    x, y, width, height = overlay_rect(
        "phone", "inspector", (0.0, 0.0, 390.0, 800.0), 1.0
    )
    assert (x, width, y + height) == (0.0, 390.0, 800.0)
    assert height == pytest.approx(624.0)


@pytest.mark.usefixtures("frame")
def test_the_zones_of_each_layout() -> None:
    bench = _workbench([])
    bench._width = 1440.0  # pyright: ignore[reportPrivateUsage]
    assert bench.list_docked()
    assert len(bench.docking_splits()) == 3

    bench._set_mode("mid")  # pyright: ignore[reportPrivateUsage]
    # The inspector is over the workspace now, no zone of its own; the list is docked.
    assert bench.nav_open
    assert bench.list_docked()
    assert len(bench.docking_splits()) == 2

    bench.toggle_nav()
    assert not bench.list_docked()
    narrow_rail = bench.docking_splits()[0].ratio
    bench.toggle_nav()
    assert bench.docking_splits()[0].ratio > narrow_rail

    bench._set_mode("narrow")  # pyright: ignore[reportPrivateUsage]
    # Only the rail is docked; the list comes over the workspace.
    assert not bench.nav_open
    assert not bench.list_docked()
    assert len(bench.docking_splits()) == 2


def test_the_inspector_is_back_when_the_window_gets_wide_again() -> None:
    bench = _workbench([])
    assert bench.show_inspector
    bench._set_mode("mid")  # pyright: ignore[reportPrivateUsage]
    assert not bench.show_inspector
    bench._set_mode("wide")  # pyright: ignore[reportPrivateUsage]
    assert bench.show_inspector
    bench.show_inspector = False
    bench._set_mode("narrow")  # pyright: ignore[reportPrivateUsage]
    bench._set_mode("wide")  # pyright: ignore[reportPrivateUsage]
    assert not bench.show_inspector


def test_a_new_width_has_to_settle_before_the_layout_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = [100.0]
    monkeypatch.setattr(layout.time, "monotonic", lambda: now[0])
    bench = _workbench([])
    # The first width is taken at once.
    bench.update_size(1440.0)
    assert bench.mode == "wide"
    bench.update_size(800.0)
    assert bench.mode == "wide"
    now[0] += 0.2
    bench.update_size(800.0)
    assert bench.mode == "wide"
    now[0] += 0.3
    bench.update_size(800.0)
    assert bench.mode == "narrow"
    # A width that went back in time starts again.
    bench.update_size(1100.0)
    now[0] += 0.2
    bench.update_size(800.0)
    now[0] += 0.5
    bench.update_size(800.0)
    assert bench.mode == "narrow"


def test_the_first_width_is_taken_at_once() -> None:
    bench = _workbench([])
    bench.update_size(744.0)
    assert bench.mode == "narrow"


@pytest.mark.usefixtures("frame")
def test_one_overlay_at_a_time() -> None:
    bench = _workbench([])
    bench._set_mode("narrow")  # pyright: ignore[reportPrivateUsage]
    bench.toggle_inspector()
    assert bench.show_inspector
    bench.toggle_nav()
    assert bench.nav_open
    assert not bench.show_inspector
    bench.toggle_inspector()
    assert bench.show_inspector
    assert not bench.nav_open


@pytest.mark.usefixtures("frame")
def test_asking_for_a_navigator_view_opens_the_list() -> None:
    bench = _workbench([])
    bench._set_mode("narrow")  # pyright: ignore[reportPrivateUsage]
    bench.show("group_addresses")
    assert bench.nav_open
    assert bench.view == "group_addresses"
    wide = _workbench([])
    wide.show("group_addresses")
    assert wide.nav_open  # always there; no overlay to open


@pytest.mark.usefixtures("frame")
def test_the_inspector_is_drawn_over_the_workspace() -> None:
    rendered: list[str] = []
    bench = _workbench(rendered)
    bench._set_mode("mid")  # pyright: ignore[reportPrivateUsage]
    bench._area = (100.0, 50.0, 700.0, 900.0)  # pyright: ignore[reportPrivateUsage]
    bench.render_overlays()
    assert rendered == []
    bench.show_inspector = True
    bench.render_overlays()
    assert "device" in rendered


@pytest.mark.usefixtures("frame")
def test_nothing_is_drawn_over_the_workspace_when_wide() -> None:
    rendered: list[str] = []
    bench = _workbench(rendered)
    bench._area = (100.0, 50.0, 700.0, 900.0)  # pyright: ignore[reportPrivateUsage]
    bench.render_overlays()
    assert rendered == []


@pytest.mark.usefixtures("frame")
def test_the_navigators_list_closes_when_something_is_chosen() -> None:
    rendered: list[str] = []
    selection: list[object] = ["a"]
    bench = _workbench(rendered, selection)
    bench._set_mode("narrow")  # pyright: ignore[reportPrivateUsage]
    bench._area = (100.0, 50.0, 700.0, 900.0)  # pyright: ignore[reportPrivateUsage]
    bench.toggle_nav()
    bench.render_overlays()
    assert bench.nav_open
    assert "buildings" in rendered
    selection[0] = "b"
    rendered.clear()
    bench.render_overlays()
    assert not bench.nav_open
    assert rendered == []


def _phone(
    rendered: list[str],
    selection: list[object] | None = None,
    device: bool = True,
) -> Workbench:
    names = (
        "editor",
        "buildings",
        "monitor",
        "health",
        "catalog",
        "tools",
        "operations",
        "logger",
        "device",
    )
    panels = [
        PanelDefinition(name, name, "", lambda name=name: rendered.append(name))
        for name in names
    ]
    labels = {name: (lambda name=name: name.title()) for name in names}
    bench = Workbench(
        panels,
        labels,
        lambda: ("Device", device),
        (lambda: selection[0]) if selection is not None else None,
    )
    bench._relayout = lambda: None  # pyright: ignore[reportPrivateUsage]
    bench._set_mode("phone")  # pyright: ignore[reportPrivateUsage]
    return bench


def test_the_phone_has_only_the_workspace() -> None:
    bench = _phone([])
    assert bench.docking_splits() == []
    visible = {
        name: bench._zone_visible(name)  # pyright: ignore[reportPrivateUsage]
        for name in (
            layout.NAVIGATOR,
            layout.WORKSPACE,
            layout.INSPECTOR,
            layout.BOTTOM,
        )
    }
    assert visible == {
        layout.NAVIGATOR: False,
        layout.WORKSPACE: True,
        layout.INSPECTOR: False,
        layout.BOTTOM: False,
    }
    assert not bench.show_inspector
    wide = _workbench([])
    assert wide._zone_visible(layout.NAVIGATOR)  # pyright: ignore[reportPrivateUsage]
    assert wide._zone_visible(layout.BOTTOM)  # pyright: ignore[reportPrivateUsage]


@pytest.mark.usefixtures("frame")
def test_asking_for_a_panel_shows_its_tab_on_the_phone() -> None:
    bench = _phone([])
    bench.show("operations")
    assert (bench.phone_tab, bench.phone_more) == ("more", "operations")
    bench.show("monitor")
    assert bench.phone_tab == "bus"
    bench.show("health")
    assert bench.phone_tab == "check"
    bench.show("catalog")
    assert (bench.phone_tab, bench.phone_more) == ("more", "catalog")
    bench.show("editor")
    assert (bench.phone_tab, bench.phone_screen) == ("project", "device")
    bench.phone_screen = "device"
    bench.show("buildings")
    assert (bench.phone_tab, bench.phone_screen) == ("project", "list")


def test_more_lists_what_has_no_tab() -> None:
    bench = _phone([])
    items = bench._more_items()  # pyright: ignore[reportPrivateUsage]
    assert [key for key, _label in items] == [
        "catalog",
        "tools",
        "operations",
        "logger",
    ]
    assert bench._more_label("logger") == "Logger"  # pyright: ignore[reportPrivateUsage]
    assert bench._more_label("other") == "other"  # pyright: ignore[reportPrivateUsage]


@pytest.mark.usefixtures("frame")
def test_the_list_is_shown_until_a_device_is_selected() -> None:
    rendered: list[str] = []
    selection: list[object] = ["a"]
    bench = _phone(rendered, selection)
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert bench.phone_screen == "list"
    assert "buildings" in rendered
    assert "editor" not in rendered
    rendered.clear()
    selection[0] = "b"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert (bench.phone_tab, bench.phone_screen) == ("project", "device")
    assert "editor" in rendered


@pytest.mark.usefixtures("frame")
def test_selecting_something_that_is_not_a_device_keeps_the_list() -> None:
    rendered: list[str] = []
    selection: list[object] = ["a"]
    bench = _phone(rendered, selection, device=False)
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    selection[0] = "b"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert bench.phone_screen == "list"
    assert "editor" not in rendered


@pytest.mark.usefixtures("frame")
def test_a_device_selected_from_another_tab_is_shown() -> None:
    rendered: list[str] = []
    selection: list[object] = ["a"]
    bench = _phone(rendered, selection)
    bench.phone_tab = "check"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    selection[0] = "b"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert (bench.phone_tab, bench.phone_screen) == ("project", "device")


@pytest.mark.usefixtures("frame")
def test_each_tab_of_the_phone_shows_its_panel() -> None:
    rendered: list[str] = []
    bench = _phone(rendered)
    for tab, panel in (("bus", "monitor"), ("check", "health")):
        rendered.clear()
        bench.phone_tab = tab
        bench._render_phone()  # pyright: ignore[reportPrivateUsage]
        assert rendered == [panel]
    # "More" lists first, and shows the panel chosen.
    rendered.clear()
    bench.phone_tab = "more"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert rendered == []
    bench.phone_more = "logger"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert rendered == ["logger"]
    rendered.clear()
    bench.phone_more = "catalog"
    bench._render_phone()  # pyright: ignore[reportPrivateUsage]
    assert rendered == ["catalog"]


@pytest.mark.usefixtures("frame")
def test_the_inspector_is_a_sheet_on_the_phone() -> None:
    rendered: list[str] = []
    bench = _phone(rendered)
    bench._area = (0.0, 0.0, 390.0, 800.0)  # pyright: ignore[reportPrivateUsage]
    bench.toggle_inspector()
    bench.render_overlays()
    assert "device" in rendered
