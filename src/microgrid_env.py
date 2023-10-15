import gym
from gym import spaces
import pandas as pd

from src.params import *
from src.microgrid import Microgrid


class MicrogridEnv(gym.Env):
    def __init__(self, data_dict):
        """
        Params:
            data_dict: hourly environment data. Should contain the following
                keys: "energy_demand", "solar_irradiance", "wind_speed", and
                "rate_consumption_charge". Each key should map to a list value
                containing the hourly data for that variable.
        """

        # Define the action space
        num_binary_actions = 2  # "actions_purchased"
        num_discrete_actions = 13  # all other variables with discrete scale

        # Combine the binary and discrete action spaces
        self.action_space = spaces.MultiDiscrete(
            [2] * num_binary_actions + [discrete_steps_actions] * num_discrete_actions)

        # Define observation space
        self.observation_space = spaces.Box(low=np.array([0] * 4 + [soc_min]),
                                            high=np.array(
                                                [10_000,  # solar irradiance
                                                 100,  # wind speed
                                                 10,  # electricity price to sell for
                                                 10_000,  # energy demand in kWh
                                                 soc_max,  # battery status
                                                 ]),
                                            dtype=np.float64)

        # Initialize your Microgrid
        self.microgrid = Microgrid()
        self.step_count = 0
        self.data_dict = data_dict  # hourly environment data

    def reset(self, **kwargs):
        self.step_count = 0
        # Reset the Microgrid to its initial state
        self.microgrid = Microgrid()
        # Return the initial observation
        return self.get_observation()

    def step(self, action):
        # Split the flattened action into sub-actions
        # adjusting_status = action[:3]
        # Ensure that adjusting_status values are either 0 or 1
        # adjusting_status = np.round(adjusting_status).astype(int)
        action_dict = {
            "purchased": action[0:2],
            "adjusting_status": action[2:5],
            "solar": action[5:8],
            "wind": action[8:11],
            "generator": action[11:14],
            "discharged": [action[14]]
        }

        # Execute the chosen action on the Microgrid
        self.microgrid.transition(action_dict, self.data_dict, self.step_count)

        # Calculate the reward based on your cost reduction goal
        reward = self.compute_reward()

        # Check if the episode is done (you can define a termination condition here)
        self.step_count += 1
        max_epochs = len(self.data_dict["wind_speed"])
        done = self.step_count >= max_epochs  # You need to define when an episode is done

        # Return the next observation, reward, done flag, and any additional info
        return self.get_observation(), reward, done, {}

    def get_observation(self):
        # Extract relevant information from the Microgrid's state and return it as an observation (environment state)
        # TODO scaling?

        return [self.microgrid.solar_irradiance, self.microgrid.wind_speed, self.microgrid.energy_price_utility_grid,
               self.microgrid.energy_demand, self.microgrid.soc]

    def compute_reward(self):
        # negative costs as reward
        return -self.microgrid.cost_of_epoch()

    def render(self, mode='human'):
        mg = self.microgrid

        info = {
            "reward": self.compute_reward(),
            "operational_cost": mg.operational_cost(),
            "sell_back_reward": mg.sell_back_reward(),
            "energy_demand": mg.energy_demand,
            "energy_load": mg.energy_total,
            "discharged": mg.actions_discharged,

            "energy_purchased": mg.actions_purchased,
            "energy_battery_discharged": mg.actions_discharged,

            "energy_generated_solar": mg.energy_generated_solar(),
            "solar_load": mg.actions_solar["load"],
            "solar_battery": mg.actions_solar["battery"],
            "solar_sell": mg.actions_solar["sell"],

            "energy_generated_wind": mg.energy_generated_wind(),
            "wind_load": mg.actions_wind["load"],
            "wind_battery": mg.actions_wind["battery"],
            "wind_sell": mg.actions_wind["sell"],

            "energy_generated_generator": mg.energy_generated_generator(),
            "generator_load": mg.actions_generator["load"],
            "generator_battery": mg.actions_generator["battery"],
            "generator_sell": mg.actions_generator["sell"],

            "actions_adjusting_status": mg.actions_adjusting_status,
            "soc": mg.soc,
            "solar_irradiance": mg.solar_irradiance,
            "wind_speed": mg.wind_speed,
            "energy_price_utility_grid": mg.energy_price_utility_grid,
        }

        return info

