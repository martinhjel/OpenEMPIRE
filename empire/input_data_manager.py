import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from empire.core.config import EmpireRunConfiguration
from empire.input_client.client import EmpireInputClient

logger = logging.getLogger(__name__)


class IDataManager(ABC):
    @abstractmethod
    def apply(self):
        pass


class AvailabilityManager(IDataManager):
    """
    Manager responsible for updating the availability/capacity factor for specific generator technologies within a
    given dataset.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        generator_technology: str,
        availability: float,
    ) -> None:
        """
        Initializes the AvailabilityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param availability: The new availability value to be set for the specified generator technology.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.availability = availability
        self.validate()

    def validate(self) -> None:
        if self.availability < 0.0 or self.availability > 1.0:
            raise ValueError("availability has to be in range [0,1]")

    def apply(self) -> None:
        df_availability = self.client.generator.get_generator_type_availability()

        condition = df_availability["Generator"].isin([self.generator_technology])

        if not condition.any():
            raise ValueError(f"No rows found for technology {self.generator_technology}.")

        df_availability.loc[condition, "GeneratorTypeAvailability"] = self.availability

        logger.info(f"Setting availability to {self.availability} for {self.generator_technology}.")
        self.client.generator.set_generator_type_availability(df_availability)


class CapitalCostManager(IDataManager):
    """
    Manager responsible for updating the capital cost for specific generator technologies within a  given dataset.
    """

    def __init__(self, client: EmpireInputClient, generator_technology: str, capital_cost: float) -> None:
        """
        Initializes the CapitalCostManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param capital_cost: The new capital cost value to be set for the specified generator technology.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.capital_cost = capital_cost

    def apply(self) -> None:
        df_capital_costs = self.client.generator.get_capital_costs()
        df_capital_costs.loc[
            df_capital_costs["GeneratorTechnology"] == self.generator_technology,
            "generatorCapitalCost in euro per kW",
        ] = self.capital_cost

        logger.info(f"Setting capital cost to {self.capital_cost} for {self.generator_technology}.")
        self.client.generator.set_capital_costs(df_capital_costs)


class FuelCostManager(IDataManager):
    """
    Manager responsible for updating the fuel cost for specific generator technologies within a  given dataset.
    """

    def __init__(self, client: EmpireInputClient, generator_technology: str, fuel_cost: float) -> None:
        """
        Initializes the FuelCostManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param fuel_cost: The new fuel cost value to be set for the specified generator technology in EUR/GJ.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.fuel_cost = fuel_cost

    def apply(self) -> None:
        df_fuel_costs = self.client.generator.get_fuel_costs()
        df_fuel_costs.loc[
            df_fuel_costs["GeneratorTechnology"] == self.generator_technology,
            "generatorTypeFuelCost in euro per GJ",
        ] = self.fuel_cost

        logger.info(f"Setting fuel cost to {self.capital_cost} for {self.generator_technology}.")
        self.client.generator.set_fuel_costs(df_fuel_costs)


class CO2PricetManager(IDataManager):
    """
    Manager responsible for updating the CO2 price within a  given dataset.
    """

    def __init__(self, client: EmpireInputClient, periods: list[int], co2_prices: list[float]) -> None:
        """
        Initializes the CO2PricetManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param periods: The periods to set the co2 price for.
        :param co2_prices: The new co2 prices to be set for the specified periods in EUR/tCO2.
        """
        self.client = client
        self.periods = periods
        self.co2_prices = co2_prices

        if len(periods) != len(co2_prices):
            raise ValueError("Length of 'periods' have to match 'co2_prices'.")

    def apply(self) -> None:
        df_co2_price = self.client.general.get_co2_price()

        for p, c in zip(self.periods, self.co2_prices):
            df_co2_price.loc[
                df_co2_price["Period"] == p,
                "CO2price in euro per tCO2",
            ] = c

        logger.info(f"Setting CO2 price to {self.co2_prices} for the periods {self.periods}.")
        self.client.general.set_co2_price(df_co2_price)


