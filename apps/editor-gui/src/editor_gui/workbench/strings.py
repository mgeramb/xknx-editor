"""Strings of the workbench, the layout of fixed zones (redesign preview)."""

from pathlib import Path

from editor_gui.strings import create_translator

_locale_dir = Path(__file__).parent / "locales"
_ = create_translator("workbench", _locale_dir)


class WorkbenchStrings:
    # Areas of the activity rail.
    @property
    def AREA_PROJECT(self) -> str:
        return _("Project")

    @property
    def AREA_BUS(self) -> str:
        return _("Bus")

    @property
    def AREA_CHECK(self) -> str:
        return _("Check")

    # Zones.
    @property
    def NAVIGATOR(self) -> str:
        return _("Navigator")

    @property
    def WORKSPACE(self) -> str:
        return _("Workspace")

    @property
    def INSPECTOR(self) -> str:
        return _("Inspector")

    @property
    def BOTTOM_PANEL(self) -> str:
        return _("Bottom Panel")

    # Top bar.
    @property
    def SEARCH_PLACEHOLDER(self) -> str:
        return _("Search devices, group addresses and commands…")

    def PENDING(self, count: int) -> str:
        return _.plural(
            "{count} device to program", "{count} devices to program", count
        )

    @property
    def TOGGLE_INSPECTOR(self) -> str:
        return _("Show or hide the inspector")

    @property
    def TOGGLE_BOTTOM_PANEL(self) -> str:
        return _("Show or hide the bottom panel")

    @property
    def MORE_MENUS(self) -> str:
        return _("More")

    # Group objects.
    @property
    def FILTER_ALL(self) -> str:
        return _("All")

    @property
    def FILTER_LINKED(self) -> str:
        return _("Linked")

    @property
    def FILTER_UNLINKED(self) -> str:
        return _("Unlinked")

    @property
    def FILTER_HINT(self) -> str:
        return _("Search object, function or group address…")

    def SELECTED(self, count: int) -> str:
        return _.plural("{count} object selected", "{count} objects selected", count)

    @property
    def CLEAR_SELECTION(self) -> str:
        return _("Clear Selection")

    @property
    def COL_OBJECT(self) -> str:
        return _("Object / Function")

    @property
    def COL_DATA_TYPE(self) -> str:
        return _("Data Type")

    @property
    def COL_FLAGS(self) -> str:
        return _("Flags")

    @property
    def COL_LAST_VALUE(self) -> str:
        return _("Last Value")

    def CHANNEL_OBJECTS(self, count: int) -> str:
        return _.plural("{count} object", "{count} objects", count)

    def CHANNEL_LINKED(self, count: int) -> str:
        return _.plural("{count} linked", "{count} linked", count)

    @property
    def CHANNEL_SUMMARY(self) -> str:
        return _("{objects} · {linked}")

    @property
    def WITHOUT_CHANNEL(self) -> str:
        return _("General")

    @property
    def NO_OBJECTS(self) -> str:
        return _("No objects for this filter.")

    @property
    def GROUP_OBJECT(self) -> str:
        return _("Group Object")

    @property
    def INSPECTOR_HINT(self) -> str:
        return _("Click an object to edit its details, flags and group addresses.")

    @property
    def DESCRIPTION(self) -> str:
        return _("Description")

    @property
    def NO_DESCRIPTION(self) -> str:
        return _("No description")

    @property
    def PRIORITY(self) -> str:
        return _("Priority")

    @property
    def LINK_GROUP_ADDRESS(self) -> str:
        return _("Link Group Address…")

    @property
    def NO_GROUP_ADDRESS(self) -> str:
        return _("No group address linked")

    @property
    def NO_VALUE(self) -> str:
        return _("No value yet")


S = WorkbenchStrings()
