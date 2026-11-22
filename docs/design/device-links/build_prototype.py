"""Build the Device Links prototype from a project into one offline HTML file.

    uv run python docs/design/device-links/build_prototype.py <project.xknx>

The project is only read. The result holds its device, room and group address names (no keys) and
is ignored by Git.
"""

from __future__ import annotations

import base64
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from editor_gui.device import com_object_display_name
from editor_gui.device_snapshot import decode_snapshot
from editor_gui.plugins.bus_diagram.flow import Scope, build_flow, project_hubs
from editor_gui.plugins.project.service import (
    _effective_flags,  # pyright: ignore[reportPrivateUsage] # the flags the GUI shows
)

from xknxeditor.proj.core.service import DeviceLinkInfo

HERE = Path(__file__).parent
FONTS = HERE.parents[2] / "apps/editor-gui/src/editor_gui/assets/fonts"


def ga_text(address: int) -> str:
    return f"{address >> 11}/{address >> 8 & 7}/{address & 255}"


def flag(value: int | None) -> bool | None:
    return None if value is None else bool(value)


def read_project(db: sqlite3.Connection) -> dict[str, Any]:
    objects: dict[int, Any] = {}
    for (data,) in db.execute("select data from device_snapshots"):
        if snapshot := decode_snapshot(data):
            objects.update(
                (co.db_id, co) for co in snapshot.com_objects if co.db_id is not None
            )

    links: list[DeviceLinkInfo] = []
    for device, ga, sending, c, r, w, t, u, co in db.execute(
        """select o.device_id, l.group_address_id, l.is_sending, o.communication_flag,
        o.read_flag, o.write_flag, o.transmit_flag, o.update_flag, o.id
        from com_object_links l join com_objects o on o.id = l.com_object_id order by l.id"""
    ):
        link = DeviceLinkInfo(
            device_id=device,
            group_address_id=ga,
            is_sending=bool(sending),
            communication=flag(c),
            read=flag(r),
            write=flag(w),
            transmit=flag(t),
            update=flag(u),
            com_object_id=co,
        )
        known = objects.get(co)
        links.append(_effective_flags(link, known.flags if known else None))

    addresses = [
        SimpleNamespace(id=i, address=ga_text(address), name=name)
        for i, address, name in db.execute(
            "select id, address, name from group_addresses order by address"
        )
    ]
    project = SimpleNamespace(device_links=lambda: links, group_addresses=addresses)
    hubs = project_hubs(cast(Any, project))

    segments = {
        i: f"{area}.{line}"
        for i, area, line in db.execute(
            """select s.id, a.address, l.address from segments s
            join lines l on l.id = s.line_id join areas a on a.id = l.area_id"""
        )
    }
    devices: list[dict[str, Any]] = [
        {
            "id": i,
            "ia": f"{segments[segment]}.{address}"
            if segment in segments and address is not None
            else "",
            "name": name or product,
            "product": product,
            "space": space,
        }
        for i, segment, address, name, product, space in db.execute(
            """select id, segment_id, address, name, product_name, space_id
            from devices order by segment_id, address"""
        )
    ]
    spaces = [
        {"id": i, "parent": parent, "type": kind, "name": name}
        for i, parent, kind, name in db.execute(
            'select id, parent_id, space_type, name from spaces order by "order", id'
        )
    ]
    groups = {
        (
            str(start >> 11) if parent is None else f"{start >> 11}/{start >> 8 & 7}"
        ): name
        for start, parent, name in db.execute(
            "select range_start, parent_id, name from group_ranges"
        )
    }
    members = {hub.ga_id: hub.members for hub in hubs}
    used = {co for hub in hubs for m in hub.members for co, _s, _r in m.objects}

    # Today's Links view, for comparison.
    labels = {d["id"]: f"{d['ia']} {d['name']}" for d in devices}
    today = build_flow(hubs, Scope("all"), {}, labels, groups)
    at = {node.key: (node.column, node.y) for node in today.nodes}

    return {
        "devices": devices,
        "spaces": spaces,
        "groups": groups,
        "gas": [
            [
                ga.id,
                ga.address,
                ga.name,
                [
                    [m.node_id, [[co, int(s), int(r)] for co, s, r in m.objects]]
                    for m in members.get(ga.id, ())
                ],
            ]
            for ga in addresses
        ],
        "objects": {
            co: [objects[co].number, com_object_display_name(objects[co])]
            if co in objects
            else [0, "?"]
            for co in sorted(used)
        },
        "today": {
            "height": today.height,
            "nodes": [
                [n.column, n.y, n.label or f"{n.address} {n.name}"] for n in today.nodes
            ],
            "edges": [[*at[a], *at[b]] for a, b, _main in today.edges],
        },
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    source = Path(sys.argv[1]).resolve()
    db = sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)
    data = read_project(db)
    db.close()
    data["title"] = source.stem
    # "<" escaped: a name in the project must not be able to end the script element.
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    fonts = ""
    for family, file, weight in (
        ("XKNX Sans", "XKNXSans-Regular.ttf", 400),
        ("XKNX Sans", "XKNXSans-Bold.ttf", 700),
        ("Inconsolata", "Inconsolata-Medium.ttf", 500),
    ):
        encoded = base64.b64encode((FONTS / file).read_bytes()).decode()
        fonts += (
            f'@font-face{{font-family:"{family}";font-weight:{weight};'
            f'src:url(data:font/ttf;base64,{encoded}) format("truetype")}}\n'
        )
    template = (HERE / "prototype.html").read_text(encoding="utf-8")
    html = template.replace("/*FONTS*/", fonts).replace("/*DATA*/null", text)
    target = HERE / "Entwurf.local.html"
    target.write_text(html, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
