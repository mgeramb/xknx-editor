"""The workbench's zones: the navigator with the activity rail on the left, the workspace in the
middle, the inspector on the right and the bottom panel. Each zone is one docked window without a
tab bar that draws the usual panels (their ``render``) where they belong, so every panel works as
before; only where it is shown changes.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from imgui_bundle import hello_imgui, imgui

from editor_gui.plugins.base.registry import PanelDefinition
from editor_gui.widgets.choice import chosen_fill
from editor_gui.widgets.dpi import px
from editor_gui.widgets.tabs import begin_tab_bar
from editor_gui.widgets.tree import collapsing_header
from editor_gui.workbench import state
from editor_gui.workbench.strings import S

# Font Awesome icons of the activity rail (those of the icon font the app loads).
_ICON_PROJECT = ""  # folder-open
_ICON_CATALOG = ""  # book
_ICON_BUS = ""  # clock-rotate-left (history of telegrams)
_ICON_CHECK = ""  # check-circle
_ICON_TOOLS = ""  # wrench

_RAIL_WIDTH = 72.0
_RAIL_BUTTON_HEIGHT = 54.0

# The layouts by the width of the window (the steps of the browser UI's ``form_factor``): "wide"
# has all zones docked; "mid" (a tablet in landscape) folds the navigator's list away and shows the
# inspector over the workspace; "narrow" (a tablet in portrait) also shows the navigator's list over
# the workspace, and the inspector as a sheet from below.
WIDE_MIN = 1280.0
MID_MIN = 1000.0
# A width right at a limit must not flip the layout back and forth.
_MARGIN = 40.0
# How long a new width has to stay before the layout changes (resizing, turning the device).
_SETTLE = 0.4


def layout_mode(width: float, current: str | None = None) -> str:
    """The layout for a window of this width: ``"wide"``, ``"mid"`` or ``"narrow"``. With the
    layout shown now, a limit is crossed only by a little more than it."""
    wide, mid = WIDE_MIN, MID_MIN
    if current == "wide":
        wide -= _MARGIN
    elif current is not None:
        wide += _MARGIN
    if current in ("wide", "mid"):
        mid -= _MARGIN
    elif current is not None:
        mid += _MARGIN
    if width >= wide:
        return "wide"
    if width >= mid:
        return "mid"
    return "narrow"


def overlay_rect(
    mode: str, kind: str, area: tuple[float, float, float, float], unit: float
) -> tuple[float, float, float, float]:
    """The place (x, y, width, height) of an overlay over the workspace ``area``: the navigator's
    list from the left edge, the inspector from the right edge in "mid" and as a sheet from below
    in "narrow". ``unit`` is the size of a pixel (the scale of the display)."""
    x, y, width, height = area
    if kind == "navigator":
        return x, y, min(width * 0.85, 340.0 * unit), height
    if mode == "narrow":
        sheet = height * 0.55
        return x, y + height - sheet, width, sheet
    over = min(width * 0.6, 360.0 * unit)
    return x + width - over, y, over, height


# The windows of the zones (their ids after ``###``).
NAVIGATOR = "wb_navigator"
WORKSPACE = "wb_workspace"
INSPECTOR = "wb_inspector"
BOTTOM = "wb_bottom"

# The panels the navigator switches between.
_NAVIGATOR_VIEWS = ("buildings", "topology", "group_addresses")
# The panels of the inspector, each a section.
_INSPECTOR_PANELS = ("device", "manufacturer", "comment")
# The panels of the bottom panel, each a tab.
_BOTTOM_PANELS = ("operations", "logger", "history", "project_log", "project_info")


@dataclass(frozen=True)
class _Area:
    key: str
    icon: str
    label: Callable[[], str]
    panels: tuple[str, ...]


class Workbench:
    """The zones and what they show: the area chosen in the rail, the view of the navigator, the
    tab of the workspace and of the bottom panel, and whether the inspector and the bottom panel
    are shown."""

    def __init__(
        self,
        panels: list[PanelDefinition],
        labels: dict[str, Callable[[], str]],
        device_section: Callable[[], tuple[str, bool]] | None = None,
        selection_key: Callable[[], object] | None = None,
    ) -> None:
        self._panels = {panel.name: panel for panel in panels}
        self._labels = labels
        # The title of the inspector's first section for what is selected (a device, a space, an
        # area, a line, a group range or address) and whether the manufacturer's section applies.
        self._device_section = device_section
        self._areas = (
            _Area(
                "project", _ICON_PROJECT, lambda: S.AREA_PROJECT, ("editor", "cockpit")
            ),
            _Area("catalog", _ICON_CATALOG, self._label("catalog"), ("catalog",)),
            _Area(
                "bus",
                _ICON_BUS,
                lambda: S.AREA_BUS,
                ("monitor", "timeline", "bus_diagram"),
            ),
            _Area("check", _ICON_CHECK, lambda: S.AREA_CHECK, ("health",)),
            _Area(
                "tools",
                _ICON_TOOLS,
                self._label("tools"),
                ("tools", "mass_linker", "recover"),
            ),
        )
        self.area = "project"
        self.view = "buildings"
        self._select_view: str | None = None
        self._tab: dict[str, str] = {}
        self._select_tab: str | None = None
        self.bottom_tab = "operations"
        self._select_bottom: str | None = None
        self.show_inspector = True
        self.show_bottom = True
        # The layout by the width of the window, the width it was made for, and whether the
        # navigator's list is shown (docked in "mid", over the workspace in "narrow").
        self.mode = "wide"
        self.nav_open = True
        self._width = 1440.0
        self._sized = False
        self._since: float | None = None
        # The inspector as it was in "wide", shown again when the window gets wide again.
        self._wide_inspector = True
        # The workspace's place on the screen, which the overlays lie over.
        self._area: tuple[float, float, float, float] | None = None
        # The frame an overlay was opened in, and what was selected then (choosing something
        # else in the navigator's list closes it).
        self._opened = -1
        self._selection: object = None
        self._selection_key = selection_key

    def _label(self, name: str) -> Callable[[], str]:
        return self._labels.get(name, lambda: name)

    # The docking layout.

    def dockable_windows(self) -> list[hello_imgui.DockableWindow]:
        windows: list[hello_imgui.DockableWindow] = []
        for name, title, dock, render in (
            (NAVIGATOR, S.NAVIGATOR, "LeftSpace", self._render_navigator),
            (WORKSPACE, S.WORKSPACE, "MainDockSpace", self._render_workspace),
            (INSPECTOR, S.INSPECTOR, "RightSpace", self._render_inspector),
            (BOTTOM, S.BOTTOM_PANEL, "BottomSpace", self._render_bottom),
        ):
            window = hello_imgui.DockableWindow()
            window.label = f"{title}###{name}"
            window.dock_space_name = dock
            window.gui_function = render
            window.can_be_closed = False
            window.include_in_view_menu = False
            window.remember_is_visible = False
            window.imgui_window_flags = imgui.WindowFlags_.no_collapse
            if name == INSPECTOR:
                window.is_visible = self.show_inspector
            elif name == BOTTOM:
                window.is_visible = self.show_bottom
            windows.append(window)
        return windows

    def docking_splits(self) -> list[hello_imgui.DockingSplit]:
        flags = (
            imgui.internal.DockNodeFlagsPrivate_.no_tab_bar
            | imgui.DockNodeFlags_.no_undocking
            | imgui.DockNodeFlags_.no_docking_split
        )
        splits: list[hello_imgui.DockingSplit] = []

        def split(new: str, direction: imgui.Dir, ratio: float) -> None:
            item = hello_imgui.DockingSplit()
            item.initial_dock = "MainDockSpace"
            item.new_dock = new
            item.direction = direction
            item.ratio = ratio
            item.node_flags = flags
            splits.append(item)

        split("LeftSpace", imgui.Dir.left, self._left_ratio())
        if self.show_bottom:
            split("BottomSpace", imgui.Dir.down, 0.26)
        if self.show_inspector and self.mode == "wide":
            split("RightSpace", imgui.Dir.right, 0.24)
        return splits

    def list_docked(self) -> bool:
        """Whether the navigator's list is in its zone (else only the rail is)."""
        return self.mode == "wide" or (self.mode == "mid" and self.nav_open)

    def _left_ratio(self) -> float:
        width = max(self._width, 1.0)
        if self.mode == "wide":
            return 0.25
        if self.list_docked():
            return min(0.4, px(_RAIL_WIDTH + 270.0) / width)
        return min(0.3, px(_RAIL_WIDTH + 16.0) / width)

    def main_dock_space_flags(self) -> int:
        return int(
            imgui.internal.DockNodeFlagsPrivate_.no_tab_bar
            | imgui.DockNodeFlags_.no_undocking
        )

    def _relayout(self) -> None:
        """Build the zones again after the inspector or the bottom panel was shown or hidden."""
        params = hello_imgui.get_runner_params().docking_params
        for window in params.dockable_windows:
            name = window.label.split("###")[-1]
            if name == INSPECTOR:
                window.is_visible = self.show_inspector and self.mode == "wide"
            elif name == BOTTOM:
                window.is_visible = self.show_bottom
        params.docking_splits = self.docking_splits()
        params.layout_reset = True

    def toggle_inspector(self) -> None:
        self.show_inspector = not self.show_inspector
        if self.mode == "wide":
            self._relayout()
        elif self.show_inspector:
            # One overlay at a time.
            self._opened = imgui.get_frame_count()
            if self.mode == "narrow":
                self.nav_open = False

    def toggle_nav(self) -> None:
        """Fold the navigator's list away or show it again (it is always there in "wide")."""
        self.nav_open = not self.nav_open
        if self.mode == "mid":
            self._relayout()
        elif self.nav_open:
            self._opened = imgui.get_frame_count()
            self._selection = self._selection_key() if self._selection_key else None
            self.show_inspector = False

    def update_size(self, width: float) -> None:
        """Switch to the layout for a window of this width, once the width has settled."""
        wanted = layout_mode(width, self.mode)
        if self._sized and wanted == self.mode:
            self._since = None
            self._width = width
            return
        if self._sized:
            now = time.monotonic()
            if self._since is None:
                self._since = now
            if now - self._since < _SETTLE:
                return
        self._since = None
        self._sized = True
        self._width = width
        self._set_mode(wanted)

    def _set_mode(self, mode: str) -> None:
        was = self.mode
        self.mode = mode
        if was == "wide" and mode != "wide":
            self._wide_inspector = self.show_inspector
            self.show_inspector = False
        elif mode == "wide" and was != "wide":
            self.show_inspector = self._wide_inspector
        self.nav_open = mode == "mid"
        self._relayout()

    def toggle_bottom(self) -> None:
        self.show_bottom = not self.show_bottom
        self._relayout()

    # Where a panel is: other parts of the app ask for one to be shown.

    def show(self, name: str) -> None:
        """Bring the panel ``name`` to the front: its area and tab, its navigator view, its
        inspector section or its tab of the bottom panel."""
        if name in _NAVIGATOR_VIEWS:
            self.view = name
            self._select_view = name
            if self.mode != "wide" and not self.nav_open:
                self.toggle_nav()
            return
        if name in _INSPECTOR_PANELS:
            if not self.show_inspector:
                self.toggle_inspector()
            return
        if name in _BOTTOM_PANELS:
            self.bottom_tab = name
            self._select_bottom = name
            if not self.show_bottom:
                self.toggle_bottom()
            return
        for area in self._areas:
            if name in area.panels:
                self.area = area.key
                self._tab[area.key] = name
                self._select_tab = name
                return

    # The zones.

    def _panel(self, name: str) -> None:
        panel = self._panels.get(name)
        if panel is None:
            return
        imgui.push_id(name)
        if imgui.begin_child(f"##wb_{name}", imgui.ImVec2(0, 0)):
            panel.render()
        imgui.end_child()
        imgui.pop_id()

    def _render_navigator(self) -> None:
        imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(0, px(4)))
        if imgui.begin_child(
            "##wb_rail",
            imgui.ImVec2(px(_RAIL_WIDTH), 0),
            0,
            imgui.WindowFlags_.no_scrollbar,
        ):
            for area in self._areas:
                if self._rail_button(area):
                    self.area = area.key
                    if self.mode == "narrow":
                        self.nav_open = False
        imgui.end_child()
        imgui.pop_style_var()
        if not self.list_docked():
            return
        imgui.same_line()
        low = imgui.get_cursor_screen_pos()
        imgui.get_window_draw_list().add_line(
            imgui.ImVec2(low.x - px(4), low.y - imgui.get_style().window_padding.y),
            imgui.ImVec2(
                low.x - px(4), low.y + imgui.get_content_region_avail().y + px(8)
            ),
            imgui.get_color_u32(imgui.Col_.border),
        )
        if imgui.begin_child("##wb_nav", imgui.ImVec2(0, 0)):
            self._render_nav_list()
        imgui.end_child()

    def _render_nav_list(self) -> None:
        """The navigator's views as tabs, and the one shown."""
        if begin_tab_bar("##wb_views"):
            for view in _NAVIGATOR_VIEWS:
                flags = (
                    imgui.TabItemFlags_.set_selected if self._select_view == view else 0
                )
                if imgui.begin_tab_item(f"{self._label(view)()}###{view}", None, flags)[
                    0
                ]:
                    # A view asked for shows at once; its tab follows in the next frame.
                    if self._select_view is None:
                        self.view = view
                    imgui.end_tab_item()
            imgui.end_tab_bar()
        self._select_view = None
        self._panel(self.view)

    def _rail_button(self, area: _Area) -> bool:
        """An icon over its label, filled while its area is shown."""
        size = imgui.ImVec2(px(_RAIL_WIDTH) - px(8), px(_RAIL_BUTTON_HEIGHT))
        imgui.set_cursor_pos_x(px(4))
        clicked = imgui.invisible_button(f"##rail_{area.key}", size)
        low, high = imgui.get_item_rect_min(), imgui.get_item_rect_max()
        on = area.key == self.area
        draw = imgui.get_window_draw_list()
        # As the theme draws a button: its corners, its hovered color, and the chosen area
        # pressed (see chosen_fill).
        rounding = imgui.get_style().frame_rounding
        if on:
            draw.add_rect_filled(
                low, high, imgui.get_color_u32(chosen_fill()), rounding
            )
        elif imgui.is_item_hovered():
            draw.add_rect_filled(
                low, high, imgui.get_color_u32(imgui.Col_.button_hovered), rounding
            )
        color = imgui.get_color_u32(imgui.Col_.text if on else imgui.Col_.text_disabled)
        label = area.label()
        icon_size = imgui.calc_text_size(area.icon)
        label_size = imgui.calc_text_size(label)
        top = low.y + (size.y - icon_size.y - label_size.y - px(3)) / 2
        draw.add_text(
            imgui.ImVec2(low.x + (size.x - icon_size.x) / 2, top), color, area.icon
        )
        draw.push_clip_rect(low, high, True)
        draw.add_text(
            imgui.ImVec2(
                low.x + max(0.0, (size.x - label_size.x) / 2), top + icon_size.y + px(3)
            ),
            color,
            label,
        )
        draw.pop_clip_rect()
        if imgui.is_item_hovered() and label_size.x > size.x:
            imgui.set_tooltip(label)
        return clicked

    def _render_workspace(self) -> None:
        position, size = imgui.get_window_pos(), imgui.get_window_size()
        self._area = (position.x, position.y, size.x, size.y)
        area = next(a for a in self._areas if a.key == self.area)
        panels = [name for name in area.panels if name in self._panels]
        if len(panels) == 1:
            self._panel(panels[0])
            return
        current = self._tab.get(area.key, panels[0])
        if begin_tab_bar(f"##wb_tabs_{area.key}"):
            for name in panels:
                flags = (
                    imgui.TabItemFlags_.set_selected if self._select_tab == name else 0
                )
                if imgui.begin_tab_item(f"{self._label(name)()}###{name}", None, flags)[
                    0
                ]:
                    current = name
                    self._panel(name)
                    imgui.end_tab_item()
            imgui.end_tab_bar()
        self._tab[area.key] = current
        self._select_tab = None

    def _render_inspector(self) -> None:
        offer = state.inspector_offer()
        if offer is not None and self.area == "project":
            title, render = offer
            imgui.push_id("wb_offer")
            if collapsing_header(
                f"{title}###wb_offer", imgui.TreeNodeFlags_.default_open
            ):
                render()
                imgui.spacing()
            imgui.pop_id()
        title, device = (
            self._device_section()
            if self._device_section is not None
            else (self._label("device")(), True)
        )
        for name in _INSPECTOR_PANELS:
            if name not in self._panels:
                continue
            # The manufacturer's section only while a device is selected.
            if name == "manufacturer" and not device:
                continue
            label = title if name == "device" else self._label(name)()
            flags = imgui.TreeNodeFlags_.default_open if name == "device" else 0
            imgui.push_id(name)
            if collapsing_header(f"{label}###{name}", flags):
                self._panels[name].render()
                imgui.spacing()
            imgui.pop_id()

    # The overlays of "mid" and "narrow": the inspector, and in "narrow" the navigator's list.

    def render_overlays(self) -> None:
        """Draw the overlay over the workspace, after the zones. A click beside it closes it, so
        does choosing something in the navigator's list."""
        if self.mode == "wide" or self._area is None:
            return
        if self.mode == "narrow" and self.nav_open:
            selection = self._selection_key() if self._selection_key else None
            if selection != self._selection:
                self.nav_open = False
                return
            self._overlay("navigator", S.NAVIGATOR, self._render_nav_list)
        elif self.show_inspector:
            self._overlay("inspector", S.INSPECTOR, self._render_inspector)

    def _overlay(self, kind: str, title: str, body: Callable[[], None]) -> None:
        assert self._area is not None
        x, y, width, height = self._area
        opening = imgui.get_frame_count() <= self._opened + 1
        # The workspace dimmed; a click on it closes the overlay.
        imgui.set_next_window_pos(imgui.ImVec2(x, y))
        imgui.set_next_window_size(imgui.ImVec2(width, height))
        imgui.push_style_var(imgui.StyleVar_.window_padding, imgui.ImVec2(0, 0))
        # The zones are drawn with the docking space, which comes to the front when something in
        # them is clicked: the scrim and the overlay are brought over it again in each frame.
        imgui.set_next_window_focus()
        closed = False
        if imgui.begin(
            f"##wb_scrim_{kind}",
            None,
            imgui.WindowFlags_.no_decoration
            | imgui.WindowFlags_.no_background
            | imgui.WindowFlags_.no_move
            | imgui.WindowFlags_.no_saved_settings
            | imgui.WindowFlags_.no_docking
            | imgui.WindowFlags_.no_nav,
        ):
            imgui.get_window_draw_list().add_rect_filled(
                imgui.ImVec2(x, y),
                imgui.ImVec2(x + width, y + height),
                imgui.get_color_u32(imgui.ImVec4(0.0, 0.0, 0.0, 0.32)),
            )
            imgui.invisible_button(
                f"##wb_scrim_button_{kind}", imgui.ImVec2(width, height)
            )
            # On the press, not the release: a touch screen or the browser UI may deliver both in
            # one frame, which a button does not count as a click.
            closed = (
                imgui.is_item_hovered() and imgui.is_mouse_clicked(0) and not opening
            )
        imgui.end()
        imgui.pop_style_var()
        left, top, over_width, over_height = overlay_rect(
            self.mode, kind, self._area, px(1.0)
        )
        imgui.set_next_window_pos(imgui.ImVec2(left, top))
        imgui.set_next_window_size(imgui.ImVec2(over_width, over_height))
        imgui.set_next_window_focus()
        expanded, opened = imgui.begin(
            f"{title}###wb_overlay_{kind}",
            True,
            imgui.WindowFlags_.no_collapse
            | imgui.WindowFlags_.no_move
            | imgui.WindowFlags_.no_resize
            | imgui.WindowFlags_.no_saved_settings
            | imgui.WindowFlags_.no_docking,
        )
        if expanded:
            body()
        imgui.end()
        if closed or not opened:
            if kind == "navigator":
                self.nav_open = False
            else:
                self.show_inspector = False

    def _render_bottom(self) -> None:
        if begin_tab_bar("##wb_bottom_tabs"):
            for name in _BOTTOM_PANELS:
                if name not in self._panels:
                    continue
                flags = (
                    imgui.TabItemFlags_.set_selected
                    if self._select_bottom == name
                    else 0
                )
                if imgui.begin_tab_item(f"{self._label(name)()}###{name}", None, flags)[
                    0
                ]:
                    self.bottom_tab = name
                    self._panel(name)
                    imgui.end_tab_item()
            imgui.end_tab_bar()
        self._select_bottom = None
