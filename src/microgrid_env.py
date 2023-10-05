import gym
from gym import spaces
import pandas as pd

from params import *
from microgrid import Microgrid


class MicrogridEnv(gym.Env):
    def __init__(self, env_df):
        # Define the action and observation spaces
        self.action_space = spaces.Dict({
            "adjusting status": spaces.MultiBinary(3), # {0,1}^3
            "solar": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "wind": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "generator": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "purchased": spaces.Box(0, np.inf, shape=(2,), dtype=float),
            "discharged": spaces.Box(0, np.inf, dtype=float),
        })
        self.observation_space = spaces.Dict(
            {
                "solar": spaces.Box(0, np.inf, dtype=float),
                "wind": spaces.Box(0, np.inf, dtype=float),
                "electricity price": spaces.Box(0, np.inf, dtype=float),
                "load": spaces.Box(0, np.inf, dtype=float),
                "battery": spaces.Box(soc_min, soc_max, dtype=float),
            }
        )
        # Initialize your Microgrid
        self.microgrid = Microgrid()
        self.env_df = env_df
        self.step_count = 0

    def reset(self, **kwargs):
        self.step_count = 0
        # Reset the Microgrid to its initial state
        self.microgrid = Microgrid()
        # Return the initial observation
        return self.get_observation(), None # TODO: replace None with environment info

    def update_environment(self):
        current_row = self.env_df.iloc[self.step_count]
        self.microgrid.solar_irradiance = current_row["Solar Irradiance"]
        self.microgrid.wind_speed = current_row["Wind Speed"]
        self.microgrid.energy_price_utility_grid = current_row["Grid Electricity Price"]
        # TODO: the load should probably influence the environment
        # = current_row["warehouse 1"] + current_row["small hotel 1"]
        
    def step(self, action):
        # Update the Microgrid's state and compute the reward
        self.update_environment()

        # Execute the chosen action on the Microgrid
        self.microgrid.actions_adjusting_status = Microgrid.get_actions_dict(action["adjusting status"], actions=["s", "w", "g"])
        self.microgrid.actions_solar = Microgrid.get_actions_dict(action["solar"])
        self.microgrid.actions_wind = Microgrid.get_actions_dict(action["wind"])
        self.microgrid.actions_generator = Microgrid.get_actions_dict(action["generator"])
        self.microgrid.actions_purchased = action["purchased"]
        self.microgrid.actions_discharged = action["discharged"][0]

        self.microgrid.transition()

        # Calculate the reward based on your cost reduction goal
        reward = self.compute_reward()

        # Check if the episode is done (you can define a termination condition here)
        self.step_count += 1
        done = self.step_count >= len(self.env_df)  # You need to define when an episode is done

        # Return the next observation, reward, done flag, and any additional info
        return self.get_observation(), reward, done, {}, None # TODO: decide whether we should return env info instead of None

    def get_observation(self):
        # Extract relevant information from the Microgrid's state and return it as an observation
        observation = [
            self.microgrid.working_status["s"],
            self.microgrid.working_status["w"],
            self.microgrid.working_status["g"],
            self.microgrid.soc,
            self.microgrid.solar_irradiance,
            self.microgrid.wind_speed,
            # Add other relevant variables here
        ]
        return np.array(observation)

    def compute_reward(self):
        return self.microgrid.cost_of_epoch()

    def render(self, mode='human'):
        pass