class FixedOMCostManager(IDataManager):
    """
    Manager responsible for updating the fixed o&m cost for specific generator technologies within a  given dataset.
    """

    def __init__(self, client: EmpireInputClient, generator_technology: str, fixed_om_cost: float) -> None:
        """
        Initializes the FixedOMCostManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param fixed_om_cost: The new capital cost value to be set for the specified generator technology.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.fixed_om_cost = fixed_om_cost

    def apply(self) -> None:
        df_fixed_om_costs = self.client.generator.get_fixed_om_costs()

        y = "generatorFixedOMCost in euro per kW"
        if y not in df_fixed_om_costs.columns:  # NB: Bug in excel sheet
            y = "generatorCapitalCost in euro per kW"

        df_fixed_om_costs.loc[
            df_fixed_om_costs["GeneratorTechnology"] == self.generator_technology,
            y,
        ] = self.fixed_om_cost

        logger.info(f"Setting fixed o&m cost to {self.fixed_om_cost} for {self.generator_technology}.")
        self.client.generator.set_fixed_om_costs(df_fixed_om_costs)


class MaxInstalledCapacityManager(IDataManager):
    """
    Manager responsible for updating the maximum installed capacities for specific generator technologies within a
    given dataset.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        generator_technology: str,
        nodes: list[str],
        max_installed_capacity: float,
    ) -> None:
        """
        Initializes the MaxInstalledCapacityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param nodes: List of node names where the generator technology is applied.
        :param max_installed_capacity: The new maximum installed capacity value to be set for the specified generator technology.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.nodes = nodes
        self.max_installed_capacity = max_installed_capacity

    def apply(self) -> None:
        df_max_installed = self.client.generator.get_max_installed_capacity()

        condition = df_max_installed["Node"].isin(self.nodes) & df_max_installed["GeneratorTechnology"].isin(
            [self.generator_technology]
        )

        if not condition.any():
            raise ValueError(f"No rows found for nodes {self.nodes} and technology {self.generator_technology}.")

        df_max_installed.loc[condition, "generatorMaxInstallCapacity  in MW"] = self.max_installed_capacity

        logger.info(
            f"Setting max installed capacity to {self.max_installed_capacity} for {self.generator_technology} in nodes {self.nodes}."
        )
        self.client.generator.set_max_installed_capacity(df_max_installed)


class MaxBuiltCapacityManager(IDataManager):
    """
    Manager responsible for updating the maximum built capacities for specific generator technologies within a
    given dataset.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        generator_technology: str,
        max_built_capacity: float,
        nodes: list[str] | None = None,
    ) -> None:
        """
        Initializes the MaxBuiltCapacityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param generator_technology: The specific generator technology to be updated.
        :param max_built_capacity: The new maximum built capacity value to be set for the specified generator technology.
        :param nodes: List of node names where the generator technology is applied or None to apply for all nodes.
        """
        self.client = client
        self.generator_technology = generator_technology
        self.nodes = nodes
        self.max_built_capacity = max_built_capacity

    def apply(self) -> None:
        df_max_built = self.client.generator.get_max_built_capacity()

        if self.nodes:
            condition = df_max_built["Node"].isin(self.nodes) & df_max_built["GeneratorTechnology"].isin(
                [self.generator_technology]
            )
        else:
            condition = df_max_built["GeneratorTechnology"].isin(
                [self.generator_technology]
            )

        if not condition.any():
            raise ValueError(f"No rows found for nodes {self.nodes} and technology {self.generator_technology}.")

        df_max_built.loc[condition, "generatorMaxBuildCapacity in MW"] = self.max_built_capacity

        logger.info(
            f"Setting max built capacity to {self.max_built_capacity} for {self.generator_technology} in nodes {self.nodes}."
        )
        self.client.generator.set_max_built_capacity(df_max_built)


