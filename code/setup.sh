#!/bin/bash

# Specify the full path to the Conda binary
CONDA_BIN="/Users/sbidanta/opt/anaconda3/bin/conda"

# Create a Conda environment named 'butterfly'
$CONDA_BIN create -n butterfly python=3.11 -y

# Activate the Conda environment
source $CONDA_BIN activate butterfly

# Upgrade pip to the latest version
pip install --upgrade pip

# Install the dependencies from requirements.txt
pip install -r requirements.txt

echo "Environment setup is complete. Conda environment 'butterfly' is activated."
echo "To deactivate, use the 'conda deactivate' command."