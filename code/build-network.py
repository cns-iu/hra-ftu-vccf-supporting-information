import csv
import re
from dataclasses import dataclass

import networkx as nx
import requests

ASCTB_DATA = "https://cdn.humanatlas.io/hra-asctb-json-releases/hra-asctb-all.v2.1.json"
data = requests.get(ASCTB_DATA).json()


def get_temp_code(str):
    str = str.strip()
    str = str.lower()
    str = re.sub('\\W+', '-', str)
    str = re.sub('[^a-z0-9-]+', '', str)
    return f'ASCTB-TEMP:{str}'


def get_id(item):
    if item['id'].strip() == "":
        return get_temp_code(item['name'])
    else:
        return item['id']


def get_label(item):
    if item['rdfs_label'].strip() == "":
        return item['name'].strip()
    else:
        return item['rdfs_label'].strip()


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
    return Item(id, label, type, organ, id)


BODY = [Item('UBERON:0013702', 'body', 'AS', 'body', 'UBERON:0013702')]

skip_organs = set(['bonemarrow-pelvis', 'blood-vasculature', 'anatomical-systems'])
tables = list(sorted(filter(lambda x: x not in skip_organs, data.keys())))
paths = []
for table in tables:
    rows = data[table]
    organ = table.replace('-', '_')
    for row in rows['data']:
        as_path = [get_item(item, organ, 'AS')
                   for item in row['anatomical_structures']]
        ct_path = [get_item(item, organ, 'CT')
                   for item in row['cell_types']]
        paths.append({
            'as': BODY + as_path,
            'ct': ct_path
        })


tree = nx.DiGraph()


def add_node(tree, item):
    tree.add_node(item.id, id=item.id, name=item.name, type=item.type, organ=item.organ,
                  ontology_id=item.ontology_id)


dup = 0
for path in paths:
    as_path = path['as'] + path['ct']
    for src in range(len(as_path) - 1):
        source, target = as_path[src], as_path[src + 1]
        if not tree.has_edge(source.id, target.id):
            if not tree.has_node(source.id):
                add_node(tree, source)
            # target is in the graph, but not connected to this source node
            elif tree.has_node(target.id):
                dup += 1
                target.id = f"{target.id}$${dup}"

            if not tree.has_node(target.id):
                add_node(tree, target)

            tree.add_edge(source.id, target.id, organ=target.organ, source=source.id,
                          target=target.id, source_type=source.type, target_type=target.type)

print('is tree?', nx.is_tree(tree))
nx.write_graphml_lxml(tree, 'data/asct-tree.graphml')
nx.nx_agraph.write_dot(tree, 'data/asct-tree.dot')


with open('data/asct-nodes.csv', 'w', newline='') as csvfile:
    header = ['id', 'name', 'type', 'organ', 'ontology_id']
    writer = csv.DictWriter(csvfile, fieldnames=header)

    writer.writeheader()
    for id, data in tree.nodes.items():
        writer.writerow(data)

with open('data/asct-edges.csv', 'w', newline='') as csvfile:
    header = ['organ', 'source', 'target', 'source_type', 'target_type']
    writer = csv.DictWriter(csvfile, fieldnames=header)

    writer.writeheader()
    for id, data in tree.edges.items():
        writer.writerow(data)
