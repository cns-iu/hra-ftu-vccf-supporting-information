import csv
import re
from dataclasses import dataclass

import networkx as nx
import requests

# Include cell types in the graph?
INCLUDE_CELL_TYPES = True

# Make sure nodes are unique to each table?
FACET_BY_TABLE = False

ASCTB_DATA = "https://cdn.humanatlas.io/hra-asctb-json-releases/hra-asctb-all.v2.1.json"
data = requests.get(ASCTB_DATA).json()


def get_temp_code(str):
    str = str.strip()
    str = str.lower()
    str = re.sub("\\W+", "-", str)
    str = re.sub("[^a-z0-9-]+", "", str)
    return f"ASCTB-TEMP:{str}"


def get_id(item):
    if item["id"].strip() == "":
        return get_temp_code(item["name"])
    else:
        return item["id"]


def get_label(item):
    if item["rdfs_label"].strip() == "":
        return item["name"].strip()
    else:
        return item["rdfs_label"].strip()


@dataclass
class Item:
    id: str
    name: str
    type: str
    organ: str
    ontology_id: str


def get_item(item, organ, type):
    id = get_id(item)
    label = get_label(item)
    if FACET_BY_TABLE:
        node_id = f"{id}_{organ}_{type}"
    else:
        node_id = id
    return Item(node_id, label, type, organ, id)


BODY = Item("UBERON:0013702", "body", "AS", "body", "UBERON:0013702")
SYSTEMS = [
    "anatomical-systems",
    "blood-vasculature",
    "lymph-vasculature",
    "peripheral-nervous-system",
    "muscular-system",
    "skeleton",
]

skip_organs = set(["bonemarrow-pelvis"] + SYSTEMS)
tables = SYSTEMS + list(sorted(filter(lambda x: x not in skip_organs, data.keys())))
paths = []
for table in tables:
    rows = data[table]
    organ = table.replace("-", "_")
    for row in rows["data"]:
        as_path = [get_item(item, organ, "AS") for item in row["anatomical_structures"]]
        ct_path = [get_item(item, organ, "CT") for item in row["cell_types"]]
        paths.append({"as": as_path, "ct": ct_path})


tree = nx.DiGraph()


def add_node(tree, item):
    tree.add_node(
        item.id,
        id=item.id,
        label=item.name,
        name=item.name,
        type=item.type,
        organ=item.organ,
        ontology_id=item.ontology_id,
    )


def add_edge(tree, source, target):
    tree.add_edge(
        source.id,
        target.id,
        organ=target.organ,
        source=source.id,
        target=target.id,
        source_type=source.type,
        target_type=target.type,
    )


add_node(tree, BODY)
dup = 0
for path in paths:
    if INCLUDE_CELL_TYPES:
        as_path = path["as"] + path["ct"]
    else:
        as_path = path["as"]
    if not tree.has_node(as_path[0].id):
        add_node(tree, as_path[0])
        add_edge(tree, BODY, as_path[0])

    for src in range(len(as_path) - 1):
        source, target = as_path[src], as_path[src + 1]
        if source.id != target.id and not tree.has_edge(source.id, target.id):
            if not tree.has_node(source.id):
                add_node(tree, source)
            else:  # source node exists
                found_child = None
                for child in tree.successors(source.id):
                    if tree.nodes[child]["ontology_id"] == target.ontology_id:
                        target.id = child
                        found_child = True

                # target node is in the graph, but not connected to this source node
                if not found_child and tree.has_node(target.id):
                    dup += 1
                    target.id = f"{target.id}$${dup}"

            if not tree.has_node(target.id):
                add_node(tree, target)

            add_edge(tree, source, target)

print("is tree?", nx.is_tree(tree))
print("has cycles?", nx.algorithms.dag.has_cycle(tree))
print("duplicated nodes:", dup)
nx.write_graphml_lxml(tree, "data/asct-tree.graphml")
nx.nx_agraph.write_dot(tree, "data/asct-tree.dot")
nx.nx_agraph.to_agraph(tree).draw("data/asct-tree.svg", prog="dot")

with open("data/asct-nodes.csv", "w", newline="") as csvfile:
    header = ["id", "name", "type", "organ", "ontology_id"]
    writer = csv.writer(csvfile)

    writer.writerow(header)
    for id, data in tree.nodes.items():
        writer.writerow([data[col] for col in header])

with open("data/asct-edges.csv", "w", newline="") as csvfile:
    header = ["organ", "source", "target", "source_type", "target_type"]
    writer = csv.writer(csvfile)

    writer.writerow(header)
    for id, data in tree.edges.items():
        writer.writerow([data[col] for col in header])
