"""The colors of a chosen item where the theme gives it its own: the open drop-down, its chosen
and hovered entries, the dot of a chosen radio button and a toggle button that is on (the light
theme's blue). The theme sets them (``theme.apply_style``); None keeps the theme's own colors."""

from __future__ import annotations

from dataclasses import dataclass

from imgui_bundle import imgui


@dataclass(frozen=True)
class ChoiceColors:
    # The open drop-down's field, its chosen and hovered entries, a chosen radio button's dot and
    # a toggle button that is on (a group object's flag, a filter, an area of the rail).
    fill: imgui.ImVec4
    # The background of a drop-down's list.
    list_bg: imgui.ImVec4


_colors: ChoiceColors | None = None


def set_choice_colors(colors: ChoiceColors | None) -> None:
    global _colors
    _colors = colors


def choice_colors() -> ChoiceColors | None:
    return _colors


def chosen_fill() -> imgui.ImVec4:
    """The fill of a toggle button that is on: the theme's choice color where it has one, else
    the color of its pressed buttons."""
    if _colors is not None:
        return _colors.fill
    return imgui.get_style_color_vec4(imgui.Col_.button_active)
