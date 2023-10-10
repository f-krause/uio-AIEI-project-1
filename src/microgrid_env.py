import gymnasium as gym
from gymnasium import spaces
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

        # Define the action and observation spaces
        self.action_space = spaces.Dict({
            # we have to build our own distribution for "adjusting status" since
            # * MultiBinary is not supported by RLlib
            # * MultiDiscrete is broken in the current release (see readme)
            #"adjusting status": spaces.MultiBinary(3), # {0,1}^3, spaces.MultiDiscrete(2 * np.ones(3, dtype=np.int64)),
            # therefore, we spam in multiple binary actions (=Discrete(2)), one
            # for each adjusting status
            **{"adjusting status %d" % i: spaces.Discrete(2) for i in range(3)},
            "solar": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "wind": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "generator": spaces.Box(0, np.inf, shape=(3,), dtype=float),
            "purchased": spaces.Box(0, np.inf, shape=(2,), dtype=float),
            "discharged": spaces.Box(0, np.inf, dtype=float),
        })
        # the restrictions for the observation space are picked based on the
        # values occurring in the dataset
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

        # load environment from first data point such that the environment is 
        # never in a state with "weird" (aka wrong/default) values.
        self.microgrid.update_environment(self.data_dict, self.step_count)
        self.step_count += 1
        assert self.step_count <= len(self.data_dict["wind_speed"]), "not enough data"

        # Return the initial observation
        info = {} # TODO: replace None with environment info
        return self.get_observation(), info

    def step(self, action):
        # Execute the chosen action on the Microgrid
        self.microgrid.transition(action, self.data_dict, self.step_count)

        # Calculate the reward based on your cost reduction goal
        reward = self.compute_reward()

        # Check if the episode is done (you can define a termination condition here)
        self.step_count += 1
        max_epochs = len(self.data_dict["wind_speed"]) # this is NOT len(self.data_dict), this would return len(self.data_dict.keys())
        done = self.step_count >= max_epochs  # You need to define when an episode is done

        # Return the next observation, reward, done flag, and any additional info
        truncated = False # From documentation: "This flag should indicate, whether the episode was terminated prematurely due to some time constraint or other kind of horizon setting."
        return self.get_observation(), reward, done, truncated, {}  # TODO: decide whether we should return env info instead of None

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
            "observations contain negative values"
        )
        assert all(v < np.inf for v in res.values()), (
            "observations contain degenerate values"
        )

        return res

    def compute_reward(self):
        return self.microgrid.cost_of_epoch()

    def render(self, mode='human'):
        pass
