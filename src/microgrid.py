import gym
from gym import spaces

from params import *


class MicrogridEnv(gym.Env):
    def __init__(self):
        # Define the action and observation spaces
        self.action_space = spaces.Discrete(3)  # Assuming 3 possible actions for each component
        self.observation_space = spaces.Dict(
            {
                "solar": spaces.Box(0, np.inf, dtype=float),
                "wind": spaces.Box(0, np.inf, dtype=float),
                "electricity price": spaces.Box(0, np.inf, dtype=float),
                "load": spaces.Box(0, np.inf, dtype=float),
                "battery": spaces.Box(SOC_min, SOC_max, dtype=float),
            }
        )
        # Initialize your Microgrid
        self.microgrid = Microgrid()

    def reset(self):
        # Reset the Microgrid to its initial state
        self.microgrid = Microgrid()
        # Return the initial observation
        return self.get_observation()

    def step(self, action):
        # Execute the chosen action on the Microgrid
        # Update the Microgrid's state and compute the reward
        # TODO: put actions
        self.microgrid.transition()

        # Calculate the reward based on your cost reduction goal
        reward = self.compute_reward()

        # Check if the episode is done (you can define a termination condition here)
        done = False  # You need to define when an episode is done

        # Return the next observation, reward, done flag, and any additional info
        return self.get_observation(), reward, done, {}

    def get_observation(self):
        # Extract relevant information from the Microgrid's state and return it as an observation
        observation = [
            self.microgrid.workingstatus[0],
            self.microgrid.workingstatus[1],
            self.microgrid.workingstatus[2],
            self.microgrid.SOC,
            self.microgrid.solarirradiance,
            self.microgrid.windspeed,
            # Add other relevant variables here
        ]
        return np.array(observation)

    def compute_reward(self):
        return self.microgrid.EnergyConsumption() * sell_back_price + self.microgrid.OperationalCost() - self.microgrid.SoldBackReward()

    def render(self, mode='human'):
        pass


