import pandas as pd
import plotly.express as px
import streamlit as st

from app.modules.utils import get_valid_data_folders
from empire.output_client.client import EmpireOutputClient

# active_results = [i for i in (Path.cwd() / "Results/1_node").glob("*")][-1]


def compare(folders):
    st.title("Compare runs")
    # active_results = Path.cwd()/"Results/basic_run/dataset_test"

    valid_result_folders_dict = get_valid_data_folders(folders)

    col1, col2 = st.columns(2)
    results_folder_relative1 = col1.selectbox("Choose results 1: ", sorted(list(valid_result_folders_dict.keys())))
    active_results_1 = valid_result_folders_dict[results_folder_relative1]

    results_folder_relative2 = col2.selectbox("Choose results 2: ", sorted(list(valid_result_folders_dict.keys())))
    active_results_2 = valid_result_folders_dict[results_folder_relative2]

    ouput_client_1 = EmpireOutputClient(active_results_1 / "Output")
    ouput_client_2 = EmpireOutputClient(active_results_2 / "Output")

    df_op = ouput_client_1.get_node_operational_values()
    df_op["Case"] = "Case1"

    col1.markdown("Case 1")
    node_1 = col1.selectbox("Node1: ", df_op["Node"].unique())
    period_1 = col1.selectbox("Period1: ", df_op["Period"].unique())
    scenario_1 = col1.selectbox("Scenario1: ", df_op["Scenario"].unique())

    df_1 = df_op.query(f"Node=='{node_1}' and Period=='{period_1}' and Scenario=='{scenario_1}'")

    df_op = ouput_client_2.get_node_operational_values()
    df_op["Case"] = "Case2"

    col2.markdown("Case2")
    node_2 = col2.selectbox("Node2: ", df_op["Node"].unique())
    period_2 = col2.selectbox("Period2: ", df_op["Period"].unique())
    scenario_2 = col2.selectbox("Scenario2: ", df_op["Scenario"].unique())

    df_2 = df_op.query(f"Node=='{node_2}' and Period=='{period_2}' and Scenario=='{scenario_2}'")

    value = st.selectbox(
        "Value: ",
        set(df_1.columns)
        .union(set(df_2.columns))
        .difference(set(["Node", "Period", "Scenario", "Season", "Case", "Hour"])),
    )
    markers = st.toggle("Use markers")
    fig = px.line(
        pd.concat([df_1, df_2]),
        y=value,
        color="Case",
        x="Hour",
        title=f"Comparing cases for {value}",
        markers=markers,
        width=1200,
        height=700,
    )
    
    st.plotly_chart(fig)
