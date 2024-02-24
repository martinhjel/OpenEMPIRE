#!/bin/bash
ncc=$1
na=$2
w=$3
p=$4
b=$5
c=$6

# Load modules and activate conda environment
module load gurobi/10.0

# Check if empire_env is the active environment
if [[ "$CONDA_DEFAULT_ENV" != "empire_env" ]]; then
    # Check if empire_env exists among the installed environments
    conda info --envs | grep -q "empire_env"
    if [ $? -eq 0 ]; then
        echo "Activating existing conda environment: empire_env"
        source ~/miniconda3/bin/activate empire_env
    else
        echo "Creating new conda environment: empire_env"
        conda env create -f ./environment.yml
        source ~/miniconda3/bin/activate empire_env
        conda install -c gurobi gurobi -y
    fi
fi

echo "Active conda env: "
echo $CONDA_DEFAULT_ENV

# Initialize the base command
cmd="python scripts/run_analysis.py"

# Add arguments that are always present
cmd+=" --nuclear-capital-cost $ncc"
cmd+=" --nuclear-availability $na"
cmd+=" --max-onshore-wind-norway $w"
cmd+=" --max-offshore-wind-grounded-norway $w"

# Conditionally add the -p flag
if [ "$p" == "true" ]; then
    echo "Protective case"
    cmd+=" -p"
else
    echo "Not protective case"
fi


# Conditionally add the -b flag
if [ "$b" == "true" ]; then
    echo "Baseload case"
    cmd+=" -b"
else
    echo "Not baseload case"
fi


# Conditionally add the -c flag
if [ "$c" == "true" ]; then
    echo "Baseload case"
    cmd+=" -c"
else
    echo "Not CCS case"
fi

echo Executing: + $cmd

# Execute the command
eval $cmd

echo "Done with starting bash script!"