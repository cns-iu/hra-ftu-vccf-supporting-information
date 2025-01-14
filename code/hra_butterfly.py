import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import json
import argparse

import vl_convert as vlc
from datashader.bundling import hammer_bundle
import svgutils.transform as st

VERSION = "v2.2"
# Directory for butterfly outputs
OUTPUT_DIR= './viz_' + VERSION

# URLs for the data
nodes_url = "./data/asct-nodes.csv" 
edges_url = "./data/asct-edges.csv"
blood_edges_url = "./data/asct-blood-vasculature-edges.csv"

dirname = "GeeksForGeeks"
if os.path.isdir(OUTPUT_DIR):
    pass
else:
    os.mkdir(OUTPUT_DIR)

# Load the data
nodes = pd.read_csv(nodes_url)
edges = pd.read_csv(edges_url)

# Filter out the organs that are not in the butterfly
omitted_organs = ['muscular_system', 'skeleton'] + ['lymph_vasculature', 'peripheral_nervous_system', 'blood_pelvis',] 

nodes = nodes[~nodes['organ'].isin(omitted_organs)]
edges = edges[~edges['organ'].isin(omitted_organs)]



# Order of organs in the butterfly
organ_order = ['trachea', 'main bronchus', 'respiratory system', 'heart',  'spinal cord', 'brain', 'eye', 'palatine tonsil', 
               'skin of body', 'thymus', 'lymph node', 'spleen',  'liver', 'Pancreas', 'small intestine',  'large intestine', 
               'kidney', 'urinary bladder', 'ureter', 'prostate gland',  'ovary', 'fallopian tube', 'uterus',  
               'placenta', 'knee', 'Bone marrow']



# There are some anatomical structures that belong to the respiratory system but are connected to the 'body' node
# Here we connect these nodes to the respiratory system node and remove the link to the body node
new_edges = edges[(edges['source']=='UBERON:0013702')&(edges['target'].isin(['UBERON:0008886', 'UBERON:0004573', 'UBERON:0003920']))].copy()
new_edges['source'].replace('UBERON:0013702', 'UBERON:0001004', inplace=True) #connect the nodes to respiratory system instead of body

edges = edges[~((edges['source']=='UBERON:0013702')&(edges['target'].isin(['UBERON:0008886', 'UBERON:0004573', 'UBERON:0003920'])))]
edges = pd.concat([edges, new_edges])


# Create a graph
whole_graph = nx.from_pandas_edgelist(edges, source='source', target='target', edge_attr=True)

print(f"The graph is a tree: {nx.is_tree(whole_graph)}")



# Query the nodes
def get_nodes(name=None, ontology_id=None):
    if name:
        return nodes[nodes['name'].str.lower()==name.lower()]
    if ontology_id:
        return nodes[nodes['ontology_id']==ontology_id]   
    

organ_order_in_id = [get_nodes(name=organ)['id'].values[0] for organ in organ_order]

# Get the graph of the organ 
def get_organ_graph(organ_id):
    organ_graph = whole_graph.copy()
    organ_graph.remove_edge('UBERON:0013702', organ_id) #remove the edge between body and the organ

    connected_components = sorted(list(nx.connected_components(organ_graph)), key=len, reverse=False) #get the connected components

    return nx.subgraph(organ_graph, connected_components[0]) #return the smallest connected component



# Generate a new integer-based ID, that takes into account the organ order
## (This is necesary for the layout, later we can order the nodes and edges based on this integer ID, 
## and then vega will visualize the organs in the desired order)

id_to_graph_int_id = {'UBERON:0013702': 0}

next_id = 1

for i, organ_id in enumerate(organ_order_in_id):
    branch_graph = get_organ_graph(organ_id)

    branch_graph_new_ids = dict(zip(nx.dfs_preorder_nodes(branch_graph, source=organ_id), range(next_id, next_id+branch_graph.number_of_nodes())))

    id_to_graph_int_id.update(branch_graph_new_ids)

    next_id += branch_graph.number_of_nodes()


nodes['graph_int_id'] = nodes['id'].map(id_to_graph_int_id)

edges['source_int'] = edges['source'].map(id_to_graph_int_id)
edges['target_int'] = edges['target'].map(id_to_graph_int_id)


# Create the graph with the new integer IDs
whole_graph_int = nx.from_pandas_edgelist(edges, source='source_int', target='target_int', edge_attr=True)

