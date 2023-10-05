from params import *


class Microgrid(object):
    def __init__(self,
                 # Environment
                 working_status=[0, 0, 0],  # working status of solar PV, wind turbine, generator
                 soc=0,  # state of charge of the battery system
                 solar_irradiance=0,  # solar irradiance at current decision epoch
                 wind_speed=0,  # wind speed at current decision epoch

                 # Actions
                 actions_adjusting_status=[0, 0, 0],  # binary: adjusting the working status
                 actions_solar=[0, 0, 0],  # energy (kWh) to support: energy load, charging battery or selling to utility grig
                 actions_wind=[0, 0, 0],
                 actions_generator=[0, 0, 0],
                 actions_purchased=[0, 0],  # buy energy from utility grid for: [kWh for energy load, kWh to charge battery]
                 actions_discharged=0,  # energy discharged by the battery for supporting the energy load
                 ):
        self.working_status = {"s": working_status[0], "w": working_status[1], "g": working_status[2]}
        self.soc = soc
        self.solar_irradiance = solar_irradiance
        self.wind_speed = wind_speed

        self.actions_adjusting_status = {"s": actions_adjusting_status[0], "w": actions_adjusting_status[1],
                                         "g": actions_adjusting_status[2]}
        self.actions_solar = self.get_actions_dict(actions_solar)
        self.actions_wind = self.get_actions_dict(actions_wind)
        self.actions_generator = self.get_actions_dict(actions_generator)
        self.actions_purchased = actions_purchased
        self.actions_discharged = actions_discharged

    @staticmethod
    def get_actions_dict(ls: list, actions=None) -> dict:
        if not actions:
            actions = ["load", "battery", "sell"]
        return {a: l for a, l in zip(actions, ls)}

    def transition(self):
        working_status = self.working_status
        working_status["s"] = self.actions_adjusting_status["s"]
        working_status["g"] = self.actions_adjusting_status["g"]

        if (
                self.actions_adjusting_status["w"] == 0 or
                self.wind_speed > cutoff_windspeed or
                self.wind_speed < cutin_windspeed
        ):
            working_status["w"] = 0
        else:
            working_status["w"] = 1

        energy_for_battery = self.actions_solar["battery"] + self.actions_wind["battery"] + \
                             self.actions_generator["battery"] + self.actions_purchased[2 - 1]
        energy_from_battery = self.actions_discharged / charging_discharging_efficiency
        soc = self.soc + energy_for_battery * charging_discharging_efficiency - energy_from_battery

        if soc > soc_max:
            soc = soc_max
        if soc < soc_min:
            soc = soc_min
        return list(working_status.values()), soc

    def energy_consumption(self):
        # FIXME isn't this energy production?
        # And what do we need this for? Why negative?
        return -(self.actions_solar["load"] + self.actions_wind["load"] + self.actions_generator[
            "load"] + self.actions_discharged)

    def energy_generated_solar(self):
        if self.working_status["s"] == 1:
            energy_solar = self.solar_irradiance * area_solarPV * efficiency_solarPV / 1000
        else:
            energy_solar = 0
        return energy_solar

    def energy_generated_wind(self):
        if self.working_status["w"] == 1 and rated_windspeed > self.wind_speed >= cutin_windspeed:
            energy_wind = number_windturbine * rated_power_wind_turbine * (self.wind_speed - cutin_windspeed) / (
                        rated_windspeed - cutin_windspeed)
        else:
            if self.working_status["w"] == 1 and cutoff_windspeed > self.wind_speed >= rated_windspeed:
                energy_wind = number_windturbine * rated_power_wind_turbine * delta_t
            else:
                energy_wind = 0
        return energy_wind

    def energy_generated_generator(self):
        if self.working_status["g"] == 1:
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
        energy_price_utility_grid = 10  # FIXME should come from data
        energy_purchased = sum(self.actions_purchased) * energy_price_utility_grid

        # TODO: cost of blackout?

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
        print("Microgrid Energy Consumption =", self.energy_consumption(), file=file)
        print("Microgrid Operational Cost =", self.operational_cost())
