"""The workbench's zones: the navigator with the activity rail on the left, the workspace in the
middle, the inspector on the right and the bottom panel. Each zone is one docked window without a
tab bar that draws the usual panels (their ``render``) where they belong, so every panel works as
before; only where it is shown changes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from imgui_bundle import hello_imgui, imgui

from editor_gui.plugins.base.registry import PanelDefinition
from editor_gui.widgets.dpi import px
from editor_gui.widgets.tree import collapsing_header
from editor_gui.workbench import state
from editor_gui.workbench.group_objects import segmented
from editor_gui.workbench.strings import S

# Font Awesome 6 icons of the activity rail.
_ICON_PROJECT = ""  # folder-open
_ICON_CATALOG = ""  # book
_ICON_BUS = ""  # clock-rotate-left (history of telegrams)
_ICON_CHECK = ""  # clipboard-check
_ICON_TOOLS = ""  # wrench

_RAIL_WIDTH = 72.0
_RAIL_BUTTON_HEIGHT = 54.0

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
    ) -> None:
        self._panels = {panel.name: panel for panel in panels}
        self._labels = labels
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
        self._tab: dict[str, str] = {}
        self._select_tab: str | None = None
        self.bottom_tab = "operations"
        self._select_bottom: str | None = None
        self.show_inspector = True
        self.show_bottom = True

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

        split("LeftSpace", imgui.Dir.left, 0.25)
        if self.show_bottom:
            split("BottomSpace", imgui.Dir.down, 0.26)
        if self.show_inspector:
            split("RightSpace", imgui.Dir.right, 0.24)
        return splits

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
                window.is_visible = self.show_inspector
            elif name == BOTTOM:
                window.is_visible = self.show_bottom
        params.docking_splits = self.docking_splits()
        params.layout_reset = True

    def toggle_inspector(self) -> None:
        self.show_inspector = not self.show_inspector
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
        imgui.end_child()
        imgui.pop_style_var()
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
            views = list(_NAVIGATOR_VIEWS)
            index = views.index(self.view) if self.view in views else 0
            index = segmented(
                "wb_views", [self._label(view)() for view in views], index
            )
            self.view = views[index]
            imgui.spacing()
            self._panel(self.view)
        imgui.end_child()

    def _rail_button(self, area: _Area) -> bool:
        """An icon over its label, filled while its area is shown."""
        size = imgui.ImVec2(px(_RAIL_WIDTH) - px(8), px(_RAIL_BUTTON_HEIGHT))
        imgui.set_cursor_pos_x(px(4))
        clicked = imgui.invisible_button(f"##rail_{area.key}", size)
        low, high = imgui.get_item_rect_min(), imgui.get_item_rect_max()
        on = area.key == self.area
        draw = imgui.get_window_draw_list()
        accent = imgui.get_style_color_vec4(imgui.Col_.check_mark)
        if on:
            draw.add_rect_filled(
                low,
                high,
                imgui.get_color_u32(imgui.ImVec4(accent.x, accent.y, accent.z, 0.22)),
                px(8),
            )
        elif imgui.is_item_hovered():
            draw.add_rect_filled(
                low, high, imgui.get_color_u32(imgui.Col_.frame_bg_hovered), px(8)
            )
        color = (
            imgui.get_color_u32(accent)
            if on
            else imgui.get_color_u32(imgui.Col_.text_disabled)
        )
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
        area = next(a for a in self._areas if a.key == self.area)
        panels = [name for name in area.panels if name in self._panels]
        if len(panels) == 1:
            self._panel(panels[0])
            return
        current = self._tab.get(area.key, panels[0])
        if imgui.begin_tab_bar(f"##wb_tabs_{area.key}"):
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
        for name in _INSPECTOR_PANELS:
            if name not in self._panels:
                continue
            flags = imgui.TreeNodeFlags_.default_open if name == "device" else 0
            imgui.push_id(name)
            if collapsing_header(f"{self._label(name)()}###{name}", flags):
                self._panels[name].render()
                imgui.spacing()
            imgui.pop_id()

    def _render_bottom(self) -> None:
        if imgui.begin_tab_bar("##wb_bottom_tabs"):
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