graph_int_id_to_id = {v: k for k, v in id_to_graph_int_id.items()} #reverse the dictionary


# Removal of the blood vasculature nodes from the whole (partonomy) graph
## We only keep those that are necessary to keep the network connected

# remove those blood nodes from the graph, which if we remove, the graph will be still connected, repeat until no such node is found.
blood_nodes_candidates = set(nodes[nodes['organ']=='blood_vasculature'].graph_int_id.tolist())

distance_from_body = nx.single_source_shortest_path_length(whole_graph_int, source=0)

distance_from_body_blood_nodes = {k: v for k, v in distance_from_body.items() if k in blood_nodes_candidates}

node_visiting_order = sorted(distance_from_body_blood_nodes.items(), key=lambda x: x[1], reverse=True)

new_pruned_graph = whole_graph_int.copy()

for node in node_visiting_order:
    new_pruned_graph.remove_node(node[0])
    if nx.is_connected(new_pruned_graph):
        blood_nodes_candidates.remove(node[0])
    else:
        break

nodes['keep'] = nodes.apply(lambda row: True if (row['organ']!='blood_vasculature' or row['graph_int_id'] in blood_nodes_candidates) else False, axis=1)

#TODO: rename it to pruned_graph and pruned_nodes, and pruned_edges
pruned_nodes = nodes[nodes['keep']]
pruned_edges = edges[edges['source_int'].isin(pruned_nodes['graph_int_id']) | edges['target_int'].isin(pruned_nodes['graph_int_id'])]
pruned_graph = nx.from_pandas_edgelist(pruned_edges, source='source_int', target='target_int', edge_attr=True)



FTUs = ['UBERON:0001285', 'UBERON:0001229', 'UBERON:0004205', 'UBERON:0001289', 'UBERON:0004193', 'UBERON:0004204', 'UBERON:0001291', 'UBERON:0004203', #kidney
        'UBERON:0001983',  'UBERON:0001984',  #large intestine
        'UBERON:0004647', #liver
        'UBERON:0002299', 'UBERON:8410043', #lung 
        'UBERON:0000006', 'UBERON:0001263', 'UBERON:0014726', #pancreas
        'UBERON:0004179', #prostate gland
        'UBERON:0000412', 'UBERON:0013487', 'UBERON:0001992', #skin
        'UBERON:0001213', #small intestine
        'UBERON:0001250', 'UBERON:0001959', #spleen
        'UBERON:0002125' 
        ]




