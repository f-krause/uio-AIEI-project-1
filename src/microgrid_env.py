import gym
from gym import spaces
import pandas as pd

from src.params import *
from src.microgrid import Microgrid


class MicrogridEnv(gym.Env):
    def __init__(self, data_dict):
        # Define the action and observation spaces
        # Stable Baselines3 has no spaces.Dict for actions. We resolve it by flattening the dict space into a box space.
        self.action_space = spaces.Box(low=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                                       high=np.array(
                                           [1, 1, 1, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000, 100000,
                                            100000]),
                                       dtype=np.float32)
        self.observation_space = spaces.Dict(
            {
                # solar irradiance in dataset is between 0 and a little over
                # 1000.
                "solar": spaces.Box(0., 10000., dtype=float),
                # wind speed in dataset is between 0 and 60, 100 should be
                # plenty of headroom
                "wind": spaces.Box(0, 100., dtype=float),
                # the electricity in the dataset is in fractions of currencies
                "electricity price": spaces.Box(0, 10., dtype=float),
                # one house has a peak load of roughly 150 in the dataset, so
                # using a lot of houses could yield a potential load of this
                # upper bound
                "energy_demand": spaces.Box(0, 100000., dtype=float),
                "battery": spaces.Box(soc_min, soc_max, dtype=float),
            }
        )
        # Initialize your Microgrid
        self.microgrid = Microgrid()
        self.step_count = 0
        self.data_dict = data_dict # hourly environment data

    def reset(self, **kwargs):
        self.step_count = 0
        # Reset the Microgrid to its initial state
        self.microgrid = Microgrid()
        # Return the initial observation
        return self.get_observation()

    def step(self, action):
        # Split the flattened action into sub-actions
        adjusting_status = action[:3]
        # Ensure that adjusting_status values are either 0 or 1
        adjusting_status = np.round(adjusting_status).astype(int)
        action_dict = {
            "adjusting status": adjusting_status,
            "solar": action[3:6],
            "wind": action[6:9],
            "generator": action[9:12],
            "purchased": action[12:14],
            "discharged": [action[14]]
        }

        # Execute the chosen action on the Microgrid
        self.microgrid.transition(action_dict, self.data_dict, self.step_count)

        # Calculate the reward based on your cost reduction goal
        reward = self.compute_reward()

        # Check if the episode is done (you can define a termination condition here)
        self.step_count += 1
        max_epochs = len(self.data_dict["wind_speed"]) # this is NOT len(self.data_dict), this would return len(self.data_dict.keys())
        done = self.step_count >= max_epochs  # You need to define when an episode is done

        # Return the next observation, reward, done flag, and any additional info
        return self.get_observation(), reward, done, {}

    def get_observation(self):
        # Extract relevant information from the Microgrid's state and return it as an observation (environment state)
        res = {k: np.array([v]) for k, v in {
            "solar": self.microgrid.solar_irradiance,
            "wind": self.microgrid.wind_speed,
            "electricity price": self.microgrid.energy_price_utility_grid,
            "energy_demand": self.microgrid.energy_demand,
            "battery": self.microgrid.soc,
        }.items()}

        # trivial post-condition check for outgoing values (this test strongly
        # suggests that the environment is not in an invalid state.)
        assert all(v >= 0. for v in res.values()), (
            res.values(),
            "observations contain negative values"
        )
        assert all(v < np.inf for v in res.values()), (
            res.values(),
            "observations contain degenerate values"
        )

        return res

    def compute_reward(self):
        return self.microgrid.cost_of_epoch()

    def render(self, mode='human'):
        mg = self.microgrid

        info = {
            "reward": self.compute_reward(),
            "operational_cost": mg.operational_cost(),
            "sell_back_reward": mg.sell_back_reward(),
            "energy_demand": mg.energy_demand,
            "energy_load": mg.energy_load(),
            
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
            
            "working_status": mg.working_status,
            "soc": mg.soc,
            "solar_irradiance": mg.solar_irradiance,
            "wind_speed": mg.wind_speed,
            "energy_price_utility_grid": mg.energy_price_utility_grid,   
        }

        return info

