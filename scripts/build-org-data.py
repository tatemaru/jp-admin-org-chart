#!/usr/bin/env python3
"""Build docs/viewer/data/*.json from Mermaid org charts at each git tag."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "viewer" / "data"

NODE_RE = re.compile(r'([A-Za-z_][\w]*)\s*\[\s*"([^"]+)"\s*\]')
EDGE_RE = re.compile(r"([A-Za-z_][\w]*)\s*-->\s*([A-Za-z_][\w]*)")
SUB_START = re.compile(r'subgraph\s+([A-Za-z_][\w]*)\s*\[\s*"([^"]+)"\s*\]')

ERA_LABELS = {
    "era/dajokan": "時代: 太政官制",
    "era/cabinet": "時代: 内閣制度",
    "era/empire": "時代: 帝国議会",
    "era/postwar": "時代: 日本国憲法",
    "era/heisei-pre-reorg": "時代: 再編直前（1府22）",
    "era/heisei-reorg": "時代: 中央省庁再編以降",
    "era/reiwa-detail": "時代: デジタル庁以降",
    "era/current": "最新（HEAD）",
}


def git(*args: str, binary: bool = False):
    return subprocess.check_output(["git", *args], cwd=REPO, text=not binary)


def list_tags() -> list[str]:
    tags = git("tag", "-l", "point/*", "era/*", "snapshot/*").splitlines()

    def key(t: str):
        if t.startswith("era/"):
            order = [
                "dajokan",
                "cabinet",
                "empire",
                "postwar",
                "heisei-pre-reorg",
                "heisei-reorg",
                "reiwa-detail",
                "current",
            ]
            name = t.split("/", 1)[1]
            return (0, order.index(name) if name in order else 99, t)
        if t.startswith("point/"):
            return (1, t)
        return (2, t)

    return sorted(tags, key=key)


def list_readme_paths(tag: str) -> list[str]:
    raw = git("ls-tree", "-r", "-z", "--name-only", tag, binary=True)
    paths = [p.decode("utf-8") for p in raw.split(b"\0") if p]
    return [
        f
        for f in paths
        if f == "README.md"
        or (
            f.endswith("/README.md")
            and (f.startswith("行政機構/") or f.startswith("付録/"))
        )
    ]


def extract_mermaid_blocks(md: str) -> list[str]:
    return re.findall(r"```mermaid\n(.*?)```", md, flags=re.S)


def parse_flowchart(src: str):
    nodes: dict[str, str] = {}
    edges: list[tuple[str, str]] = []
    subgraphs: dict[str, dict] = {}
    current_sub = None
    for raw in src.splitlines():
        line = raw.strip()
        if not line or line.startswith("flowchart") or line.startswith("graph"):
            continue
        if line == "end":
            current_sub = None
            continue
        m = SUB_START.search(line)
        if m:
            current_sub = m.group(1)
            subgraphs[current_sub] = {"title": m.group(2), "members": []}
            continue
        for m in NODE_RE.finditer(line):
            nid, label = m.group(1), m.group(2).replace("\\n", " / ")
            nodes[nid] = label
            if current_sub and nid != current_sub:
                subgraphs[current_sub]["members"].append(nid)
        for m in EDGE_RE.finditer(line):
            edges.append((m.group(1), m.group(2)))
    return nodes, edges, subgraphs


def expand_edges(nodes, edges, subgraphs):
    out: list[tuple[str, str]] = []
    for a, b in edges:
        if b in subgraphs:
            for mem in subgraphs[b]["members"]:
                out.append((a, mem))
        elif a in nodes and b in nodes:
            out.append((a, b))
    return [(a, b) for a, b in out if a in nodes and b in nodes and a not in subgraphs]


def build_tree_for_tag(tag: str) -> dict:
    interesting = list_readme_paths(tag)
    all_nodes: dict[str, dict] = {}
    label_index: dict[str, str] = {}

    def add_chart(path: str, md: str, attach_under: str | None = None):
        for bi, block in enumerate(extract_mermaid_blocks(md)):
            nodes, edges, subgraphs = parse_flowchart(block)
            edges = expand_edges(nodes, edges, subgraphs)
            prefix = f"{path}#{bi}:"
            local_to_uid = {nid: prefix + nid for nid in nodes}
            for nid, label in nodes.items():
                uid = local_to_uid[nid]
                all_nodes[uid] = {
                    "id": uid,
                    "parentId": None,
                    "name": label,
                    "source": path,
                }
            for a, b in edges:
                if a in local_to_uid and b in local_to_uid:
                    all_nodes[local_to_uid[b]]["parentId"] = local_to_uid[a]

            if attach_under:
                for nid, label in list(nodes.items()):
                    uid = local_to_uid[nid]
                    if uid not in all_nodes:
                        continue
                    if all_nodes[uid]["parentId"] is not None:
                        continue
                    if label in label_index and label_index[label] != uid:
                        target = label_index[label]
                        for other in all_nodes.values():
                            if other["parentId"] == uid:
                                other["parentId"] = target
                        del all_nodes[uid]
                    else:
                        all_nodes[uid]["parentId"] = attach_under
                        label_index[label] = uid
            else:
                # Index every label so detail charts can attach under overview nodes.
                for nid, label in nodes.items():
                    label_index.setdefault(label, local_to_uid[nid])

    root_id = "__root__"
    all_nodes[root_id] = {
        "id": root_id,
        "parentId": None,
        "name": "国家行政機構",
        "source": "",
    }

    if "README.md" in interesting:
        md = git("show", f"{tag}:README.md")
        add_chart("README.md", md)
        for n in list(all_nodes.values()):
            if n["id"] != root_id and n["parentId"] is None:
                n["parentId"] = root_id
            if n["id"] != root_id:
                label_index.setdefault(n["name"], n["id"])

    for path in interesting:
        if path == "README.md":
            continue
        md = git("show", f"{tag}:{path}")
        m = re.search(r"^#\s+(.+)$", md, re.M)
        title = m.group(1).strip() if m else Path(path).parent.name
        parent = label_index.get(title)
        if parent is None:
            uid = f"missing:{title}"
            all_nodes[uid] = {
                "id": uid,
                "parentId": root_id,
                "name": title,
                "source": path,
            }
            label_index[title] = uid
            parent = uid
        add_chart(path, md, attach_under=parent)

    by_id = {n["id"]: n for n in all_nodes.values()}
    for n in all_nodes.values():
        if n["parentId"] and n["parentId"] not in by_id:
            n["parentId"] = root_id

    subject = git("log", "-1", "--format=%s", tag).strip()
    body = git("log", "-1", "--format=%B", tag)
    when = ""
    m = re.search(r"施行:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}[^\n]*)", body)
    if m:
        when = m.group(1).strip()
    elif tag.startswith("point/"):
        when = tag.split("/")[1][:10]
    elif tag.startswith("snapshot/"):
        when = tag.split("/")[1]

    label = ERA_LABELS.get(tag)
    if not label:
        if tag.startswith("point/"):
            label = f"{when or tag} — {subject}"
        elif tag.startswith("snapshot/"):
            label = f"年次snapshot {tag.split('/', 1)[1]} — {subject}"
        else:
            label = f"{tag} — {subject}"

    return {
        "tag": tag,
        "label": label,
        "subject": subject,
        "when": when,
        "nodes": [
            {"id": n["id"], "parentId": n["parentId"], "name": n["name"]}
            for n in all_nodes.values()
        ],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for tag in list_tags():
        data = build_tree_for_tag(tag)
        safe = tag.replace("/", "__")
        (OUT / f"{safe}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append(
            {
                "tag": tag,
                "file": f"{safe}.json",
                "label": data["label"],
                "when": data.get("when", ""),
                "subject": data.get("subject", ""),
                "nodeCount": len(data["nodes"]),
            }
        )
        print(f"{tag}: {len(data['nodes'])} nodes")
    (OUT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(index)} tag datasets to {OUT}")


if __name__ == "__main__":
    main()
