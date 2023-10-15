from src.params import *


class Microgrid(object):
    def __init__(self,
                 # Environment
                 working_status=[1, 1, 0],  # working status of solar PV, wind turbine, generator
                 energy_demand=34,  # energy demand (kWh) for one unit (hour)
                 soc=soc_min,  # state of charge of the battery system
                 solar_irradiance=0.1,  # solar irradiance at current decision epoch
                 wind_speed=40,  # wind speed at current decision epoch
                 energy_price_utility_grid=0.6,  # rate consumption charge, should come from data

                 # Actions (*: 0-100%, in 25% steps if discrete_steps_actions = 6)
                 actions_adjusting_status=[0, 0, 0],  # discrete: adjusting the working status
                 actions_purchased=[0, 0],  # buy energy (*) from utility grid for: [energy load, charge battery]
                 actions_solar=[0, 0, 0],  # energy (*) to support: energy load, charge battery or sell to utility grid
                 actions_wind=[0, 0, 0],
                 actions_generator=[0, 0, 0],
                 actions_discharged=0,  # energy (*) discharged by the battery for supporting the energy load
                 ):
        # Environment
        self.energy_for_battery_bought = 0
        self.energy_for_load_bought = 0
        self.energy_total = 0
        self.working_status = self.get_actions_dict(working_status, actions=["solar", "wind", "generator"])
        self.energy_demand = energy_demand
        self.soc = soc
        self.solar_irradiance = solar_irradiance
        self.wind_speed = wind_speed
        self.energy_price_utility_grid = energy_price_utility_grid

        # Actions
        self.actions_adjusting_status = self.get_actions_dict(actions_adjusting_status,
                                                      actions=["solar", "wind", "generator"])
        self.actions_purchased = self.get_actions_dict(actions_purchased, ["load", "battery"])
        # Get kWh for each action
        actions_solar = np.array(actions_solar) / (discrete_steps_actions - 1) * self.energy_generated_solar()
        actions_wind = np.array(actions_wind) / (discrete_steps_actions - 1) * self.energy_generated_wind()
        actions_generator = np.array(actions_generator) / (discrete_steps_actions - 1) * self.energy_generated_generator()
        self.actions_solar = self.get_actions_dict(actions_solar)
        self.actions_wind = self.get_actions_dict(actions_wind)
        self.actions_generator = self.get_actions_dict(actions_generator)
        self.actions_discharged = actions_discharged / (discrete_steps_actions - 1) * capacity_battery_storage

    @staticmethod
    def get_actions_dict(ls: list, actions=["load", "battery", "sell"]) -> dict:
        return {a: l for a, l in zip(actions, ls)}

    def update_actions(self, action):
        actions_adjusting_status = np.array(action["adjusting_status"]) / (discrete_steps_actions - 1)
        self.actions_adjusting_status = self.get_actions_dict(actions_adjusting_status,
                                                              actions=["solar", "wind", "generator"])
        self.actions_purchased = self.get_actions_dict(action["purchased"], ["load", "battery"])

        actions_solar = np.array(action["solar"]) / (discrete_steps_actions - 1) * self.energy_generated_solar()
        actions_wind = np.array(action["wind"]) / (discrete_steps_actions - 1) * self.energy_generated_wind()
        actions_generator = np.array(action["generator"]) / (discrete_steps_actions - 1) \
                            * self.energy_generated_generator()

        self.actions_solar = self.get_actions_dict(actions_solar)
        self.actions_wind = self.get_actions_dict(actions_wind)
        self.actions_generator = self.get_actions_dict(actions_generator)

        # TODO think about order of battery charging/discharging/etc
        self.actions_discharged = action["discharged"][0] / (discrete_steps_actions - 1) * capacity_battery_storage
        if self.soc - self.actions_discharged < soc_min:
            self.actions_discharged = self.soc - soc_min

    def update_working_status(self):
        self.working_status["solar"] = self.actions_adjusting_status["solar"]
        self.working_status["generator"] = self.actions_adjusting_status["generator"]

        if self.wind_speed > cutoff_windspeed or self.wind_speed < cutin_windspeed:
            self.working_status["wind"] = 0
        else:
            self.working_status["wind"] = self.actions_adjusting_status["wind"]

    def update_environment(self, data_dict, step_count):
        self.energy_demand = data_dict["energy_demand"][step_count]
        self.solar_irradiance = data_dict["solar_irradiance"][step_count]
        self.wind_speed = data_dict["wind_speed"][step_count]
        self.energy_price_utility_grid = data_dict["rate_consumption_charge"][step_count]

        # TODO think about order of battery charging/discharging/etc
        energy_for_battery = self.actions_solar["battery"] + self.actions_wind["battery"] + \
                             self.actions_generator["battery"]
        self.soc = self.soc + energy_for_battery * charging_discharging_efficiency

        if self.actions_purchased["battery"]:
            # Buy energy from grid to fully load battery (assumption to reduce action complexity)
            self.energy_for_battery_bought = soc_max - self.soc
            self.soc = soc_max

        energy_production = self.actions_solar["load"] + self.actions_wind["load"] + self.actions_generator["load"]
        self.energy_total = energy_production + self.actions_discharged  # add energy from battery

        if self.actions_purchased["load"] and self.energy_demand > self.energy_total:
            # Buy energy from grid to meet demand (assumption to reduce action complexity)
            self.energy_for_load_bought = self.energy_demand - self.energy_total
            self.energy_total = self.energy_total + self.energy_for_load_bought

        # TODO think about order of battery charging/discharging/etc
        energy_from_battery = self.actions_discharged / charging_discharging_efficiency
        self.soc -= energy_from_battery

        if self.soc > soc_max:
            self.soc = soc_max
        if self.soc < soc_min:
            self.soc = soc_min

    def transition(self, action, data_dict, step_count):
        self.update_actions(action)
        self.update_working_status()
        self.update_environment(data_dict, step_count)

    def energy_generated_solar(self):
        if self.working_status["solar"] > 0:
            return self.working_status["solar"] * self.solar_irradiance * area_solarPV * efficiency_solarPV / 1000
        return 0

    def energy_generated_wind(self):
        if self.working_status["wind"] > 0 and rated_windspeed > self.wind_speed >= cutin_windspeed:
            return self.working_status["wind"] * number_windturbine * rated_power_wind_turbine * (self.wind_speed -
                cutin_windspeed) / (rated_windspeed - cutin_windspeed) * 1000  # changed to kWh
        elif self.working_status["wind"] > 0 and cutoff_windspeed > self.wind_speed >= rated_windspeed:
            # changed to kWh
            return self.working_status["wind"] * number_windturbine * rated_power_wind_turbine * delta_t * 1000
        return 0

    def energy_generated_generator(self):
        if self.working_status["generator"] > 0:
            return self.working_status["generator"] * number_generators * rated_output_power_generator * delta_t
        return 0

    def check_blackout(self):
        if self.energy_total < self.energy_demand:
            return blackout_cost
        return 0

    def check_energy_mix_feasibility(self):
        if (self.energy_generated_solar() < sum(self.actions_solar.values()) or
            self.energy_generated_wind() < sum(self.actions_wind.values()) or
            self.energy_generated_generator() < sum(self.actions_generator.values())
        ):
            return feasibility_cost
        return 0

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
        energy_purchased = (self.energy_for_battery_bought + self.energy_for_load_bought) \
                           * self.energy_price_utility_grid

        punishment_costs = self.check_blackout()
        punishment_costs += self.check_energy_mix_feasibility()

        return energy_purchased + punishment_costs + self.operational_cost() - self.sell_back_reward()

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
        print("Microgrid Energy Consumption =", self.energy_total, file=file)
        print("Microgrid Operational Cost =", self.operational_cost())
