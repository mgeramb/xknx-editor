"""The app's menus in the macOS menu bar at the top of the screen (an ``NSMenu``, through PyObjC).

The menus stay the ImGui code they are (``imgui.begin_menu`` / ``imgui.menu_item``): a pass that
draws nothing records them as a tree (labels, shortcuts, ticks, enabled), and the native menu is
built from that tree, again whenever it changes. Choosing an entry in the native menu runs the
same menu code once more in the next frame, where only that entry reports a click. So every menu
has one source, and an entry does in the menu bar exactly what it does in the window.

AppKit calls the menu's actions on the main thread between two frames (GLFW hands it its events
there), so they are only queued, and run in the frame.
"""

from __future__ import annotations

import contextlib
import importlib
import sys
import time
from collections.abc import Callable, Generator, Sequence
from dataclasses import dataclass, field
from typing import Any

from imgui_bundle import imgui

# How often the menus are recorded again to bring the native one up to date (seconds).
_REFRESH = 0.5
# Shortcuts the native menu takes as key equivalents (⌘ + key). Others (⌘Z in text fields) stay
# with ImGui, and are only shown.
_KEY_EQUIVALENTS = frozenset("nops,")


@dataclass
class _Entry:
    """A menu entry: an item, a submenu (``children`` is not None) or a separator."""

    label: str
    shortcut: str = ""
    checked: bool = False
    enabled: bool = True
    children: list[_Entry] | None = None
    separator: bool = False


@dataclass
class _Recorder:
    """Stands in for ImGui's menu functions while the menus run: records them, or reports a
    click on the entry ``target`` (the labels from the top menu down)."""

    target: tuple[str, ...] | None = None
    root: list[_Entry] = field(default_factory=list[_Entry])
    stack: list[list[_Entry]] = field(default_factory=list[list[_Entry]])
    path: list[str] = field(default_factory=list[str])

    def entries(self) -> list[_Entry]:
        return self.stack[-1] if self.stack else self.root

    def begin_menu(self, label: str, enabled: bool = True) -> bool:
        if self.target is not None:
            depth = len(self.path)
            if depth < len(self.target) - 1 and self.target[depth] == label and enabled:
                self.path.append(label)
                return True
            return False
        entry = _Entry(label, enabled=enabled, children=[])
        self.entries().append(entry)
        if not enabled:
            return False
        self.stack.append(entry.children or [])
        entry.children = self.stack[-1]
        self.path.append(label)
        return True

    def end_menu(self) -> None:
        if self.target is None and self.stack:
            self.stack.pop()
        if self.path:
            self.path.pop()

    def _item(self, label: str, shortcut: str, selected: bool, enabled: bool) -> bool:
        if self.target is not None:
            return enabled and (*self.path, label) == self.target
        self.entries().append(_Entry(label, shortcut, selected, enabled))
        return False

    def menu_item(
        self,
        label: str,
        shortcut: str = "",
        p_selected: bool = False,
        enabled: bool = True,
    ) -> tuple[bool, bool]:
        clicked = self._item(label, shortcut, p_selected, enabled)
        return clicked, (not p_selected) if clicked else p_selected

    def menu_item_simple(
        self,
        label: str,
        shortcut: str = "",
        selected: bool = False,
        enabled: bool = True,
    ) -> bool:
        return self._item(label, shortcut, selected, enabled)

    def separator(self) -> None:
        if self.target is None:
            self.entries().append(_Entry("", separator=True))


@contextlib.contextmanager
def _recording(recorder: _Recorder) -> Generator[None]:
    """ImGui's menu functions replaced by ``recorder``'s."""
    names = ("begin_menu", "end_menu", "menu_item", "menu_item_simple", "separator")
    saved = {name: getattr(imgui, name) for name in names}
    for name in names:
        setattr(imgui, name, getattr(recorder, name))
    try:
        yield
    finally:
        for name, function in saved.items():
            setattr(imgui, name, function)


def _shown(label: str) -> str:
    """A label as the native menu shows it: without its ImGui id and the icon font's glyphs
    (private use characters, which the system font lacks)."""
    text = label.split("##")[0]
    return "".join(c for c in text if not 0xE000 <= ord(c) <= 0xF8FF).strip()


def _signature(entries: Sequence[_Entry]) -> tuple[Any, ...]:
    return tuple(
        (
            e.label,
            e.shortcut,
            e.checked,
            e.enabled,
            e.separator,
            _signature(e.children) if e.children is not None else None,
        )
        for e in entries
    )


Menus = Callable[[], list[tuple[str, Callable[[], None]]]]


