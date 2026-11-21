"""The Group Objects tab of the redesign: objects grouped by channel, a two-line object and data
type cell, flags as letter toggles, one row height (the sending group address as a chip, the
others as "+N"), a filter, a selection bar only while objects are checked, and the details of the
clicked object in the inspector.

It is the usual :class:`GroupObjectsTable` with another ``render``: linking, the dialogs, copy and
paste and the batch creation are the same, and so every edit is the same undo step.
"""

from __future__ import annotations

from imgui_bundle import imgui

from editor_gui.color import sending_green
from editor_gui.device import (
    FLAG_LABELS,
    ComObject,
    Device,
    flag_letter,
    flag_name,
    object_size_text,
)
from editor_gui.widgets.checkbox import checkbox
from editor_gui.widgets.choice import chosen_fill
from editor_gui.widgets.dpi import px
from editor_gui.widgets.filter_box import filter_box
from editor_gui.widgets.flow import button_width, checkbox_width, same_line_if_fits
from editor_gui.widgets.fonts import bold, monospace
from editor_gui.widgets.group_objects_widgets import (
    GroupAddressCatalog,
    GroupLink,
    GroupLinkResolver,
    GroupObjectsTable,
    priority_text,
)
from editor_gui.widgets.strings import S as WS
from editor_gui.workbench import state
from editor_gui.workbench.strings import S

_FILTERS = ("all", "linked", "unlinked")
# Group objects of no channel are listed under this key.
_NO_CHANNEL = ""
# The width under which the table scrolls sideways.
_TABLE_MIN_WIDTH = 780.0
# Font Awesome carets of an open and a closed channel.
_OPEN = "\uf0d7"
_CLOSED = "\uf0da"


def _soft(color: imgui.ImVec4, alpha: float) -> int:
    return imgui.get_color_u32(imgui.ImVec4(color.x, color.y, color.z, alpha))


def toggle_button(
    label: str, on: bool, size: imgui.ImVec2 | None = None, *, dim_off: bool = False
) -> bool:
    """A button in the theme's colors and corners that stays pressed while ``on`` (in the
    theme's chosen fill, see :func:`chosen_fill`); with ``dim_off`` its text is dimmed while it
    is off. Whether it was clicked."""
    colors = 0
    if on:
        imgui.push_style_color(imgui.Col_.button, chosen_fill())
        colors += 1
    elif dim_off:
        imgui.push_style_color(
            imgui.Col_.text, imgui.get_style_color_vec4(imgui.Col_.text_disabled)
        )
        colors += 1
    clicked = imgui.button(label, size if size is not None else imgui.ImVec2(0, 0))
    imgui.pop_style_color(colors)
    return clicked


def segmented(str_id: str, labels: list[str], current: int) -> int:
    """A segmented control: toggle buttons side by side, the chosen one pressed; the chosen
    index."""
    imgui.push_id(str_id)
    imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(px(2), px(2)))
    chosen = current
    for index, label in enumerate(labels):
        if index:
            imgui.same_line()
        if toggle_button(f"{label}##{index}", index == current):
            chosen = index
    imgui.pop_style_var()
    imgui.pop_id()
    return chosen


def chip(
    str_id: str, text: str, *, sending: bool = False, dashed: bool = False
) -> bool:
    """A rounded label one text line high; whether it was clicked."""
    pad = px(7)
    size = imgui.ImVec2(
        imgui.calc_text_size(text).x + 2 * pad, imgui.get_text_line_height() + px(4)
    )
    clicked = imgui.invisible_button(str_id, size)
    low, high = imgui.get_item_rect_min(), imgui.get_item_rect_max()
    draw = imgui.get_window_draw_list()
    hovered = imgui.is_item_hovered()
    if sending:
        green = sending_green()
        fill = _soft(green, 0.28 if hovered else 0.18)
        border = _soft(green, 0.0)
    else:
        fill = imgui.get_color_u32(
            imgui.Col_.frame_bg_hovered if hovered else imgui.Col_.frame_bg
        )
        border = imgui.get_color_u32(imgui.Col_.border)
    rounding = imgui.get_style().frame_rounding
    if not dashed:
        draw.add_rect_filled(low, high, fill, rounding)
    draw.add_rect(low, high, border, rounding)
    text_color = imgui.get_color_u32(
        imgui.Col_.text_disabled if dashed else imgui.Col_.text
    )
    draw.add_text(imgui.ImVec2(low.x + pad, low.y + px(2)), text_color, text)
    if hovered:
        imgui.set_mouse_cursor(imgui.MouseCursor_.hand)
    return clicked