class MaxTransmissionCapacityManager(IDataManager):
    """
    Manager responsible for updating the maximum installed transmission capacity.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        from_node: str,
        to_node: str,
        max_installed_capacity: float,
    ) -> None:
        """
        Initializes the MaxTransmissionCapacityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param from_node: From node.
        :param to_node: To node.
        :param max_installed_capacity: The new maximum installed capacity value.
        """
        self.client = client
        self.from_node = from_node
        self.to_node = to_node
        self.max_installed_capacity = max_installed_capacity

    def apply(self) -> None:
        df_max_installed = self.client.transmission.get_max_install_capacity_raw()
        
        condition = df_max_installed["InterconnectorLinks"].isin([self.from_node]) & df_max_installed["ToNode"].isin(
            [self.to_node]
        )

        if not condition.any():
            raise ValueError(f"No transmissoion connection found between {self.from_node} and {self.to_node}.")

        df_max_installed.loc[condition, "MaxRawNotAdjustWithInitCap in MW"] = self.max_installed_capacity

        logger.info(
            f"Setting transmission capacity between {self.from_node} and {self.to_node} to {self.max_installed_capacity}"
        )
        self.client.transmission.set_max_install_capacity_raw(df_max_installed)


class ElectricLoadManager(IDataManager):
    """
    Manager responsible for adjusting the electric load.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        run_config: EmpireRunConfiguration,
        node: str,
        scale: float,
        shift: float,
        datetime_format: str = "%d/%m/%Y %H:%M",
    ) -> None:
        """
        Initializes the ElectricLoadManager with the provided parameters. Scales and shifts the load for a node for
        all periods. Note that the load profile is scaled and shifted by the first period.

        Parameters:
        -----------
        :param client: The empire input client.
        :param run_config: Empire run config.
        :param node: Node.
        :param scale: Value to scale the existing load with.
        :param shift: Value to shift the load with in MW.
        """
        self.client = client
        self.run_config = run_config
        self.node = node
        self.scale = scale
        self.shift = shift
        self.datetime_format = datetime_format

    def apply(self) -> None:
        """
        Shift the load profile, then adjust the annual demand. Note that load in the first period is used for scaling.
        """

        with open(self.run_config.empire_path / "config/countries.json", "r", encoding="utf-8") as file:
            dict_countries = json.load(file)

        df_electricload = pd.read_csv(self.run_config.scenario_data_path / "electricload.csv")
        df_electricload = df_electricload.rename(columns=dict_countries)

        if self.node not in df_electricload.columns[:-4]:
            raise ValueError(f"Node {self.node} not found in 'electricload.csv'.")

        df_electric_annual_demand = self.client.nodes.get_electric_annual_demand()

        period = df_electric_annual_demand["Period"].unique()[0]  # NB! Scales only against the first period
        cond = (df_electric_annual_demand["Nodes"] == self.node) & (df_electric_annual_demand["Period"] == period)

        scale = self.scale * df_electric_annual_demand.loc[cond, "ElectricAdjustment in MWh per hour"][0] / 8760

        df_electric_annual_demand.loc[cond, "ElectricAdjustment in MWh per hour"] = (scale + self.shift) * 8760

        df_electricload.loc[:, self.node] = (self.scale * df_electricload[self.node] + self.shift)

        self.client.nodes.set_electric_annual_demand(df_electric_annual_demand)

        logger.info(f"Scaling load in node {self.node} by {self.scale} and shifting by {self.shift}")
        df_electricload.to_csv(
            self.run_config.scenario_data_path / "electricload.csv", index=False, date_format=self.datetime_format
        )


class RampRateManager(IDataManager):
    """
    Manager responsible for updating the ramp rate of thermal generators.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        thermal_generator: str,
        ramp_rate: float,
    ) -> None:
        """
        Initializes the RampRateManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param thermal_generator: Thermal generator type.
        :param ramp_rate: Ramp rate value, (0.0, 1.0].
        """
        self.client = client
        self.thermal_generator = thermal_generator
        self.ramp_rate = ramp_rate

        self.validate()

    def validate(self):
        if self.ramp_rate > 1.0:
            raise ValueError("Ramp rate cannot be larger than 1.0")

        if self.ramp_rate <= 0.0:
            raise ValueError("Ramp rate cannot be less than or equal to 0.0")

    def apply(self) -> None:
        df_ramp_rate = self.client.generator.get_ramp_rate()

        condition = df_ramp_rate["ThermalGenerators"].isin([self.thermal_generator])

        if not condition.any():
            raise ValueError(f"No ther thermal generator called {self.thermal_generator} found in dataset.")

        df_ramp_rate.loc[df_ramp_rate["ThermalGenerators"] == self.thermal_generator, "RampRate"] = self.ramp_rate

        logger.info(f"Setting ramp rate for {self.thermal_generator} to {self.ramp_rate}")
        self.client.generator.set_ramp_rate(df_ramp_rate)


class InitialTransmissionCapacityManager(IDataManager):
    """
    Manager responsible for updating the initial installed transmission capacity.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        from_node: str,
        to_node: str,
        initial_installed_capacity: float,
    ) -> None:
        """
        Initializes the InitialTransmissionCapacityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param from_node: From node.
        :param to_node: To node.
        :param max_installed_capacity: The new maximum installed capacity value.
        """
        self.client = client
        self.from_node = from_node
        self.to_node = to_node
        self.initial_installed_capacity = initial_installed_capacity

    def apply(self) -> None:
        df_initial = self.client.transmission.get_initial_capacity()

        condition = df_initial["InterconnectorLinks"].isin([self.from_node]) & df_initial["ToNode"].isin([self.to_node])

        if not condition.any():
            raise ValueError(f"No transmissoion connection found between {self.from_node} and {self.to_node}.")

        df_initial.loc[condition, "TransmissionInitialCapacity"] = self.initial_installed_capacity

        logger.info(
            f"Setting initial transmission capacity between {self.from_node} and {self.to_node} to {self.initial_installed_capacity}"
        )
        self.client.transmission.set_initial_capacity(df_initial)