def construct_network_create_vega_viz(nodes_dataframe, edges_dataframe, filename='butterfly', only_female=False, only_male=False, scenegraph=False, show_labels=False):
    '''
    Construct the network and create the vega visualization file, which is a JSON file. 
    Vega will visualize the network based on the config file. Using the API we can create the SVG and the "scenegraph" which will be used for the coordinates of the nodes.

    Parameters:
    nodes_dataframe: pd.DataFrame
        The dataframe containing the nodes of the network. It should have the following columns: 'id', 'name', 'type', 'organ', 'ontology_id', 'graph_int_id'.
    edges_dataframe: pd.DataFrame
        The dataframe containing the edges of the network. It should have the following columns: 'source_int', 'target_int', 'organ'.
    filename: str
        The name of the file to be saved
    only_female: bool
        If True, the visualization will not contain the prostate (so far that's the only male organ).
    only_male: bool
        If True, the visualization will not contain the ovaries, fallopian tube, uterus, placenta (so far these are the female organs).
    scenegraph: bool
        If True, the name of the nodes will be the id of the nodes. This is necessary to later get the coordinates of the nodes based on the IDs.
    show_labels: bool
        If True, the labels of the nodes will be shown (in the SVG file).
    '''

    nodes_df = nodes_dataframe.sort_values('graph_int_id').copy() 
    edges_df = edges_dataframe.sort_values('target_int').copy() #sorting is necessary for the order of the branches in the visualization

    # create the graph
    graph = nx.from_pandas_edgelist(edges_df, source='source_int', target='target_int', edge_attr=True)

    # get the parent of each node for the tree layout
    parents_dict = dict(nx.bfs_predecessors(graph, source=0))

    nodes_df['parent'] = nodes_df['graph_int_id'].map(parents_dict).fillna(0).astype(int)

    # set the color of the nodes based on the type
    nodes_df['color'] = nodes_df.apply(lambda row: '#56a04e' if row['ontology_id'] in FTUs else ('#984ea0' if row['type']=='AS' else '#ff7f00'), axis=1)


    # vega works with the id column, so we rename the id column to id_from_ontology_id
    nodes_df.rename(columns={'id': 'id_from_ontology_id', 'graph_int_id': 'id'}, inplace=True)
    

    if scenegraph:
        # the name has to be the id
        nodes_df.rename(columns={'name': 'name_label'}, inplace=True)
        nodes_df['name'] = nodes_df['id'].copy()


    # if the name is missing, we fill it with an empty string because vega gives an error if it is missing
    nodes_df['name'] = nodes_df['name'].fillna('')



    # from the female wing we remove the prostate
    if only_female and not only_male:
        nodes_df = nodes_df[nodes_df['organ']!='prostate']
        fn = filename + '_female'

    # from the male wing we remove the ovaries, fallopian tube, uterus, placenta
    elif only_male and not only_female:
        nodes_df = nodes_df[~nodes_df['organ'].isin(['fallopian_tube', 'ovary', 'uterus', 'placenta'])]
        fn = filename + '_male'

    elif not only_female and not only_male:
        fn = filename + '_full'

    else:
        raise ValueError('The parameters `only_female` and `only_male` cannot be both True at the same time.')

    # print(nodes_df['organ'].value_counts())

    # create the json file for the nodes
    nodes_json = nodes_df[['id', 'name', 'parent', 'type', 'ontology_id', 
                           'id_from_ontology_id', 'color', 'organ', #'organ_label'
                           ]].to_dict(orient='index')

    # the body does not have a parent, so we delete its value
    del(nodes_json[0]['parent'])

    # we need to convert the dictionary to a list, that's how the vega visualization expects it at the config['data'][0]['values']
    nodes_json = [nodes_json[i] for i in nodes_json.keys()]
    
    # load the vega config file
    with open('vega_config.json', encoding='utf8') as json_file:
        config = json.load(json_file)

    # set the data in the config file
    config['data'][0]['values'] = nodes_json
    
    # show labels if show_labels is True
    if show_labels:
        config['marks'][-1]['encode']['update']['opacity']['signal'] = config['marks'][-1]['encode']['update']['opacity']['signal'][:-1] + '1' # show the labels, by default they are hidden
    
    # create the json file and save it
    with open(f"{OUTPUT_DIR}/{fn}_vega_viz_config.json", "w") as outfile:
        outfile.write(json.dumps(config, indent=4))
        print(f'File saved as "{OUTPUT_DIR}/{fn}_vega_viz.json"')
    
    return config



vega_config = construct_network_create_vega_viz(pruned_nodes, pruned_edges, scenegraph=True)



vega_config_female_with_names = construct_network_create_vega_viz(pruned_nodes, pruned_edges, 
                                                                  only_female=True, scenegraph=False, 
                                                                  show_labels=True, filename='butterfly_names') #name shown - this one is not used just for manual checking with human readable names

vega_config_female_with_ids = construct_network_create_vega_viz(pruned_nodes, pruned_edges, 
                                                                only_female=True, scenegraph=True, 
                                                                show_labels=True, filename='butterfly_ids') #id shown - this is used for the coordinates 

vega_config_female = construct_network_create_vega_viz(pruned_nodes, pruned_edges, 
                                                       only_female=True, scenegraph=True, 
                                                       show_labels=False) #no name or id shown, based on id (scenegraph) - this is used for the viz


vega_config_male = construct_network_create_vega_viz(pruned_nodes, pruned_edges, 
                                                     only_male=True, scenegraph=True)

vega_config_male_with_ids = construct_network_create_vega_viz(pruned_nodes, pruned_edges, 
                                                              only_male=True, scenegraph=True, show_labels=True, 
                                                              filename='butterfly_ids') #id shown - this is used for the coordinates 



