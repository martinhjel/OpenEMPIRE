from argparse import ArgumentParser
from pathlib import Path

from empire.core.config import EmpireConfiguration, read_config_file
from empire.core.model_runner import run_empire_model, setup_run_paths
from empire.input_client.client import EmpireInputClient
from empire.input_data_manager import (
    AvailabilityManager,
    CapitalCostManager,
    InitialTransmissionCapacityManager,
    MaxBuiltCapacityManager,
    MaxInstalledCapacityManager,
    MaxTransmissionCapacityManager,
    RampRateManager,
    TransmissionLengthManager,
)
from empire.logger import get_empire_logger
from empire.utils import restricted_float

parser = ArgumentParser(description="A CLI script to run the Empire model.")

parser.add_argument("-ncc", "--nuclear-capital-cost", help="Nuclear capacity cost", type=float, required=True)
parser.add_argument("-na", "--nuclear-availability", help="Nuclear availability", type=restricted_float, required=True)
parser.add_argument(
    "-w",
    "--no-onshore-wind-norway",
    help="Dont allow installed onshore wind in Norway.",
    action="store_true"
)

parser.add_argument(
    "-p",
    "--protective",
    help="Protective development of north sea with no international grid connection",
    action="store_true",
)

parser.add_argument(
    "-b",
    "--baseload",
    help="Additional load will be added as baseload, not scaled by the load profile.",
    action="store_true",
)

parser.add_argument(
    "-c",
    "--ccs",
    help="Add option to build CCS plants or not.",
    action="store_true",
)

parser.add_argument(
    "-g",
    "--germany",
    help="If true, nuclear is not allowed in Germany and Austria.",
    action="store_true",
)

parser.add_argument("-t", "--test-run", help="Test run without optimization", action="store_true")

args = parser.parse_args()

capital_cost = args.nuclear_capital_cost
nuclear_availability = args.nuclear_availability
no_onshore_wind_norway = args.no_onshore_wind_norway
additional_load_is_baseload = args.baseload
version = "europe_v51"

## Read config and setup folders ##
config = read_config_file(Path("config/run.yaml"))
empire_config = EmpireConfiguration.from_dict(config=config)

empire_config.additional_load_is_baseload = additional_load_is_baseload

run_path = Path.cwd() / "Results/run_analysis/ncc{ncc}_na{na}_w{w}_p{p}_b{b}_ccs{c}_de{g}".format(
    ncc=capital_cost,
    na=nuclear_availability,
    w=no_onshore_wind_norway,
    p=args.protective,
    b=additional_load_is_baseload,
    c=args.ccs,
    g=args.germany,
)

if (run_path / "Output/results_objective.csv").exists():
    raise ValueError("There already exists results for this analysis run.")

run_config = setup_run_paths(version=version, empire_config=empire_config, run_path=run_path)
logger = get_empire_logger(run_config=run_config)

if additional_load_is_baseload:
    if not empire_config.use_scenario_generation:
        logger.warning(
            """Setting 'use_scenario_generation' to True as load must be dynamically changed when 
            'additional_load_is_baseload' is set to True."""
        )

    empire_config.use_scenario_generation = True

logger.info("Running analysis with:")
logger.info(f"Nuclear capital cost: {capital_cost}")
logger.info(f"Nuclear availability: {nuclear_availability}")
logger.info(f"No installed onshore wind in Norway: {no_onshore_wind_norway}")
logger.info(f"Dataset version: {version}")
logger.info(f"Include CCS: {args.ccs}")
logger.info(f"Skip nuclear in Germany: {args.germany}")

client = EmpireInputClient(dataset_path=run_config.dataset_path)

data_managers = [
    AvailabilityManager(client=client, generator_technology="Nuclear", availability=nuclear_availability),
    CapitalCostManager(client=client, generator_technology="Nuclear", capital_cost=capital_cost),
]

if no_onshore_wind_norway:
    data_managers.append(
        MaxInstalledCapacityManager(
            client=client,
            nodes=["NO1", "NO2", "NO3", "NO4", "NO5"],
            generator_technology="Wind_onshr",
            max_installed_capacity=0.0,
        )
    )

if not args.germany:
    data_managers.append(
        MaxInstalledCapacityManager(
            client=client,
            generator_technology="Nuclear",
            nodes=["Germany", "Austria"],
            max_installed_capacity=200000,
        )
    )

if args.protective:
    logger.info(
        "Protective north-sea transmission policy with no collaboration on transmission capacity between countries."
    )
    # Remove international connections
    remove_transmission = [
        ["HollandseeKust", "DoggerBank"],
        ["Nordsoen", "DoggerBank"],
        ["SorligeNordsjoII", "DoggerBank"],
        ["Borssele", "EastAnglia"],
        ["SorligeNordsjoI", "FirthofForth"],
        ["Nordsoen", "HelgolanderBucht"],
        ["SorligeNordsjoI", "HelgolanderBucht"],
        ["SorligeNordsjoII", "HelgolanderBucht"],
        ["Borssele", "Hornsea"],
        ["HollandseeKust", "Hornsea"],
        ["UtsiraNord", "MorayFirth"],
        ["Borssele", "Norfolk"],
        ["HollandseeKust", "Norfolk"],
        ["HollandseeKust", "Belgium"],
        ["Hornsea", "DoggerBank"],
        ["Borssele", "Netherlands"],
        ["HelgolanderBucht", "Netherlands"],
        ["SorligeNordsjoI", "Nordsoen"],
        ["SorligeNordsjoII", "Nordsoen"],
        ["UtsiraNord", "Nordsoen"],
    ]

    for from_node, to_node in remove_transmission:
        data_managers.append(
            MaxTransmissionCapacityManager(
                client=client, from_node=from_node, to_node=to_node, max_installed_capacity=0.0
            )
        )

if args.ccs:
    logger.info("Adding CCS")
    data_managers.append(MaxBuiltCapacityManager(client=client, generator_technology="CCS", max_built_capacity=200000))

# More reasonable ramp rate for nuclear
data_managers.append(RampRateManager(client=client, thermal_generator="Nuclear", ramp_rate=0.85))

# Limit new direct cable to germany from NO2
data_managers.append(
    MaxTransmissionCapacityManager(client=client, from_node="NO2", to_node="Germany", max_installed_capacity=1400)
)

# Include North Sea Link
data_managers.append(
    InitialTransmissionCapacityManager(
        client=client, from_node="NO2", to_node="Great Brit.", initial_installed_capacity=1400
    )
)

# Northconnect
data_managers.append(
    MaxTransmissionCapacityManager(client=client, from_node="NO5", to_node="Great Brit.", max_installed_capacity=0)
)

# Update length of Norned
data_managers.append(TransmissionLengthManager(client=client, from_node="NO2", to_node="Netherlands", length=580))

## Run empire model
run_empire_model(
    empire_config=empire_config, run_config=run_config, data_managers=data_managers, test_run=args.test_run
)