def _direction(com_object: ComObject) -> str:
    """↑ sends, ↓ receives, ⇅ both, from the object's flags."""
    flags = com_object.flags
    sends = flags.transmit or flags.read
    receives = flags.write or flags.update
    if sends and receives:
        return "⇅"
    if sends:
        return "↑"
    if receives:
        return "↓"
    return "·"


class RedesignedGroupObjectsTable(GroupObjectsTable):
    """:class:`GroupObjectsTable` drawn as the redesign shows it."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # pyright: ignore[reportArgumentType]
        self._filter = 0
        self._search = ""
        self._closed: set[str] = set()
        # The object clicked last: its details are in the inspector.
        self._focus: str | None = None
        self._focus_device: Device | None = None
        self._focus_links: GroupLinkResolver | None = None
        self._channels_device: Device | None = None
        self._channels: dict[str, str] = {}
        self._row_links: GroupLinkResolver = lambda _db_id: []

    # The table.

    def render(
        self,
        device: Device,
        com_objects: list[ComObject],
        get_links: GroupLinkResolver,
        get_all_group_addresses: GroupAddressCatalog,
    ) -> None:
        if self._filter_device is not device:
            self._filter_device = device
            self._module_ids = None
            self._selected.clear()
            self._focus = None
            self._batch_open = False
        if self._channels_device is not device:
            self._channels_device = device
            self._channels = device.com_object_channels()
        self._row_links = get_links
        self._render_toolbar(device)
        if self._module_ids is not None:
            visible = {
                co.id for co in device.get_filtered_com_objects(list(self._module_ids))
            }
            com_objects = [co for co in com_objects if co.id in visible]
        self._selected.intersection_update(co.id for co in com_objects)
        self._render_selection_bar(device, com_objects, get_links)

        links = {
            co.id: (get_links(co.db_id) if co.db_id is not None else [])
            for co in com_objects
        }
        shown = [co for co in com_objects if self._matches(co, links[co.id])]
        # Each channel's objects together, the channels in the order they first appear.
        first: dict[str, int] = {}
        for index, co in enumerate(shown):
            first.setdefault(self._channel(co), index)
        shown.sort(key=lambda co: first[self._channel(co)])

        flags = (
            imgui.TableFlags_.borders_inner_h
            | imgui.TableFlags_.sizing_fixed_fit
            | imgui.TableFlags_.scroll_y
            | imgui.TableFlags_.scroll_x
            | imgui.TableFlags_.pad_outer_x
        )
        # Scrolls sideways where the workspace is narrower than the columns need.
        inner = max(imgui.get_content_region_avail().x, px(_TABLE_MIN_WIDTH))
        if not imgui.begin_table(
            "##wb_group_objects", 7, flags, imgui.ImVec2(0, 0), inner
        ):
            return
        imgui.table_setup_scroll_freeze(0, 1)
        imgui.table_setup_column("##check", imgui.TableColumnFlags_.width_fixed)
        imgui.table_setup_column("#", imgui.TableColumnFlags_.width_fixed, px(48))
        stretch = imgui.TableColumnFlags_.width_stretch
        imgui.table_setup_column(S.COL_OBJECT, stretch, 1.6)
        imgui.table_setup_column(
            S.COL_DATA_TYPE, imgui.TableColumnFlags_.width_fixed, px(150)
        )
        imgui.table_setup_column(S.COL_FLAGS, imgui.TableColumnFlags_.width_fixed)
        imgui.table_setup_column(WS.GROUP_OBJECTS_COL_GROUP_ADDRESSES, stretch, 1.4)
        imgui.table_setup_column(
            S.COL_LAST_VALUE, imgui.TableColumnFlags_.width_fixed, px(110)
        )
        self._render_header_row(shown)

        channel: str | None = None
        for co in shown:
            name = self._channel(co)
            if name != channel:
                channel = name
                members = [c for c in shown if self._channel(c) == name]
                self._render_channel_row(name, members, links)
            if name in self._closed:
                continue
            self._render_object_row(device, co, links[co.id])
        imgui.end_table()
        # Offered after the rows: a click on one shows it in the inspector in the same frame.
        if self._focus is not None:
            self._focus_device = device
            self._focus_links = get_links
            state.offer_inspector(S.GROUP_OBJECT, self.render_inspector)
        if not shown:
            imgui.dummy(imgui.ImVec2(0, px(24)))
            imgui.text_disabled(S.NO_OBJECTS)
        self._render_add_window(get_links, get_all_group_addresses)
        self._render_description_popup()

    def _channel(self, co: ComObject) -> str:
        """The channel the object is listed under: its module, or else its name (which many
        devices give every object of a channel, e.g. "Channel A: Living Room")."""
        if self._channels:
            return self._channels.get(co.id, _NO_CHANNEL)
        return co.name

    def _row_texts(self, co: ComObject) -> tuple[str, str]:
        """The two lines of the object cell: what the object does and what tells it apart."""
        function = co.function_text if co.function_text != co.name else ""
        if self._channels:
            return co.name, function
        return function or co.name, co.description

    def _render_toolbar(self, device: Device) -> None:
        """The search, the filter and the module filter in one row, or the filter below the
        search where the workspace is narrow."""
        labels = [S.FILTER_ALL, S.FILTER_LINKED, S.FILTER_UNLINKED]
        spacing = imgui.get_style().item_spacing.x
        filters = sum(button_width(label) + px(2) for label in labels)
        modules = bool(any(device.get_com_object_modules()))
        reserve = filters + spacing + (px(200) + spacing if modules else 0.0)
        avail = imgui.get_content_region_avail().x
        beside = avail - reserve >= px(220)
        self._search = filter_box(
            "##wb_go_search",
            S.FILTER_HINT,
            self._search,
            reserve=max(reserve, avail - px(420)) if beside else 0.0,
        )
        if beside:
            imgui.same_line()
        self._filter = segmented(
            "wb_go_filter",
            [S.FILTER_ALL, S.FILTER_LINKED, S.FILTER_UNLINKED],
            self._filter,
        )
        if modules:
            imgui.same_line()
            imgui.push_item_width(max(px(140), imgui.get_content_region_avail().x))
            self._render_module_filter(device)
            imgui.pop_item_width()

    def _render_selection_bar(
        self,
        device: Device,
        com_objects: list[ComObject],
        get_links: GroupLinkResolver,
    ) -> None:
        """Only while objects are checked: what can be done with them."""
        selected = [c for c in com_objects if c.id in self._selected]
        if self._on_paste_links is not None:
            self._handle_copy_paste_shortcuts(device, com_objects, get_links)
        if self._on_auto_create_gas is not None:
            self._render_batch_popup(device, selected)
        if not selected:
            return
        draw = imgui.get_window_draw_list()
        low = imgui.get_cursor_screen_pos()
        height = imgui.get_frame_height() + px(10)
        draw.add_rect_filled(
            imgui.ImVec2(low.x - px(4), low.y),
            imgui.ImVec2(
                low.x + imgui.get_content_region_avail().x + px(4), low.y + height
            ),
            imgui.get_color_u32(chosen_fill()),
            imgui.get_style().frame_rounding,
        )
        imgui.set_cursor_screen_pos(imgui.ImVec2(low.x + px(4), low.y + px(5)))
        imgui.align_text_to_frame_padding()
        with bold():
            imgui.text(S.SELECTED(len(selected)).format(count=len(selected)))
        if self._on_auto_create_gas is not None:
            create = WS.GROUP_OBJECTS_BATCH_TITLE + "…"
            same_line_if_fits(button_width(create))
            if imgui.button(create):
                self._batch_open = True
        if self._on_paste_links is not None:
            targets = self._checked_targets(com_objects)
            same_line_if_fits(button_width(WS.GROUP_OBJECTS_CTX_COPY))
            if imgui.button(WS.GROUP_OBJECTS_CTX_COPY):
                self._copy_checked(com_objects, get_links)
            paste = min(len(self._link_clipboard), len(targets))
            same_line_if_fits(button_width(WS.GROUP_OBJECTS_CTX_PASTE))
            imgui.begin_disabled(paste == 0)
            if imgui.button(WS.GROUP_OBJECTS_CTX_PASTE):
                self._paste_to_checked(device, com_objects)
            imgui.end_disabled()
            if imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                imgui.set_tooltip(WS.GROUP_OBJECTS_PASTE_LINKS_HINT)
            same_line_if_fits(checkbox_width(WS.GROUP_OBJECTS_PASTE_MERGE))
            _, self._paste_merge = checkbox(
                WS.GROUP_OBJECTS_PASTE_MERGE, self._paste_merge, centred=True
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip(WS.GROUP_OBJECTS_PASTE_MERGE_HINT)
        same_line_if_fits(button_width(S.CLEAR_SELECTION))
        if imgui.button(S.CLEAR_SELECTION):
            self._selected.clear()
        imgui.set_cursor_screen_pos(imgui.ImVec2(low.x, low.y + height + px(6)))
        imgui.dummy(imgui.ImVec2(0, 0))

    def _matches(self, co: ComObject, links: list[GroupLink]) -> bool:
        if self._filter == 1 and not links:
            return False
        if self._filter == 2 and links:
            return False
        needle = self._search.strip().casefold()
        if not needle:
            return True
        hay = " ".join(
            [
                str(co.number),
                co.name,
                co.function_text,
                co.description,
                self._channels.get(co.id, ""),
                *(text for _a, _g, text, _s in links),
            ]
        ).casefold()
        return needle in hay

    def _render_header_row(self, shown: list[ComObject]) -> None:
        imgui.table_next_row(imgui.TableRowFlags_.headers)
        for column in range(7):
            imgui.table_set_column_index(column)
            if column == 0:
                every = bool(shown) and all(co.id in self._selected for co in shown)
                imgui.begin_disabled(not shown)
                changed, every = checkbox("##wb_all", every)
                imgui.end_disabled()
                if changed:
                    ids = {co.id for co in shown}
                    if every:
                        self._selected |= ids
                    else:
                        self._selected -= ids
                continue
            imgui.text_disabled(imgui.table_get_column_name(column) or "")

    def _render_channel_row(
        self, name: str, members: list[ComObject], links: dict[str, list[GroupLink]]
    ) -> None:
        imgui.table_next_row()
        imgui.table_set_bg_color(
            imgui.TableBgTarget_.row_bg0,
            imgui.get_color_u32(imgui.Col_.table_header_bg),
        )
        imgui.table_set_column_index(0)
        label = name or S.WITHOUT_CHANNEL
        closed = name in self._closed
        arrow = _CLOSED if closed else _OPEN
        if imgui.selectable(
            f"##channel_{name}",
            False,
            imgui.SelectableFlags_.span_all_columns
            | imgui.SelectableFlags_.allow_overlap,
            imgui.ImVec2(0, imgui.get_text_line_height() + px(6)),
        )[0]:
            if closed:
                self._closed.discard(name)
            else:
                self._closed.add(name)
        imgui.same_line()
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + px(3))
        imgui.text_disabled(arrow)
        imgui.table_set_column_index(2)
        imgui.set_cursor_pos_y(imgui.get_cursor_pos_y() + px(3))
        with bold():
            imgui.text(label)
        linked = sum(1 for co in members if links[co.id])
        imgui.same_line()
        imgui.text_disabled(
            S.CHANNEL_SUMMARY.format(
                objects=S.CHANNEL_OBJECTS(len(members)).format(count=len(members)),
                linked=S.CHANNEL_LINKED(linked).format(count=linked),
            )
        )

    def _render_object_row(
        self, device: Device, co: ComObject, links: list[GroupLink]
    ) -> None:
        line = imgui.get_text_line_height_with_spacing()
        height = max(2 * line, imgui.get_frame_height()) + px(8)
        imgui.table_next_row(0, height)
        imgui.push_id(co.id)
        imgui.table_set_column_index(0)
        top = imgui.get_cursor_pos_y()
        focused = co.id == self._focus
        if imgui.selectable(
            "##row",
            focused,
            imgui.SelectableFlags_.span_all_columns
            | imgui.SelectableFlags_.allow_overlap,
            imgui.ImVec2(0, height - 2 * imgui.get_style().cell_padding.y),
        )[0]:
            self._focus = co.id
        if self._on_paste_links is not None or self._on_set_description is not None:
            self._render_row_context_menu(device, co, self._row_links)
        middle = (
            top
            + (height - imgui.get_frame_height()) / 2
            - imgui.get_style().cell_padding.y
        )
        imgui.set_cursor_pos_y(middle)
        if self._on_auto_create_gas is not None:
            changed, on = checkbox("##check", co.id in self._selected)
            if changed:
                if on:
                    self._selected.add(co.id)
                else:
                    self._selected.discard(co.id)

        imgui.table_set_column_index(1)
        imgui.set_cursor_pos_y(middle + imgui.get_style().frame_padding.y)
        imgui.text_disabled(f"{_direction(co)} {co.number}")

        imgui.table_set_column_index(2)
        imgui.set_cursor_pos_y(top + px(2))
        title, detail = self._row_texts(co)
        imgui.text(title)
        if co.description and imgui.is_item_hovered():
            imgui.set_tooltip(co.description)
        imgui.text_disabled(detail or " ")

        imgui.table_set_column_index(3)
        imgui.set_cursor_pos_y(top + px(2))
        dpt = co.dpt
        with monospace():
            imgui.text(dpt.code if getattr(dpt, "major", 0) else "—")
        size = object_size_text(co.object_size)
        name = getattr(dpt, "name", "") or ""
        imgui.text_disabled(" · ".join(part for part in (name, size) if part))
        if name and imgui.is_item_hovered():
            imgui.set_tooltip(f"{name} · {size}")

        imgui.table_set_column_index(4)
        imgui.set_cursor_pos_y(middle)
        self._render_flags(device, co)

        imgui.table_set_column_index(5)
        imgui.set_cursor_pos_y(
            middle
            + (imgui.get_frame_height() - imgui.get_text_line_height() - px(4)) / 2
        )
        self._render_links(device, co, links)

        imgui.table_set_column_index(6)
        imgui.set_cursor_pos_y(top + px(2))
        values = self._latest_values(links, co)
        if values:
            text, when, _at = max(values.values(), key=lambda v: v[2])
            imgui.text(text)
            imgui.text_disabled(when or " ")
        else:
            imgui.text_disabled("—")
        imgui.pop_id()

    def _render_flags(self, device: Device, co: ComObject) -> None:
        """K L S Ü A I (C R W T U I) as small toggles, the set ones filled."""
        side = imgui.get_frame_height()
        imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(px(3), 0))
        imgui.push_style_var(imgui.StyleVar_.frame_padding, imgui.ImVec2(0, 0))
        for index, (attr, _letter, _name) in enumerate(FLAG_LABELS):
            if index:
                imgui.same_line()
            on = bool(getattr(co.flags, attr))
            locked = attr != "communication" and bool(
                getattr(co.flags, f"{attr}_locked", False)
            )
            imgui.begin_disabled(locked)
            if toggle_button(
                f"{flag_letter(attr)}##{attr}",
                on,
                imgui.ImVec2(side, side),
                dim_off=True,
            ):
                self._set_flag(device, co.id, attr, not on)
            imgui.end_disabled()
            if imgui.is_item_hovered(imgui.HoveredFlags_.allow_when_disabled):
                name = flag_name(attr)
                imgui.set_tooltip(
                    WS.TOOLTIP_LOCKED.format(name=name) if locked else name
                )
        imgui.pop_style_var(2)

    def _render_links(
        self, device: Device, co: ComObject, links: list[GroupLink]
    ) -> None:
        """The sending group address (or the first) as a chip, the others as "+N", then "+"."""
        ordered = sorted(links, key=lambda link: not link[3])
        imgui.push_style_var(imgui.StyleVar_.item_spacing, imgui.ImVec2(px(4), 0))
        if ordered:
            _aid, ga_id, text, sending = ordered[0]
            room = imgui.get_content_region_avail().x - px(90)
            shown = text
            while len(shown) > 8 and imgui.calc_text_size(shown).x + px(14) > room:
                shown = shown[:-2]
            if shown != text:
                shown = shown.rstrip() + "…"
            if (
                chip("##ga0", shown, sending=sending)
                and self._on_navigate_ga is not None
            ):
                self._on_navigate_ga(ga_id)
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    f"{text}\n{WS.GA_SENDING if sending else WS.GA_RECEIVING}"
                )
            if self._ga_menu is not None and imgui.begin_popup_context_item(
                "##ga0_ctx"
            ):
                self._ga_menu(ga_id, co)
                imgui.end_popup()
            if len(ordered) > 1:
                imgui.same_line()
                if chip("##more", f"+{len(ordered) - 1}"):
                    self._focus = co.id
                if imgui.is_item_hovered():
                    imgui.set_tooltip("\n".join(t for _a, _g, t, _s in ordered[1:]))
            imgui.same_line()
        if co.db_id is not None and chip("##add", "+", dashed=True):
            self.open_add_dialog(device, co)
        if co.db_id is not None and imgui.is_item_hovered():
            imgui.set_tooltip(WS.GA_LINK_TITLE)
        imgui.pop_style_var()

    # The inspector.

    def render_inspector(self) -> None:
        """The clicked object's details: texts, data type, priority, flags and all its group
        addresses."""
        device, get_links = self._focus_device, self._focus_links
        if device is None or get_links is None or self._focus is None:
            imgui.text_disabled(S.INSPECTOR_HINT)
            return
        co = next(
            (c for c in device.get_visible_com_objects() if c.id == self._focus), None
        )
        if co is None:
            imgui.text_disabled(S.INSPECTOR_HINT)
            return
        with bold():
            imgui.text_wrapped(f"{co.number}  {co.name}")
        if co.function_text and co.function_text != co.name:
            imgui.text_disabled(co.function_text)
        channel = self._channels.get(co.id)
        if channel:
            imgui.text_disabled(channel)
        imgui.spacing()

        imgui.text_disabled(S.DESCRIPTION)
        if co.description:
            imgui.text_wrapped(co.description)
        else:
            imgui.text_disabled(S.NO_DESCRIPTION)
        if self._on_set_description is not None and imgui.button(
            WS.GROUP_OBJECTS_CTX_EDIT_DESCRIPTION
        ):
            self._desc_popup_device = device
            self._desc_popup_co_id = co.id
            self._desc_buffer = co.description
            self._open_desc_popup = True
        imgui.spacing()

        imgui.text_disabled(S.COL_DATA_TYPE)
        if self._on_set_dpt is not None and co.supported_dpts:
            self._render_dpt_combo(device, co)
        else:
            imgui.text(getattr(co.dpt, "name", "") or "—")
        imgui.text_disabled(S.PRIORITY)
        if self._on_set_priority is not None:
            self._render_priority_combo(device, co)
        else:
            imgui.text(priority_text(co.priority))
        imgui.spacing()

        imgui.text_disabled(S.COL_FLAGS)
        for attr, _letter, _name in FLAG_LABELS:
            locked = attr != "communication" and bool(
                getattr(co.flags, f"{attr}_locked", False)
            )
            imgui.begin_disabled(locked)
            changed, value = checkbox(
                f"{flag_name(attr)} ({flag_letter(attr)})##insp_{attr}",
                bool(getattr(co.flags, attr)),
            )
            imgui.end_disabled()
            if changed and not locked:
                self._set_flag(device, co.id, attr, value)
        imgui.spacing()

        imgui.text_disabled(WS.GROUP_OBJECTS_COL_GROUP_ADDRESSES)
        links = get_links(co.db_id) if co.db_id is not None else []
        if not links:
            imgui.text_disabled(S.NO_GROUP_ADDRESS)
        for assignment_id, ga_id, text, sending in sorted(
            links, key=lambda link: not link[3]
        ):
            imgui.push_id(assignment_id)
            if imgui.button("x"):
                self._on_unlink(assignment_id)
            imgui.same_line()
            color = (
                sending_green()
                if sending
                else imgui.get_style_color_vec4(imgui.Col_.text)
            )
            imgui.text_colored(color, ("● " if sending else "") + text)
            if imgui.is_item_hovered():
                imgui.set_tooltip(WS.GA_SENDING if sending else WS.GA_RECEIVING)
                if self._on_navigate_ga is not None:
                    imgui.set_mouse_cursor(imgui.MouseCursor_.hand)
            if self._on_navigate_ga is not None and imgui.is_item_clicked():
                self._on_navigate_ga(ga_id)
            imgui.pop_id()
        if co.db_id is not None and imgui.button(S.LINK_GROUP_ADDRESS):
            self.open_add_dialog(device, co)


def make_group_objects_table(*args: object, **kwargs: object) -> GroupObjectsTable:
    """The Group Objects table of the layout in use."""
    if state.enabled():
        return RedesignedGroupObjectsTable(*args, **kwargs)
    return GroupObjectsTable(*args, **kwargs)  # pyright: ignore[reportArgumentType]
