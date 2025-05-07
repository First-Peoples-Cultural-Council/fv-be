# This file prepares the complete dependency tree and take cyclonedx CBOM as input
# Python transitive dependencies will appear flat on this trees as it is computed during installation
# Python dependency tree should be prepared using pipdeptree
import json
import sys
from collections import defaultdict


def parse_sbom(filename):
    with open(filename) as f:
        sbom = json.load(f)

    # Map component ref -> name@version
    ref_to_name = {}
    for c in sbom.get("components", []):
        name = c.get("name")
        version = c.get("version", "")
        purl = c.get("purl", "")
        ref = purl or f"{name}@{version}"
        ref_to_name[ref] = f"{name}=={version}"

    # Build dependency graph
    graph = defaultdict(list)
    all_refs = set()
    dep_refs = set()

    for dep_entry in sbom.get("dependencies", []):
        ref = dep_entry.get("ref")
        all_refs.add(ref)
        for child in dep_entry.get("dependsOn", []):
            graph[ref].append(child)
            dep_refs.add(child)

    # Root components = ones not depended on by others
    roots = all_refs - dep_refs

    return graph, ref_to_name, roots


def print_tree(graph, ref_to_name, current_ref, visited=None, prefix="", is_last=True):
    if visited is None:
        visited = set()
    if current_ref in visited:
        print(
            prefix
            + ("└── " if is_last else "├── ")
            + ref_to_name.get(current_ref, current_ref)
            + " (circular)"
        )
        return
    visited.add(current_ref)

    connector = "└── " if is_last else "├── "
    print(prefix + connector + ref_to_name.get(current_ref, current_ref))

    children = graph.get(current_ref, [])
    for i, dep_ref in enumerate(children):
        last = i == len(children) - 1
        new_prefix = prefix + ("    " if is_last else "│   ")
        print_tree(graph, ref_to_name, dep_ref, visited.copy(), new_prefix, last)


def main():
    if len(sys.argv) != 2:
        print("Usage: Only cyclonedx bom.json")
        sys.exit(1)

    filename = sys.argv[1]
    graph, ref_to_name, roots = parse_sbom(filename)

    if not roots:
        print(
            "No root components found. Your CBOM may be missing the 'dependencies' section."
        )
        sys.exit(1)

    for root in sorted(roots):
        print_tree(graph, ref_to_name, root)
        print()


if __name__ == "__main__":
    main()