class MacMenuBar:
    """The native menu bar: the app menu (About, Settings, Hide, Quit) and the app's menus."""

    def __init__(
        self,
        app_name: str,
        menus: Menus,
        *,
        about: Callable[[], None],
        settings: Callable[[], None],
        quit_app: Callable[[], None],
    ) -> None:
        assert sys.platform == "darwin"
        self._objc = importlib.import_module("objc")
        self._appkit = importlib.import_module("AppKit")
        self._foundation = importlib.import_module("Foundation")
        self._app_name = app_name
        self._menus = menus
        self._fixed = {"about": about, "settings": settings, "quit": quit_app}
        self._queued: list[tuple[str, ...]] = []
        self._signature: tuple[Any, ...] | None = None
        self._recorded_at = 0.0
        self._target = self._make_target()

    def _make_target(self) -> Any:
        """The object that receives the native menu's actions (its items' ``representedObject``
        is the entry's path)."""
        bar = self
        foundation, objc = self._foundation, self._objc

        def chosen(_self: Any, sender: Any) -> None:
            path = sender.representedObject()
            if path is not None:
                bar._queued.append(tuple(str(part) for part in path))

        target_class = type(
            "XknxEditorMenuTarget",
            (foundation.NSObject,),
            {"chosen_": objc.selector(chosen, selector=b"chosen:", signature=b"v@:@")},
        )
        return target_class.alloc().init()

    # Every frame, in the menu bar of the window.

    def frame(self) -> None:
        """Run the entries chosen since the last frame, and bring the native menu up to date."""
        queued, self._queued = self._queued, []
        for path in queued:
            self._run(path)
        now = time.monotonic()
        if now - self._recorded_at >= _REFRESH:
            self._recorded_at = now
            self._refresh()

    def _run(self, path: tuple[str, ...]) -> None:
        if path[0] == "":
            action = self._fixed.get(path[1])
            if action is not None:
                action()
            return
        for label, render in self._menus():
            if label == path[0]:
                recorder = _Recorder(target=path[1:])
                with _recording(recorder):
                    render()
                return

    def _record(self) -> list[_Entry]:
        """The app's menus as a tree, recorded in a window outside the screen (whatever else the
        menus draw is not seen)."""
        top: list[_Entry] = []
        imgui.set_next_window_pos(imgui.ImVec2(-10000.0, -10000.0))
        flags = (
            imgui.WindowFlags_.no_decoration
            | imgui.WindowFlags_.no_saved_settings
            | imgui.WindowFlags_.no_focus_on_appearing
            | imgui.WindowFlags_.no_nav
            | imgui.WindowFlags_.no_inputs
            | imgui.WindowFlags_.no_bring_to_front_on_focus
        )
        imgui.begin("##mac_menu_record", None, flags)
        for label, render in self._menus():
            recorder = _Recorder()
            with _recording(recorder):
                render()
            top.append(_Entry(label, children=recorder.root))
        imgui.end()
        return top

    def _refresh(self) -> None:
        top = self._record()
        signature = _signature(top)
        if signature == self._signature:
            return
        self._signature = signature
        self._install(top)

    # The native menu.

    def _install(self, top: list[_Entry]) -> None:
        appkit = self._appkit
        main = appkit.NSMenu.alloc().initWithTitle_("")
        main.addItem_(self._app_menu())
        for entry in top:
            item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                _shown(entry.label), None, ""
            )
            item.setSubmenu_(self._submenu(entry, (entry.label,)))
            main.addItem_(item)
        appkit.NSApplication.sharedApplication().setMainMenu_(main)

    def _submenu(self, entry: _Entry, path: tuple[str, ...]) -> Any:
        appkit = self._appkit
        menu = appkit.NSMenu.alloc().initWithTitle_(_shown(entry.label))
        menu.setAutoenablesItems_(False)
        for child in entry.children or []:
            if child.separator:
                menu.addItem_(appkit.NSMenuItem.separatorItem())
                continue
            item = self._item(
                _shown(child.label), (*path, child.label), child.shortcut
            )
            item.setEnabled_(child.enabled)
            if child.checked:
                item.setState_(appkit.NSControlStateValueOn)
            if child.children is not None:
                item.setSubmenu_(self._submenu(child, (*path, child.label)))
                item.setAction_(None)
            menu.addItem_(item)
        return menu

    def _item(self, title: str, path: tuple[str, ...], shortcut: str = "") -> Any:
        appkit = self._appkit
        key = ""
        lowered = shortcut.lower().replace(" ", "")
        if lowered.startswith(("ctrl+", "cmd+", "⌘")):
            letter = lowered.rsplit("+", 1)[-1].lstrip("⌘")
            if len(letter) == 1 and letter in _KEY_EQUIVALENTS:
                key = letter
        item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            title, b"chosen:", key
        )
        item.setTarget_(self._target)
        item.setRepresentedObject_(list(path))
        if shortcut and not key:
            # Shown beside the title, like a key equivalent the window handles itself.
            item.setToolTip_(shortcut)
        return item

    def _app_menu(self) -> Any:
        """The menu named after the app: About, Settings, Hide, Quit."""
        appkit = self._appkit
        menu = appkit.NSMenu.alloc().initWithTitle_(self._app_name)
        menu.setAutoenablesItems_(False)
        menu.addItem_(self._item(f"About {self._app_name}", ("", "about")))
        menu.addItem_(appkit.NSMenuItem.separatorItem())
        settings = self._item("Settings…", ("", "settings"))
        settings.setKeyEquivalent_(",")
        menu.addItem_(settings)
        menu.addItem_(appkit.NSMenuItem.separatorItem())
        app = appkit.NSApplication.sharedApplication()
        for title, selector, key in (
            (f"Hide {self._app_name}", b"hide:", "h"),
            ("Show All", b"unhideAllApplications:", ""),
        ):
            item = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title, selector, key
            )
            item.setTarget_(app)
            menu.addItem_(item)
        menu.addItem_(appkit.NSMenuItem.separatorItem())
        quit_item = self._item(f"Quit {self._app_name}", ("", "quit"))
        quit_item.setKeyEquivalent_("q")
        menu.addItem_(quit_item)
        holder = appkit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            self._app_name, None, ""
        )
        holder.setSubmenu_(menu)
        return holder
