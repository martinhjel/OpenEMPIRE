#!/bin/bash
# This script will now serve as a job launcher

# Values for the arguments
NUCLEAR_CAPITAL_COSTS=("3200" "4200" "5300" "6900")
NUCLEAR_AVAILABILITIES=("0.95")

# Initialize all flags to false
NO_WIND="false"
PROTECTIVE="false"
BASELOAD="false"
CCS="false"
GERMANY="false"

mkdir -p ./hpc_output/

# Array of all flags
FLAGS=("NO_WIND" "PROTECTIVE" "BASELOAD" "CCS" "GERMANY")

# Submit a job for each set of parameter values with one flag set to true at a time
for flag in "${FLAGS[@]}"; do
    # Reset all flags to false
    NO_WIND="false"
    PROTECTIVE="false"
    BASELOAD="false"
    CCS="false"
    GERMANY="false"

    # Set the current flag to true
    eval $flag="true"

    for ncc in "${NUCLEAR_CAPITAL_COSTS[@]}"; do
        for na in "${NUCLEAR_AVAILABILITIES[@]}"; do
            qsub \
                -V \
                -cwd \
                    -N empire_model_${ncc}_${na}_w${NO_WIND}_p${PROTECTIVE}_b${BASELOAD}_c${CCS}_g${GERMANY} \
                -o ./hpc_output/ \
                -e ./hpc_output/ \
                -l h_rt=12:00:00 \
                -l mem_free=150G \
                    -l hostname="compute-6-1|compute-4-57|compute-4-53|compute-6-2|compute-4-56|compute-4-58|compute-6-20|compute-6-21|compute-6-22|compute-6-23" \
                -pe smp 8 \
                    ./scripts/run_analysis_sge_worker.sh $ncc $na $NO_WIND $PROTECTIVE $BASELOAD $CCS $GERMANY
        done
    done
done


# Special case with more scenarios activated
NO_WIND="true"
PROTECTIVE="true"
BASELOAD="true"
CCS="false"
GERMANY="true"

for ncc in "${NUCLEAR_CAPITAL_COSTS[@]}"; do
    for na in "${NUCLEAR_AVAILABILITIES[@]}"; do
        qsub \
            -V \
            -cwd \
                -N empire_model_${ncc}_${na}_w${NO_WIND}_p${PROTECTIVE}_b${BASELOAD}_c${CCS}_g${GERMANY} \
            -o ./hpc_output/ \
            -e ./hpc_output/ \
            -l h_rt=12:00:00 \
            -l mem_free=150G \
                -l hostname="compute-6-1|compute-4-57|compute-4-53|compute-6-2|compute-4-56|compute-4-58|compute-6-20|compute-6-21|compute-6-22|compute-6-23" \
            -pe smp 8 \
                ./scripts/run_analysis_sge_worker.sh $ncc $na $NO_WIND $PROTECTIVE $BASELOAD $CCS $GERMANY
    done
done