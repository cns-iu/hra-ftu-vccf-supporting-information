## Functional Tissue Units in the Human Reference Atlas

Supriya Bidanta<sup>1,5</sup>, Katy Börner<sup>1,5,6</sup>, Ellen M. Quardokus<sup>1</sup>, Bruce W. Herr II<sup>1</sup>, Marcell Nagy<sup>2</sup>, Katherine S. Gustilo<sup>1</sup>, Rachel Bajema<sup>1</sup>, Libby Maier<sup>1</sup>, Roland Molontay<sup>2,3</sup>, Griffin Weber<sup>4,6</sup>

<sup>1</sup> Indiana University, Bloomington, IN; 
<sup>2</sup> Budapest University of Technology and Economics, Budapest, Hungary;
<sup>3</sup> Institute of Biostatistics and Network Science, Semmelweis University, Budapest, Hungary;
<sup>4</sup> Harvard Medical School, Boston, MA


<sup>5</sup> Contributed equally (co-first authors)
<sup>6</sup> Corresponding authors 

Functional tissue units (FTUs) form the basic building blocks of organs and are important for understanding and modeling the healthy physiological function of the organ and changes that occur during disease states. In this first comprehensive catalog of 22 anatomically based, nested functional tissue units (FTUs) from 10 healthy human organs, we document the definition, physical dimensions, blood vasculature connections, and cellular composition. All anatomy terms are mapped to the multi-species Uber-anatomy Ontology (UBERON) and Cell Ontology (CL) to support computational access via standardized metadata. The catalog includes datasets, illustrations, and a large printable poster illustrating how the blood vasculature connects the 22 FTUs in 10 organs. All data and code are freely available. The work is part of an ongoing international effort to construct a Human Reference Atlas (HRA) of all cells in the human body.

The repo is structured in the following way:

```
├── data
├── code
├── visualization
```

### Data
The data folder contains 1 supplemental data with information on blood vasculature in all 22 FTUs.
  
### Code
A Python notebook is provided. Run HRA_Butterfly_viz.ipynb to generate a radial tree butterfly resembling visualization of the anatomical structures partonomy with an overlay of the vasculature tree that connects the chambers of the heart in the center via increasingly smaller vessels to the 22 FTUs.

##### Prerequisite:
  - Python (version > 3.12)
  - for the ipynb vs code/pycharm/data spell (or something other than jupyter) is recommended.
  - packages: pandas, numpy, matplotlib, json, networkx, datashader, vl_convert, svgutils  

The butterfly visualization code reads data from the <a href="https://humanatlas.io/asctb-reporter" target="_blank">ASCT+B Reporter</a> in JSON format. It generates SVG files that can be combined and post-processed in a graphics editor like Adobe Illustrator to add a legend, title, FTUs, and any other information.

The static version of the data and code can be found in Zenodo under the DOI: <a href="https://zenodo.org/records/11477238" target="_blank">10.5281/zenodo.11477238</a>
   
### Visualization
The directory features all files to view and print the 36" poster. To print the poster on a 36" printer, resize the two halves to 35.5".