class TransmissionLengthManager(IDataManager):
    """
    Manager responsible for updating the length of transmission between nodes.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        from_node: str,
        to_node: str,
        length: float,
    ) -> None:
        """
        Initializes the TransmissionLengthCapacityManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param from_node: From node.
        :param to_node: To node.
        :param length: The new length in km.
        """
        self.client = client
        self.from_node = from_node.replace(" ", "")
        self.to_node = to_node.replace(" ", "")
        self.length = length

    def apply(self) -> None:
        df_length = self.client.transmission.get_length()

        condition = df_length["FromNode"].isin([self.from_node]) & df_length["ToNode"].isin([self.to_node])

        if not condition.any():
            raise ValueError(f"No transmission connection found between {self.from_node} and {self.to_node}.")

        df_length.loc[condition, "Length in km"] = self.length

        logger.info(f"Setting transmission length between {self.from_node} and {self.to_node} to {self.length}")
        self.client.transmission.set_length(df_length)


class TransmissionCapexManager(IDataManager):
    """
    Manager responsible for updating the capital cost of transmission types.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        transmission_type: str,
        capex: float,
    ) -> None:
        """
        Initializes the TransmissionCapexManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param transmission_type: Transmission type (HVDC_Cable/HVAC_OverheadLine).
        :param capex: The capex in EUR/MW/km.
        """
        self.client = client
        self.transmission_type = transmission_type
        self.capex = capex

    def apply(self) -> None:
        df_capex = self.client.transmission.get_type_capital_cost()

        condition = df_capex["Type"].isin([self.transmission_type])

        if not condition.any():
            raise ValueError(f"No transmission type found for {self.transmission_type}.")

        df_capex.loc[condition, "TypeCapitalCost in euro per MWkm"] = self.capex

        logger.info(f"Setting transmission type capex for {self.transmission_type} to {self.capex}")
        self.client.transmission.set_type_capital_cost(df_capex)


class TransmissionFixedOMManager(IDataManager):
    """
    Manager responsible for updating the Fixed O&M cost of transmission types.
    """

    def __init__(
        self,
        client: EmpireInputClient,
        transmission_type: str,
        fixed_om: float,
    ) -> None:
        """
        Initializes the TransmissionCapexManager with the provided parameters.

        Parameters:
        -----------
        :param client: The client interface for retrieving and setting generator data.
        :param transmission_type: Transmission type (HVDC_Cable/HVAC_OverheadLine).
        :param fixed_om: The fixed O&M in EUR/MW.
        """
        self.client = client
        self.transmission_type = transmission_type
        self.fixed_om = fixed_om

    def apply(self) -> None:
        df_fixed_om = self.client.transmission.get_type_capital_cost()

        condition = df_fixed_om["Type"].isin([self.transmission_type])

        if not condition.any():
            raise ValueError(f"No transmission type found for {self.transmission_type}.")

        df_fixed_om.loc[condition, "TypeFixedOMCost in euro per MW"] = self.fixed_om

        logger.info(f"Setting transmission type fixed o&m for {self.transmission_type} to {self.fixed_om}")
        self.client.transmission.set_type_fixed_om_cost(df_fixed_om)


if __name__ == "__main__":
    from pathlib import Path

    dataset_path = Path(
        "/Users/martihj/gitsource/OpenEMPIRE/Results/norway_analysis/ncc6000.0_na0.95_w0.0_wog0.0_pTrue/Input/Xlsx"
    )
    input_client = EmpireInputClient(dataset_path=dataset_path)

    transmission_manager = MaxTransmissionCapacityManager(
        client=input_client, from_node="SorligeNordsjoII", to_node="UtsiraNord", max_installed_capacity=0.0
    )

    transmission_manager.apply()

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
        MaxTransmissionCapacityManager(
            client=input_client, from_node=from_node, to_node=to_node, max_installed_capacity=0.0
        ).apply()
