from pathlib import Path

import openpyxl
import pandas as pd
import yaml

from empire.input_client.client import EmpireInputClient
from empire.input_client.utils import create_empty_empire_dataset

def list_get_methods(obj):
    return [method_name for method_name in dir(obj) if callable(getattr(obj, method_name)) and method_name[:3] == "get"]


def list_set_methods(obj):
    return [method_name for method_name in dir(obj) if callable(getattr(obj, method_name)) and method_name[:3] == "set"]

dataset_name = "1_node_yaml"
periods = [1, 2]
dataset_path = Path.cwd() / f"Data handler/{dataset_name}"
if not dataset_path.exists():
    create_empty_empire_dataset(dataset_path)

yaml_input_client = EmpireInputClient(dataset_path)

existing_dataset_path = Path.cwd() / "Data handler/1_node"
existing_input_client = EmpireInputClient(dataset_path=existing_dataset_path)
new_input_client = EmpireInputClient(dataset_path=dataset_path)


def get_input_clients_as_dict(input_client: EmpireInputClient):
    return {
        "general": input_client.general,
        "generator": input_client.generator,
        "sets": input_client.sets,
        "storage": input_client.storage,
        "nodes": input_client.nodes,
        "transmission": input_client.transmission,
    }


def to_yaml(input_client: EmpireInputClient, file: Path):
    if file.suffix not in ([".yml", ".yaml"]):
        raise ValueError(f"file {file} has to be a yaml-type file.")

    clients = get_input_clients_as_dict(input_client)
    data = {}
    for client in clients:
        data[client] = {}
        for i in list_get_methods(clients[client]):
            data[client][i[4:]] = getattr(clients[client], i)().to_dict(orient="records")

    with open(file, "w") as file:
        yaml.dump(data, file, default_flow_style=False)


def from_yaml(input_client: EmpireInputClient, file: Path):
    clients = get_input_clients_as_dict(input_client)

    with open(file, "r") as file:
        data = yaml.safe_load(file)

    for client in clients:
        for i in list_set_methods(clients[client]):
            df = pd.DataFrame.from_dict(data[client][i[4:]])
            getattr(clients[client], i)(df)

yaml_file = Path.cwd()/"test.yaml"
to_yaml(existing_input_client, yaml_file)

with open("tt.yaml", "w") as f
existing_input_client.transmission.get_type_fixed_om_cost().to_dict(orient="records")

yaml_file = Path.cwd()/"Data handler/1_node_2_periods/1_node_2_periods.yaml"
from_yaml(EmpireInputClient(dataset_path=yaml_file.parent), yaml_file)


df = input_client.transmission.get_type_capital_cost()


input_client = EmpireInputClient(dataset_path=yaml_file.parent)

pd.DataFrame(data["transmission"]["type_capital_cost"])



existing_input_client.transmission.get_type_capital_cost()