def create_vega_viz(config, filename, scenegraph=False):
    '''
    Create the visualization based on the vega config file. The visualization can be saved as SVG or as a scenegraph JSON file.

    Parameters:
    config: dict
        The vega config file.
    filename: str
        The name of the file to be saved.
    scenegraph: bool
        If True, the scenegraph JSON file will be saved, otherwise the SVG file will be saved.
    '''

    if scenegraph:
        scenegraph_data = vlc.vega_to_scenegraph(vg_spec=config)

        with open(f"{OUTPUT_DIR}/vega_{filename}_scenegraph.json", "w") as outfile:
            outfile.write(json.dumps(scenegraph_data, indent=4))

        return scenegraph_data
    
    else:
        svg_str = vlc.vega_to_svg(vg_spec=config,)

        with open(f"{OUTPUT_DIR}/vega_{filename}_viz.svg", "wt") as f:
            f.write(svg_str)

        return svg_str
    


# Create the vega viz of the female wing
female_svg = create_vega_viz(vega_config_female, 'female', scenegraph=False)

# Create the vega viz of the male wing
male_svg = create_vega_viz(vega_config_male, 'male', scenegraph=False)


# Get the scenegraphs for the coordinates
scenegraph_female = create_vega_viz(vega_config_female_with_ids, 'female_id', scenegraph=True)
scenegraph_male = create_vega_viz(vega_config_male_with_ids, 'male_id', scenegraph=True)


def get_node_coordinates(scenegraph):
    return {item['text']: (item['x'], item['y']) for item in scenegraph['scenegraph']['items'][0]['items'][2]['items']}


coordinates_of_nodes_fem = get_node_coordinates(scenegraph_female)
coordinates_of_nodes_mal = get_node_coordinates(scenegraph_male)


#######################################################################################################################
#######################################################################################################################

# Vascular network

blood_edges = pd.read_csv(blood_edges_url)

blood_graph = nx.from_pandas_edgelist(blood_edges, source='source', target='target', edge_attr=True,)# create_using=nx.DiGraph)

blood_nodes = nodes[nodes['id'].isin(blood_graph.nodes)]

blood_nodes['graph_int_id'] = blood_nodes['id'].map(id_to_graph_int_id)

blood_edges['source_int'] = blood_edges['source'].map(id_to_graph_int_id)
blood_edges['target_int'] = blood_edges['target'].map(id_to_graph_int_id)


blood_graph_int = nx.from_pandas_edgelist(blood_edges, source='source_int', target='target_int', edge_attr=True)


id_of_heart = blood_nodes[blood_nodes['name']=='heart']['graph_int_id'].values[0]

blood_nodes[blood_nodes['graph_int_id'].isin(list(nx.neighbors(blood_graph_int, id_of_heart)))]


components = blood_graph_int.copy()
components.remove_node(id_of_heart)
components = list(nx.connected_components(components))

components += [set([id_of_heart])]


id_of_left_ventricle_and_left_atrium = blood_nodes[blood_nodes['name'].apply(lambda x: 'left cardiac atrium' in str(x).lower() or 'left ventricle' in str(x).lower())]['graph_int_id'].tolist()

id_of_right_ventricle_and_right_atrium = blood_nodes[blood_nodes['name'].apply(lambda x: 'right cardiac atrium' in str(x).lower() or 'right ventricle' in str(x).lower())]['graph_int_id'].tolist()


blood_nodes['artery/vein'] = blood_nodes['graph_int_id'].apply(lambda x: 'artery' if set(id_of_left_ventricle_and_left_atrium+[id_of_heart]).intersection(set([comp for comp in components if x in comp][0])) else 'vein')


# those nodes whose ontology id is in both blood and whole graph but not in 'blood_vasculature' organ
nodes_except_blood = nodes[nodes['organ']!='blood_vasculature']
# matching nodes between blood vasculature and other organs
matching_nodes = nodes_except_blood[nodes_except_blood['id'].isin(blood_nodes['id'])]



