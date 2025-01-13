## Code for butterfly visualization

A Python notebook is used to compile data and render visualizations.

* Create a 6-foot (26” or 193 cm) diameter poster using ASCT+B and Blood vasculature data in a Butterfly Visual.
   
### Butterfly Visualisation ([HRA_Butterfly_viz_v2.ipynb](./HRA_Butterfly_viz_v2.ipynb))
##### Input data
There are two sources of data for the visualization, one is for the [organ partonomy network], and the other one is for the [vascular network](./data/Vessel.csv). All the data files can be found in the [data folder](./data/). The data tables for the organs have been downloaded from the <a href="https://humanatlas.io/asctb-reporter" target="_blank">ASCT+B Reporter</a> in “Graph Data” format which is a JSON file containing the [nodes](./data/asct_nodes.csv) and the [edges](./data/asct_edges.csv) of the individual organ networks, which have the following format:

```json
{
 "data": {
   "nodes": [
     {
       "id": 0,
       "type": "AS",
       "name": "Body",
       "metadata": {	
         "name": "Body",
         "ontologyId": "UBERON:0013702",
         "ontologyType": "UBERON",
         "ontologyTypeId": "0013702",
         "label": "body proper",
         "references": []
       }
     },
     {
       "id": 1,
       "type": "AS",
       "name": "brain",
	...
	}
	...
   ],
   "edges": [
     {
       "source": 0,
       "target": 1
     },
     {
       "source": 1,
       "target": 2
     },
     {
       "source": 2,
       "target": 3
	},
	...


   ]
 }
}


```

There are two components of the “data”, the first is the node list, which contains the ID of the node (within the organ), the name, and the type (AS, CT, BM, gene), and then there is some metadata as well. From the metadata, the only field that we use is the “ontologyId”. 

##### Data Processing
The data preprocessing Python code merges the nodes and edges of the organs and transforms the data in the following table format:

Data frame of the nodes:

| id   | id_old | name                          | type | organ             | ontology_id    |
|------|--------|-------------------------------|------|-------------------|----------------|
| 0    | 0      | Body                          | AS   | body              | UBERON:0013702 |
| 1    | 1      | Bone marrow                   | AS   | bonemarrow_pelvis | UBERON:0002371 |
| 2    | 2      | B lineage                     | CT   | bonemarrow_pelvis | CL:0000945     |
| 3    | 3      | precursor B cell (pre B cell) | CT   | bonemarrow_pelvis | CL:0000817     |
| 4    | 4      | immature B cell               | CT   | bonemarrow_pelvis | CL:0000816     |
| ...  | ...    | ...                           | ...  | ...               | ...            |
| 3521 | 91     | columnar cell of endocervix   | CT   | uterus            | CL:0002152     |
| 3522 | 92     | endocervical epithelial cell  | CT   | uterus            |                |
| 3523 | 75     | uterine smooth muscle cell    | CT   | uterus            |                |
| 3524 | 75     | uterine smooth muscle cell    | CT   | uterus            |                |
| 3525 | 76     | endothelial cell              | CT   | uterus            |                |

Data frame of the edges:

|   | source | target |
|--:|-------:|-------:|
| 0 |      1 |      2 |
| 1 |      1 |      3 |
| 2 |      1 |      5 |
| 3 |      1 |     10 |
| 4 |      1 |     12 |


The preprocessing part has the following steps:

The code has one input: a dictionary, where the keys are the organs and the values are the downloaded JSON data, and the code outputs the data frames of the nodes and the edges.  
The code performs the following steps:
1. Create a new ID:
 	 - In the data table, the ‘old_id’ column represents the id of the node in the corresponding organ table, and the new ‘id’ column is the node’s id in the whole body. The starting number of the IDs in the organs is always zero (zero is always the ID of ‘body’ and ‘1’ is the ID of the organ of the corresponding table). To be able to merge the tables, a new ID of the nodes is created where every ID is unique. 
2. Filter nodes:
  	- Only the anatomical structures and cell types are kept
3. Extract the uberon ID
  	- The uberon ID is given as a metadata feature, and the code extracts it and gives it as a “main” property of the nodes
4. Merge the nodes of different organs
5. Filter edges:
  	- The code removes those edges that are between cell types (if there are any) - if the graph data is correctly generated, there should not be any edges between cell types.
6. Renumber the edges:
  	- The edge list in the JSON file is given using the local “within-organ” ID, hence the organ IDs are replaced with the newly created global “within-body” ID to make the combined network visualization possible.