class Microgrid(object):
    def __init__(self,
                 workingstatus=[0, 0, 0],  # solar PV, wind turbine, generator
                 SOC=0,  # state of charge
                 actions_adjustingstatus=[0, 0, 0],
                 actions_solar=[0, 0, 0],  # the energy load (buy), charging battery (charge), sold back (sell)
                 actions_wind=[0, 0, 0],  # the energy load (buy), charging battery (charge), sold back (sell)
                 actions_generator=[0, 0, 0],  # the energy load (buy), charging battery (charge), sold back (sell)
                 actions_purchased=[0, 0],  # the energy load (buy), charging battery (charge)
                 actions_discharged=0,  # the energy load (buy)
                 solarirradiance=0,
                 windspeed=0):
        self.workingstatus = workingstatus
        self.SOC = SOC
        self.actions_adjustingstatus = actions_adjustingstatus
        self.actions_solar = actions_solar
        self.actions_wind = actions_wind
        self.actions_generator = actions_generator
        self.actions_purchased = actions_purchased
        self.actions_discharged = actions_discharged
        self.solarirradiance = solarirradiance
        self.windspeed = windspeed

    def transition(self):
        workingstatus = self.workingstatus
        SOC = self.SOC
        if self.actions_adjustingstatus[1 - 1] == 1:
            workingstatus[1 - 1] = 1
        else:
            workingstatus[1 - 1] = 0
        if self.actions_adjustingstatus[2 - 1] == 0 or self.windspeed > cutoff_windspeed or self.windspeed < cutin_windspeed:
            workingstatus[2 - 1] = 0
        else:
            if self.actions_adjustingstatus[2 - 1] == 1 and cutoff_windspeed >= self.windspeed >= cutin_windspeed:
                workingstatus[2 - 1] = 1
        if self.actions_adjustingstatus[3 - 1] == 1:
            workingstatus[3 - 1] = 1
        else:
            workingstatus[3 - 1] = 0
        SOC = self.SOC + (self.actions_solar[2 - 1] + self.actions_wind[2 - 1] + self.actions_generator[2 - 1] + self.actions_purchased[2 - 1]) * charging_discharging_efficiency - self.actions_discharged / charging_discharging_efficiency
        if SOC > SOC_max:
            SOC = SOC_max
        if SOC < SOC_min:
            SOC = SOC_min
        return workingstatus, SOC

    def energy_consumption(self):
        return -(self.actions_solar[1 - 1] + self.actions_wind[1 - 1] + self.actions_generator[1 - 1] + self.actions_discharged)

    def energy_generated_solar(self):
        if self.workingstatus[1 - 1] == 1:
            energy_generated_solar = self.solarirradiance * area_solarPV * efficiency_solarPV / 1000
        else:
            energy_generated_solar = 0
        return energy_generated_solar

    def energy_generated_wind(self):
        if self.workingstatus[2 - 1] == 1 and rated_windspeed > self.windspeed >= cutin_windspeed:
            energy_generated_wind = number_windturbine * rated_power_wind_turbine * (self.windspeed - cutin_windspeed) / (rated_windspeed - cutin_windspeed)
        else:
            if self.workingstatus[2 - 1] == 1 and cutoff_windspeed > self.windspeed >= rated_windspeed:
                energy_generated_wind = number_windturbine * rated_power_wind_turbine * delta_t
            else:
                energy_generated_wind = 0
        return energy_generated_wind

    def energy_generated_generator(self):
        if self.workingstatus[3 - 1] == 1:
            energy_generated_generator = number_generators * rated_output_power_generator * delta_t
        else:
            energy_generated_generator = 0
        return energy_generated_generator

    def operational_cost(self):
        if self.workingstatus[1 - 1] == 1:
            energy_generated_solar = self.solarirradiance * area_solarPV * efficiency_solarPV / 1000
        else:
            energy_generated_solar = 0
        if self.workingstatus[2 - 1] == 1 and rated_windspeed > self.windspeed >= cutin_windspeed:
            energy_generated_wind = number_windturbine * rated_power_wind_turbine * (self.windspeed - cutin_windspeed) / (rated_windspeed - cutin_windspeed)
        else:
            if self.workingstatus[2 - 1] == 1 and cutoff_windspeed > self.windspeed >= rated_windspeed:
                energy_generated_wind = number_windturbine * rated_power_wind_turbine * delta_t
            else:
                energy_generated_wind = 0
        if self.workingstatus[3 - 1] == 1:
            energy_generated_generator = number_generators * rated_output_power_generator * delta_t
        else:
            energy_generated_generator = 0
        operational_cost = energy_generated_solar * unit_operational_cost_solar + energy_generated_wind * \
                           unit_operational_cost_wind + energy_generated_generator * unit_operational_cost_generator
        operational_cost += (self.actions_discharged + self.actions_solar[2 - 1] + self.actions_wind[2 - 1] + \
                             self.actions_generator[2 - 1]) * delta_t * unit_operational_cost_battery / \
                            (2 * capacity_battery_storage * (SOC_max - SOC_min))
        return operational_cost

    def sold_back_reward(self):
        return (self.actions_solar[3 - 1] + self.actions_wind[3 - 1] + self.actions_generator[3 - 1]) * unit_reward_soldbackenergy

    def print_microgrid(self, file):
        print("Microgrid working status [solar PV, wind turbine, generator]=", self.workingstatus, ", SOC =", self.SOC, file=file)
        print("microgrid actions [solar PV, wind turbine, generator]=", self.actions_adjustingstatus, file=file)
        print("solar energy supporting [the energy load, charging battery, sold back]=", self.actions_solar, file=file)
        print("wind energy supporting [the energy load, charging battery, sold back]=", self.actions_wind, file=file)
        print("generator energy supporting [the energy load, charging battery, sold back]=", self.actions_generator, file=file)
        print("energy purchased from grid supporting [the energy load, charging battery]=", self.actions_purchased, file=file)
        print("energy discharged by the battery supporting the energy load =", self.actions_discharged, file=file)
        print("solar irradiance =", self.solarirradiance, file=file)
        print("wind speed =", self.windspeed, file=file)
        print("Microgrid Energy Consumption =", self.energy_consumption(), file=file)
        print("Microgrid Operational Cost =", self.operational_cost)
