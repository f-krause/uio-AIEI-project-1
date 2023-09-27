import gym
from gym import spaces

from params import *
from microgrid import Microgrid


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
                "battery": spaces.Box(soc_min, soc_max, dtype=float),
            }
        )
        # Initialize your Microgrid
        self.microgrid = Microgrid()

    def reset(self, **kwargs):
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
        return self.microgrid.energy_consumption() * sell_back_price + self.microgrid.operational_cost() - self.microgrid.sell_back_reward()

    def render(self, mode='human'):
        pass