7. Correction of organ data
  	- For some organs, the networks in the ASCT+B reporter are disconnected networks. To avoid that, some edges are manually added to connect these disconnected parts to the corresponding organ node.
8. Clone cell types:
  	- The network extracted from the JSON data should be a tree, but sometimes a cell type is linked to two or more different AS (it has many parents because all those AS contain that CT). In this case, this CT node is cloned (as many times as many additional parents it has), the new clones are appended to the node table with the same properties but new IDs, and they are connected to one of the AS parents, so each CT clone has only one parent. 
9. Validate if the individual organ networks are trees (free of cycles and connected)

Since the visualization follows the format from the ASCT+B reporter, in the anatomical structures are in the inner layers, while the cell types are at the last layer, meaning that the cell types are the leaves of the tree. 


##### Partonomy radial tree layout
To be able to visualize the network, the  `construct_network_create_vega_viz` performs the above-detailed data preprocessing and creates the node and edge lists. Then since the visualization is created in Vega (https://vega.github.io/editor), the output of this code is a JSON file that will be the input of Vega. The code identifies the parent node of each node (for the visualization), sets the color and labels of the nodes, and then using a template vega_config.json file writes the network data in the file and saves it in a new file. The visualization can be done by copy-pasting the content of the created JSON file in the online editor (https://vega.github.io/editor).


##### Vascular network layout
The data input for the vascular network is the Vessel.csv file from here https://zenodo.org/records/7542316 which has the following format:

|   |   BranchesFrom |                       Vessel |           ASID |    VesselType |      BodyPart |     BodyPartID |
|--:|---------------:|-----------------------------:|---------------:|--------------:|--------------:|---------------:|
| 0 |    left atrium |                  left atrium | UBERON:0002079 | heart chamber | heart chamber | UBERON:0004151 |
| 1 |    left atrium | left inferior pulmonary vein |       fma49913 |          vein |          lung | UBERON:0002048 |
| 2 |    left atrium | left superior pulmonary vein |       fma49916 |          vein |          lung | UBERON:0002048 |
| 3 |    left atrium |               pulmonary vein | UBERON:0002016 |          vein |          lung | UBERON:0002048 |
| 4 | pulmonary vein |     segmental pulmonary vein |        fma9411 |          vein |          lung | UBERON:0002048 |

The visualization of the vascular network is as follows:
1. Get the matching nodes
  	- To be able to layover the vascular network over the organ network, first, the matching nodes have to be identified (nodes that are present in both data sources). The matching is based on the ‘ASID’ field of the vascular data and the ‘ontology_id’ field of the organ data. 
2. Create the full vascular network
  	- The visualized network is a subgraph of the full vascular network, hence first, the full network has to be created. It is created using the ‘BranchesFrom’ and ‘Vessel’ columns with the former one being the source and the latter one being the target of the edges.
3. Prune the network at the matching nodes.
  	- The pruning algorithm is as follows: the first layer consists of the matching nodes, and then in each iteration, a new inner layer is constructed containing the parent nodes (vessels) of the nodes in the previous iteration. Hence, the algorithm discovers the nodes by moving from the matching nodes towards the core of the network. 
4. Make the network connected
  	- The original vascular network is given in a disconnected format, there is one network for each VesselType (one for veins, one for arteries, one for heart chambers, and so on). To make the network connected, the central vessels (right atrium, right ventricle, left atrium, left ventricle) of these networks are connected to a root node, called ‘blood vasculature’.
5. Get the position/coordinates of the matching nodes
  	- To be able to layover the two networks on top of each other, the matching nodes must have the same coordinates. To ensure that, first we have to extract these coordinates from the Vega visualization. For that, we export the Vega visualization in JSON and then assign these coordinates to the matching nodes.
6. Visualize the network.
   	- For the visualization, we apply the spring layout of `networkx` which uses the Fruchterman-Reingold force-directed algorithm where we fix the position of the matching nodes using the extracted coordinates.
   	- To make the edges curved, we use the `hammer_bundle` function of the `Datashader` package

The output of the function is a pdf file. 

##### Combine both visualizations in Illustrator
Finally, the two networks have been overlaid in Adobe Illustrator as follows:
1. Create a new canvas of size 1780x1780
2. Import the organ visualization and set its parameters:
   ```
      X: 920
      Y: 890
      W: 1720
      H: 1720
   ```
3. Import the vascular network and set its parameters to the same:
    ```
      X: 920
      Y: 890
      W: 1720
      H: 1720
    ```
4. The female visualization is mirrored/flipped vertically.

**Note**: While printing, it is recommended that the outline be aligned to 25".
