import pandas as pd

# URLs for the data
nodes_url = "https://raw.githubusercontent.com/cns-iu/hra-ftu-vccf-supporting-information/main/code/data/asct-nodes.csv" 
edges_url = "https://raw.githubusercontent.com/cns-iu/hra-ftu-vccf-supporting-information/main/code/data/asct-edges.csv"

# Load the data
nodes = pd.read_csv(nodes_url)
edges = pd.read_csv(edges_url)

# Check for duplicates
print('duplicated nodes based on id, type, organ, and ontology_id:')
print(nodes.duplicated(subset=['id', 'type', 'organ', 'ontology_id']).sum(), end='\n\n')



# get the nodes from the data based on the name or ontology_id
def get_nodes(name=None, ontology_id=None):
    if name:
        return nodes[nodes['name']==name]
    if ontology_id:
        return nodes[nodes['ontology_id']==ontology_id]   
    

# print the rows corresponding to heart
print('All the nodes corresponding to heart:')
print(get_nodes(ontology_id='UBERON:0000948'), end='\n\n')


# examples for the duplicate nodes in the vasculature
print('Ten examples of duplicate nodes in the vasculature:')
print(nodes[nodes['ontology_id'].duplicated(keep=False)&(nodes['organ']=='blood_vasculature')].head(10), end='\n\n')

#one example of the duplicate nodes in the vasculature
print('Number of left cardiac atriums in the data:')
print(len(get_nodes(ontology_id='UBERON:0002079')), end='\n\n')

# print the rows corresponding to left cardiac atrium
print('All the nodes corresponding to left cardiac atrium:')
print(get_nodes(ontology_id='UBERON:0002079'), end='\n\n')