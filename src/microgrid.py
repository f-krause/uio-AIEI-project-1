from params import *


class Microgrid(object):
    def __init__(self,
                 # Environment
                 working_status=[0, 0, 0],  # working status of solar PV, wind turbine, generator
                 energy_demand=0,  # energy demand (kWh) for one unit (hour)
                 soc=0,  # state of charge of the battery system
                 solar_irradiance=0,  # solar irradiance at current decision epoch
                 wind_speed=0,  # wind speed at current decision epoch
                 energy_price_utility_grid=np.inf,  # rate consumption charge, should come from data

                 # Actions
                 actions_adjusting_status=[0, 0, 0],  # binary: adjusting the working status
                 actions_solar=[0, 0, 0],  # energy (kWh) to support: energy load, charging battery or selling to utility grig
                 actions_wind=[0, 0, 0],
                 actions_generator=[0, 0, 0],
                 actions_purchased=[0, 0],  # buy energy from utility grid for: [kWh for energy load, kWh to charge battery]
                 actions_discharged=0,  # energy discharged by the battery for supporting the energy load
                 ):
        # Environment
        self.working_status = self.get_actions_dict(working_status, actions=["solar", "wind", "generator"])
        self.energy_demand = energy_demand
        self.soc = soc
        self.solar_irradiance = solar_irradiance
        self.wind_speed = wind_speed
        self.energy_price_utility_grid = energy_price_utility_grid

        # Actions
        self.actions_adjusting_status = self.get_actions_dict(actions_adjusting_status,
                                                              actions=["solar", "wind", "generator"])
        self.actions_solar = self.get_actions_dict(actions_solar)
        self.actions_wind = self.get_actions_dict(actions_wind)
        self.actions_generator = self.get_actions_dict(actions_generator)
        self.actions_purchased = self.get_actions_dict(actions_purchased, ["load", "battery"])
        self.actions_discharged = actions_discharged

    @staticmethod
    def get_actions_dict(ls: list, actions=["load", "battery", "sell"]) -> dict:
        return {a: l for a, l in zip(actions, ls)}

    def update_actions(self, action):
        self.actions_adjusting_status = Microgrid.get_actions_dict(action["adjusting status"],
                                                                   actions=["solar", "wind", "generator"])
        self.actions_solar = Microgrid.get_actions_dict(action["solar"])
        self.actions_wind = Microgrid.get_actions_dict(action["wind"])
        self.actions_generator = Microgrid.get_actions_dict(action["generator"])
        self.actions_purchased = Microgrid.get_actions_dict(action["purchased"], ["load", "battery"])
        self.actions_discharged = action["discharged"][0]

    def update_working_status(self):
        self.working_status["solar"] = self.actions_adjusting_status["solar"]
        self.working_status["generator"] = self.actions_adjusting_status["generator"]

        if (
                self.actions_adjusting_status["wind"] == 0 or
                self.wind_speed > cutoff_windspeed or
                self.wind_speed < cutin_windspeed
        ):
            self.working_status["wind"] = 0
        else:
            self.working_status["wind"] = 1

    def update_environment(self, data_dict, step_count):
        self.energy_demand = data_dict["energy_demand"][step_count]
        self.solar_irradiance = data_dict["solar_irradiance"][step_count]
        self.wind_speed = data_dict["wind_speed"][step_count]
        self.energy_price_utility_grid = data_dict["rate_consumption_charge"][step_count]

        energy_for_battery = self.actions_solar["battery"] + self.actions_wind["battery"] + \
                             self.actions_generator["battery"] + self.actions_purchased["battery"]
        energy_from_battery = self.actions_discharged / charging_discharging_efficiency
        self.soc = self.soc + energy_for_battery * charging_discharging_efficiency - energy_from_battery

        if self.soc > soc_max:
            self.soc = soc_max
        if self.soc < soc_min:
            self.soc = soc_min

    def transition(self, action, data_dict, step_count):
        self.update_actions(action)
        self.update_working_status()
        self.update_environment(data_dict, step_count)

    def energy_load(self):
        energy_production = self.actions_solar["load"] + self.actions_wind["load"] + self.actions_generator["load"]
        return energy_production + self.actions_discharged + self.actions_purchased["load"]

    def energy_generated_solar(self):
        if self.working_status["solar"] == 1:
            energy_solar = self.solar_irradiance * area_solarPV * efficiency_solarPV / 1000
        else:
            energy_solar = 0
        return energy_solar

    def energy_generated_wind(self):
        if self.working_status["wind"] == 1 and rated_windspeed > self.wind_speed >= cutin_windspeed:
            energy_wind = number_windturbine * rated_power_wind_turbine * (self.wind_speed - cutin_windspeed) / (
                        rated_windspeed - cutin_windspeed)
        else:
            if self.working_status["wind"] == 1 and cutoff_windspeed > self.wind_speed >= rated_windspeed:
                energy_wind = number_windturbine * rated_power_wind_turbine * delta_t
            else:
                energy_wind = 0
        return energy_wind

    def energy_generated_generator(self):
        if self.working_status["generator"] == 1:
            energy_generator = number_generators * rated_output_power_generator * delta_t
        else:
            energy_generator = 0
        return energy_generator

    def operational_cost(self):
        # Cost of operating solar, wind and generator production
        operational_cost = self.energy_generated_solar() * unit_operational_cost_solar + \
                           self.energy_generated_wind() * unit_operational_cost_wind + \
                           self.energy_generated_generator() * unit_operational_cost_generator
        # Cost of battery usage
        operational_cost += (self.actions_discharged + self.actions_solar["battery"] + self.actions_wind["battery"]
                             + self.actions_generator["battery"]) * delta_t * unit_operational_cost_battery / \
                            (2 * capacity_battery_storage * (soc_max - soc_min))
        return operational_cost

    def sell_back_reward(self):
        return (self.actions_solar["sell"] + self.actions_wind["sell"] + self.actions_generator["sell"]) \
            * sell_back_energy_price

    def cost_of_epoch(self):
        energy_purchased = sum(self.actions_purchased.values()) * self.energy_price_utility_grid

        if self.energy_load() < self.energy_demand:
            energy_purchased += blackout_cost

        return energy_purchased + self.operational_cost() - self.sell_back_reward()

    def print_microgrid(self, file=None):
        print("Microgrid working status [solar PV, wind turbine, generator]=", self.working_status, ", SOC =", self.soc,
              file=file)
        print("microgrid actions [solar PV, wind turbine, generator]=", self.actions_adjusting_status, file=file)
        print("solar energy supporting [the energy load, charging battery, sold back]=", self.actions_solar, file=file)
        print("wind energy supporting [the energy load, charging battery, sold back]=", self.actions_wind, file=file)
        print("generator energy supporting [the energy load, charging battery, sold back]=", self.actions_generator,
              file=file)
        print("energy purchased from grid supporting [the energy load, charging battery]=", self.actions_purchased,
              file=file)
        print("energy discharged by the battery supporting the energy load =", self.actions_discharged, file=file)
        print("solar irradiance =", self.solar_irradiance, file=file)
        print("wind speed =", self.wind_speed, file=file)
        print("Microgrid Energy Consumption =", self.energy_load(), file=file)
        print("Microgrid Operational Cost =", self.operational_cost())
