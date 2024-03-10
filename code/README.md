## Code for FTU data exploration and butterfly visualisation

There are two Python notebooks used to compile data and render visualizations.

1. Compile data for the Interactive FTU Explorer
2. Create a 6-foot (26” or 193 cm) diameter poster using ASCT+B and Blood vasculature data in a Butterfly Visual.
   
### Compile data for the Interactive FTU Explorer (FTU_Explorer_data.ipynb)
Four steps are used to compile the data:
```
1. Load data and reference file
2. Use Ensembl gene IDs and barcodes to retrieve HGNC gene symbols and cell type names.      
3. Generate CSV file with cell type label, Ensembl ID, HGNC ID, HGNC Symbol and mean expression values
4. Convert CSV file to JSON files
```

##### Load data and reference file
The code reads the gene expression matrix and three reference files that contain the gene, cell name, sample, barcode, cluster, and the cell type information from the [Single Cell Expression Atlas Portal](https://www.ebi.ac.uk/gxa/sc/experiments?species=%22homo%20sapiens%22) for kidney cortex [E-CURD-119](https://www.ebi.ac.uk/gxa/sc/experiments/E-CURD-119/downloads), liver [E-MTAB-10533](https://www.ebi.ac.uk/gxa/sc/experiments/E-MTAB-10553/downloads) and lung [E-GEOD-130148](https://www.ebi.ac.uk/gxa/sc/experiments/E-GEOD-130148/downloads)

Preview of the Expdesign file:
| CellName | Sample | Cell# | Cluster# | CellType |
|-----------|-------|-----------------|--------------|-------------------|
| P1TLH_AAACCTGTCCTCATTA_1 | P1TLH | AAACCTGTCCTCATTA | 17   | Cholangiocytes  |

- ```CellName``` is the combination of the Cell# and Sample.
- ```Sample``` signifies a specific sample, experiment, condition, or batch in the dataset.
- ```Cell#``` cell barcode which means each cell single-cell sequencing is tagged with a unique sequence (barcode) so that RNA sequences can be traced back to individual cells.
- ```Cluster#``` a number is assigned while clustering the dataset.
- ```CellType``` is the cell type label.

The reference file extension mtx_rows has the Ensembl gene ID which will be loaded as rows. The other reference file extension mtx_cols has barcodes for cell type. This section of the code first loads the gene names as the index of the gene expression matrix. Next, the mtx_cols file loads the cell type barcode as columns of the gene expression matrix.

##### Use Ensembl gene IDs and barcodes to retrieve and cell type names and HGNC IDs.
This section of the code reads Ensembl gene IDs and retrieves HGNC IDs using the *Homo_sapiens.GRCh37.87.chr.gtf.gz* database which is downloaded from [Ensembl database for human](https://ftp.ensembl.org/pub/grch37/current/gtf/homo_sapiens/). In a second step, the barcode is used to retrieve the respective cell type name by using the Expdesign file which comes from the anatomogram. Finally, we generate two dictionaries, one for gene names and another for cell types.

##### Generate CSV files with cell type label, Ensembl ID, HGNC ID, HGNC Symbol and mean expression values.
To accurately calculate average expression values for each cell type within a Functional Tissue Unit (FTU), it is imperative to preprocess the gene expression data first. This involves initially transforming the DataFrame into an AnnData structure, wherein the cell type appellations are designated as observations and gene appellations as variables. The matrix encapsulating gene expression can be accessed via anndata_object.X. Subsequently, the dataset undergoes a filtration process, retaining only those cell types associated with a atleast of 200 genes. The data undergoes a normalization procedure and is transformed into a logarithmic scale. In the final data cleansing stage, normalization of the mean expression for each gene across cell types is conducted, scaling the values to range between 0 and 1. This is achieved by deducting the minimum gene expression (np.min(gene_expression)) from each gene expression value and then dividing the result by the range of gene expression values (np.max(gene_expression) - np.min(gene_expression)).

Preview of result.csv file

| cell_label | ensembl_id | gene_label | mean expression |
|------------|-------------|------------|-----------------|
| connecting tubule | ENSG00000127914 | AKAP9  | 0.24976267 |


The HGNC gene IDs are populated using below R code:
```
# Load your CSV file containing cell types, genes, and mean expressions
# Replace 'your_file.csv' with the actual file path
data <- read.csv("result.csv")

# Define the Ensembl dataset you want to query (e.g., human, GRCh38)
ensembl <- useMart("ENSEMBL_MART_ENSEMBL", dataset = "hsapiens_gene_ensembl")

# Create a vector of unique gene symbols
unique_genes <- unique(data$Gene.Name)

# Retrieve HGNC IDs for unique gene symbols
hgnc_query <- getBM(
  	filters = "hgnc_symbol",
  	attributes = c("ensembl_gene_id","hgnc_symbol", "hgnc_id"),
 	 values = unique_genes,
 	 mart = ensembl
)

# Merge the HGNC IDs back into the original data
data <- merge(data, hgnc_query, by.x = "Gene.Name", by.y = "hgnc_symbol", all.x = TRUE)

# Save the updated data to a new CSV file
write.csv(data, "data_with_hgnc_id.csv", row.names = FALSE

```
Preview of the final CSV file:

| cell_label | ensembl_id | gene_id | gene_label | mean_expression | 
|-----------|-------|-----------------|--------------|-------------------|
| connecting tubule | ENSG00000127914 | HGNC:379 | AKAP9  | 0.24976267 |

#### Convert CSV files to JSON files

The final step is to convert the CSV file to JSON that can be used by the Interactive FTU Explorer. The JSON file has two sections called context and graph. The context section is a framework for the CSV file asking UBERON, illustration_files, mapping, organ_id and datasource information. The graph section contains the summary of the FTU. This summary has information about the cell id, cell type label, genes associated with that cell,count and percentage of that cell type. This summary structure is repeated for all the cell types available in the CSV file generated in the above step.

This section reads data from two CSV files (summary.csv and genes.csv), and then use this data to construct a JSON object that represents a structured view of cell summaries and gene expressions. This JSON object is then saved to a file named <organ>.json. 

Here's a breakdown of what the script is doing:

1. ***Reading CSV Files***: It reads data from two CSV files into pandas DataFrames (summary_df and genes_df). These files contain information about cell summaries and gene expressions, respectively.

2. ***Initializing JSON Data Structure***: The script initializes a JSON object (data) with a specific structure, including a graph of cell summaries.

3. ***Creating a Cell-Label-to-Genes Mapping***: The script iterates over the rows of the genes_df DataFrame to construct a dictionary (cell_label_to_genes). This dictionary maps cell labels to their corresponding gene information.

4. ***Populating JSON Structure with Data from Summary CSV***: The script iterates over the rows of the summary_df DataFrame. For each row, it creates a cell summary object that includes cell ID, label, associated genes (retrieved from the previously created mapping), count, and percentage. These cell summary objects are appended to the summary list within the JSON structure.

5. ***Saving JSON Data to a File**: Finally, the script writes the JSON data to a file named <organ>.json.

6. ***Confirmation Message***: After saving the JSON file, it prints a confirmation message.

An example for one cell type in the kidney-kidney-renal-corpuscle is given here:
```json
{
  "@context": [
    "https://cns-iu.github.io/hra-cell-type-populations-supporting-information/data-processor/ccf-context.jsonld",
    {
      "UBERON": {
        "@id": "http://purl.obolibrary.org/obo/UBERON_",
        "@prefix": true
      },
      "illustration_files": {
        "@id": "ccf:has_illustration_file",
        "@type": "@id"
      },
      "mapping": {
        "@id": "ccf:has_illustration_node",
        "@type": "@id"
      },
      "organ_id": {
        "@id": "ccf:organ_id",
        "@type": "@id"
      },
      "data_sources": {
        "@id": "ccf:has_data_source",
        "@type": "@id"
      }
    }
  ],
    "@graph": [
        {
            "@type": "CellSummary",
            "cell_source": "https://purl.humanatlas.io/2d-ftu/kidney-kidney-renal-corpuscle",
            "annotation_method": "Aggregation",
            "biomarker_type": "gene",
            "summary": [
		{
                    "@type": "CellSummaryRow",
                    "cell_id": "http://purl.obolibrary.org/obo/CL_0000057",
                    "cell_label": "fibroblast",
                    "genes": [
                        {.....
			}
			]
		}
		]
	}
]
}
```

### Butterfly Visualisation (HRA_Butterfly_viz.ipynb)
##### Input data
There are two sources of data for the visualization, one is for the organ partonomy network, and the other one is for the vascular network. The data tables for the organs have been downloaded from the ASCT+B Reporter in “Graph Data” format which is a JSON file containing the nodes and the edges of the individual organ networks, which have the following format:

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
