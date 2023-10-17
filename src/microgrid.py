from src.params import *


class Microgrid(object):
    def __init__(self,
                 # Environment
                 working_status=[1, 0, 0],  # working status of solar PV, wind turbine, generator
                 energy_demand=34,  # energy demand (kWh) for one unit (hour)
                 soc=soc_min,  # state of charge of the battery system
                 solar_irradiance=0.1,  # solar irradiance at current decision epoch
                 wind_speed=40,  # wind speed at current decision epoch
                 energy_price_utility_grid=0.6,  # rate consumption charge, should come from data

                 actions_adjusting_status=[0, 0, 0],
                 actions_solar=0,  # energy  to support: energy load, charge battery or sell to utility grid
                 actions_wind=0,
                 actions_generator=0,
                 actions_purchased=[0, 0],  # buy energy from utility grid for: [energy load, charge battery]
                 actions_discharged=0,
                 alternative_cost=False
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
        self.operational_cost_battery = 0
        self.energy_purchased = 0
        self.alternative_cost = alternative_cost

        # Actions
        self.actions_adjusting_status = self.get_actions_dict(actions_adjusting_status,
                                                      actions=["solar", "wind", "generator"])
        self.actions_solar = actions_solar
        self.actions_wind = actions_wind
        self.actions_generator = actions_generator
        self.actions_purchased = self.get_actions_dict(actions_purchased,
                                                      actions=["load", "battery"])
        self.actions_discharged = actions_discharged

    @staticmethod
    def get_actions_dict(ls: list, actions=["load", "battery", "sell"]) -> dict:
        return {a: l for a, l in zip(actions, ls)}

    def update_actions(self, action):
        self.actions_adjusting_status = self.get_actions_dict(action["adjusting_status"],
                                                              actions=["solar", "wind", "generator"])
        self.actions_solar = action["solar"]
        self.actions_wind = action["wind"]
        self.actions_generator = action["generator"]
        self.actions_purchased = self.get_actions_dict(action["purchased"],
                                                              actions=["load", "battery"])
        self.actions_discharged = action["discharged"]

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

        # Production
        self.energy_total = 0
        if self.actions_solar == 0:
            self.energy_total += self.energy_generated_solar()
        if self.actions_wind == 0:
            self.energy_total += self.energy_generated_wind()
        if self.actions_generator == 0:
            self.energy_total += self.energy_generated_generator()
        if self.actions_discharged == 1:
            self.energy_total += self.soc - soc_min
            self.soc = soc_min

        if self.actions_purchased["load"] and self.energy_demand > self.energy_total:
            # Buy energy from grid to meet demand (assumption to reduce action complexity)
            self.energy_for_load_bought = self.energy_demand - self.energy_total
            self.energy_total += self.energy_for_load_bought

        # Battery
        self.operational_cost_battery = 0

        if self.actions_solar == 1:
            self.soc += self.energy_generated_solar() * charging_discharging_efficiency
            self.operational_cost_battery += self.energy_generated_solar()
        if self.actions_wind == 1:
            self.soc += self.energy_generated_wind() * charging_discharging_efficiency
            self.operational_cost_battery += self.energy_generated_wind()
        if self.actions_generator == 1:
            self.soc += self.energy_generated_generator() * charging_discharging_efficiency
            self.operational_cost_battery += self.energy_generated_generator()

        if self.soc > soc_max:
            self.soc = soc_max

        if self.actions_purchased["battery"] == 1:
            # Buy energy from grid to fully load battery (assumption to reduce action complexity)
            self.energy_for_battery_bought = soc_max - self.soc
            self.soc = soc_max
            self.operational_cost_battery += self.energy_for_battery_bought

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

    def operational_cost(self):
        # Cost of operating solar, wind and generator production
        operational_cost = self.energy_generated_solar() * unit_operational_cost_solar + \
                           self.energy_generated_wind() * unit_operational_cost_wind + \
                           self.energy_generated_generator() * unit_operational_cost_generator
        # Cost of battery usage
        operational_cost += self.operational_cost_battery * delta_t * unit_operational_cost_battery / \
                            (2 * capacity_battery_storage * (soc_max - soc_min))
        return operational_cost

    def sell_back_reward(self):
        sell_back_energy = 0
        if self.actions_solar == 2:
            sell_back_energy += self.energy_generated_solar() * sell_back_energy_price
        if self.actions_wind == 2:
            sell_back_energy += self.energy_generated_wind() * sell_back_energy_price
        if self.actions_generator == 2:
            sell_back_energy += self.energy_generated_generator() * sell_back_energy_price
        return sell_back_energy
    
    def cost_of_epoch(self):
        if self.alternative_cost:
            energy_purchased = self.energy_for_battery_bought + self.energy_for_load_bought
            
            self.energy_purchased = 0.25 * energy_purchased**2 * self.energy_price_utility_grid + \
                                    0.5 * energy_purchased * self.energy_price_utility_grid
        else:
            self.energy_purchased = (self.energy_for_battery_bought + self.energy_for_load_bought) \
                   * self.energy_price_utility_grid
        
        punishment_costs = self.check_blackout()
        return self.energy_purchased + punishment_costs + self.operational_cost() - self.sell_back_reward()

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