def get_coordinates_for_blood_nodes(coordinates_of_nodes, only_female=False, only_male=False, bundle_edges=False):
    '''
    Get the coordinates of the blood nodes based on the coordinates of the partonomy graph nodes.

    Parameters:
    coordinates_of_nodes: dict
        The dictionary containing the coordinates of the nodes.
    only_female: bool
        If True, the visualization will not contain the prostate (so far that's the only male organ).
    only_male: bool
        If True, the visualization will not contain the ovaries, fallopian tube, uterus, placenta.
    bundle_edges: bool
        If True, the edges will be bundled (for the final viz, this is used).

    '''

    if only_female and not only_male:
        matching_nodes_filtered = matching_nodes[matching_nodes['organ']!='prostate'].copy()
        filename='female'

    elif only_male and not only_female:
        matching_nodes_filtered = matching_nodes[~matching_nodes['organ'].isin(['fallopian_tube', 'ovary', 'uterus', 'placenta'])].copy()
        filename='male'

    else:
        raise ValueError('Set either only_female or only_male parameters True')
    
    
    #Get the pruned blood graph

    parents = set(matching_nodes_filtered['graph_int_id'].tolist())

    # get the parent of each node for the tree layout
    blood_parents_dict = dict(nx.bfs_predecessors(blood_graph_int, source=262))

    pruned_blood_nodes = parents.copy()

    while len(parents)>0:
        parents = set([blood_parents_dict[node] for node in parents if node in blood_parents_dict]) - pruned_blood_nodes

        pruned_blood_nodes = pruned_blood_nodes.union(parents)


    
    pruned_blood_nodes = blood_nodes[blood_nodes['graph_int_id'].isin(pruned_blood_nodes)]

    pruned_blood_graph = nx.induced_subgraph(blood_graph_int, pruned_blood_nodes['graph_int_id'].tolist())

    veins = blood_nodes[blood_nodes['artery/vein']=='vein']['graph_int_id'].tolist()
    arteries = blood_nodes[blood_nodes['artery/vein']=='artery']['graph_int_id'].tolist()

    graphs = {'veins': nx.induced_subgraph(pruned_blood_graph, veins+[id_of_heart]), 'arteries': nx.induced_subgraph(pruned_blood_graph, arteries)}


    # get the coordinates of the nodes
    pruned_blood_nodes['coordinates'] = pruned_blood_nodes['graph_int_id'].apply(lambda x: coordinates_of_nodes[x] if x in coordinates_of_nodes else np.nan)

    pruned_blood_nodes = pruned_blood_nodes.dropna(subset=['coordinates'])

    pruned_blood_nodes.set_index('graph_int_id', inplace=True)

    coordinates = {'veins': pruned_blood_nodes[(pruned_blood_nodes['artery/vein']=='vein')|(pruned_blood_nodes['name']=='heart')]['coordinates'].to_dict(), 
                   'arteries': pruned_blood_nodes[pruned_blood_nodes['artery/vein']=='artery']['coordinates'].to_dict()}

    fixed_nodes = {'veins': pruned_blood_nodes[(pruned_blood_nodes['artery/vein']=='vein')|(pruned_blood_nodes['name']=='heart')].index.tolist(), 
                   'arteries': pruned_blood_nodes[pruned_blood_nodes['artery/vein']=='artery'].index.tolist()}

    pos = {}

    pos['veins'] = nx.spring_layout(graphs['veins'], pos=coordinates['veins'], fixed=fixed_nodes['veins'], seed=42, iterations=1000, dim=2, k=0.01/np.sqrt(len(graphs['veins'])))
    pos['arteries'] = nx.spring_layout(graphs['arteries'], pos=coordinates['arteries'], fixed=fixed_nodes['arteries'], seed=42, iterations=1000, dim=2, k=0.01/np.sqrt(len(graphs['arteries'])))


    # return graphs, pos, fixed_nodes

    if not bundle_edges:
        plt.figure(figsize=(17.2,17.2))
        plt.axes().set_aspect('equal')
        plt.margins(x=0, y=0)
        plt.xlim(0,1720)
        plt.ylim(0, 1720)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=(0,0,1,1))
        plt.axis('off') 

        nx.draw(graphs['arteries'], pos=pos['arteries'], node_size=10, edge_color='tab:red', node_color='tab:red')
        nx.draw(graphs['veins'], pos=pos['veins'], node_size=10, edge_color='tab:blue', node_color='tab:blue')
        nx.draw_networkx_nodes(graphs['arteries'], pos=pos['arteries'], nodelist=[id_of_heart], node_size=40, node_color='tab:red', node_shape='p')

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=(0,0,1,1))
        plt.axis('off')
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        plt.savefig(f'{OUTPUT_DIR}/blood_viz_{filename}.pdf',  transparent=True, pad_inches=0.0, bbox_inches=0)
        print(f'Fig saved as "{OUTPUT_DIR}/blood_viz_{filename}.pdf"')
        plt.show()

    else:
        # nodes_only = {'veins': pd.DataFrame.from_dict(relabel_mapping_inv['veins'], orient='index').rename(columns={0:'name'}), 
        #     'arteries': pd.DataFrame.from_dict(relabel_mapping_inv['arteries'], orient='index').rename(columns={0:'name'})}
        
        # nodes = {'veins': pd.DataFrame.from_dict(pos2['veins']).T.rename(columns={0:'x', 1:'y'}).join(nodes_only['veins'])[['name', 'x', 'y']], 
        #          'arteries': pd.DataFrame.from_dict(pos2['arteries']).T.rename(columns={0:'x', 1:'y'}).join(nodes_only['arteries'])[['name', 'x', 'y']]}
        
        # edges = {'veins': nx.to_pandas_edgelist(renamed_comp['veins'])[['source', 'target']], 
        #          'arteries': nx.to_pandas_edgelist(renamed_comp['arteries'])[['source', 'target']]}
        # hb = hammer_bundle(nodes, edges, initial_bandwidth=0.03,tension=0.9, accuracy=8000)
        edges = {'veins': nx.to_pandas_edgelist(graphs['veins'], source='source_int', target='target_int')[['source_int', 'target_int']].rename(columns={'source_int': 'source', 'target_int': 'target'}),
                 'arteries': nx.to_pandas_edgelist(graphs['arteries'],  source='source_int', target='target_int')[['source_int', 'target_int']].rename(columns={'source_int': 'source', 'target_int': 'target'}),
                 }
        nodes = {'veins': pd.DataFrame.from_dict(pos['veins']).T.rename(columns={0:'x', 1:'y'}),#.reset_index(names=['name']),#.join(pruned_blood_nodes[['name', 'artery/vein']]), 
                 'arteries': pd.DataFrame.from_dict(pos['arteries']).T.rename(columns={0:'x', 1:'y'})#.join(pruned_blood_nodes[['name', 'artery/vein']])
                 }
        
        
        hb = {'veins': hammer_bundle(nodes['veins'], edges['veins'], initial_bandwidth=.015, decay=0.8, tension=0.99, accuracy=1000), 
              'arteries': hammer_bundle(nodes['arteries'], edges['arteries'], initial_bandwidth=.015, decay=0.8, tension=0.99, accuracy=1000)}
        
        plt.figure(figsize=(17.2, 17.2))
        plt.axes().set_aspect('equal')
        plt.margins(x=0, y=0)
        plt.xlim(0,1720)
        plt.ylim(-1720, 0)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=(0,0,1,1))
        plt.axis('off')

        plt.plot(hb['veins']['x'], -hb['veins']['y'], color='tab:blue', alpha=0.8)
        plt.plot(hb['arteries']['x'], -hb['arteries']['y'], color='tab:red', alpha=0.8)

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.tight_layout(pad=0, h_pad=0, w_pad=0, rect=(0,0,1,1))
        plt.axis('off')
        plt.gca().set_axis_off()
        plt.subplots_adjust(top = 1, bottom = 0, right = 1, left = 0, hspace = 0, wspace = 0)
        plt.margins(0,0)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        
        plt.savefig(f'{OUTPUT_DIR}/blood_viz_{filename}_bundled.svg', pad_inches=0.0, transparent=True, bbox_inches=0)
        print(f'Fig saved as "{OUTPUT_DIR}/blood_viz_{filename}_bundled.svg"')
        plt.show()
    
        


get_coordinates_for_blood_nodes(coordinates_of_nodes_fem, only_female=True, bundle_edges=True)


get_coordinates_for_blood_nodes(coordinates_of_nodes_mal, only_male=True, bundle_edges=True)


#######################################################################################################################

# Overlay the two networks
template = st.fromfile(f'{OUTPUT_DIR}/vega_female_viz.svg', )
second_svg = st.fromfile(f'{OUTPUT_DIR}/blood_viz_female_bundled.svg')

template.set_size(size=('1720', '1720'))
second_svg.set_size(size=('1720', '1720'))  

template.append(second_svg)
template.save(f'{OUTPUT_DIR}/female_butterfly_wing.svg')


template = st.fromfile(f'{OUTPUT_DIR}/vega_male_viz.svg')
template.set_size(size=('1720', '1720'))
second_svg = st.fromfile(f'{OUTPUT_DIR}/blood_viz_male_bundled.svg')
second_svg.set_size(size=('1720', '1720'))

template.append(second_svg)
template.save(f'{OUTPUT_DIR}/male_butterfly_wing.svg')
