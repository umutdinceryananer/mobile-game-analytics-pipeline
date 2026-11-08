"""Write a Mermaid lineage diagram of the dbt project into README.md.

Reads dbt/target/manifest.json and replaces the text between the lineage markers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "dbt" / "target" / "manifest.json"
README_PATH = REPO_ROOT / "README.md"
START_MARKER = "<!-- dbt-lineage:start -->"
END_MARKER = "<!-- dbt-lineage:end -->"
LAYERS = ["sources", "staging", "intermediate", "marts"]


def _node_id(unique_id: str) -> str:
    return unique_id.replace(".", "_")


def build_diagram(manifest: dict) -> str:
    """Return a Mermaid flowchart of the sources and models in the manifest."""
    nodes_by_layer: dict[str, list[str]] = {layer: [] for layer in LAYERS}
    edges: list[str] = []

    for unique_id, source in sorted(manifest["sources"].items()):
        label = f"{source['source_name']}.{source['name']}"
        nodes_by_layer["sources"].append(f'{_node_id(unique_id)}[("{label}")]')

    for unique_id, node in sorted(manifest["nodes"].items()):
        if node["resource_type"] != "model":
            continue
        layer = node["fqn"][1]
        nodes_by_layer[layer].append(f'{_node_id(unique_id)}["{node["name"]}"]')
        for parent in node["depends_on"]["nodes"]:
            edges.append(f"    {_node_id(parent)} --> {_node_id(unique_id)}")

    lines = ["```mermaid", "flowchart LR"]
    for layer in LAYERS:
        lines.append(f"    subgraph {layer}")
        lines.extend(f"        {node}" for node in nodes_by_layer[layer])
        lines.append("    end")
    lines.extend(sorted(edges))
    lines.append("```")
    return "\n".join(lines)


def update_readme(readme: str, diagram: str) -> str:
    """Return the README text with the diagram placed between the markers."""
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL
    )
    if not pattern.search(readme):
        raise ValueError(f"Lineage markers not found in {README_PATH}")
    replacement = f"{START_MARKER}\n{diagram}\n{END_MARKER}"
    return pattern.sub(lambda _: replacement, readme)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    readme = README_PATH.read_text(encoding="utf-8")
    README_PATH.write_text(update_readme(readme, build_diagram(manifest)), "utf-8")
    print(f"Lineage diagram written to {README_PATH}")


if __name__ == "__main__":
    main()
