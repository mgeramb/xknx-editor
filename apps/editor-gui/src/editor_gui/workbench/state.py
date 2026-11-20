"""What the workbench and the panels drawn in it share."""

from __future__ import annotations

import os
from collections.abc import Callable

from imgui_bundle import imgui


def enabled() -> bool:
    """Whether the editor shows the redesign's layout (``XKNX_REDESIGN=1``)."""
    return os.environ.get("XKNX_REDESIGN", "").strip() == "1"


_offer: tuple[int, str, Callable[[], None]] | None = None


def offer_inspector(title: str, render: Callable[[], None]) -> None:
    """A panel offers the inspector a section ``title`` for what is selected in it (call each
    frame while it applies)."""
    global _offer
    _offer = (imgui.get_frame_count(), title, render)


def inspector_offer() -> tuple[str, Callable[[], None]] | None:
    """The section offered in this or the last frame."""
    if _offer is None or imgui.get_frame_count() - _offer[0] > 1:
        return None
    return _offer[1], _offer[2]
