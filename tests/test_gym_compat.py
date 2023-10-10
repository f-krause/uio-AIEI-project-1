from ray.rllib.utils.pre_checks.env import check_gym_environments
from ray.rllib.algorithms import AlgorithmConfig
from src.microgrid_env import MicrogridEnv
from gymnasium.spaces import Box
import numpy as np

def test_no_throw_reset():
  dummy_data_dict = {"energy_demand": [1,2,3], 
                     "solar_irradiance": [.4,.4,.4],
                     "wind_speed": [.3,.4,1.5], 
                     "rate_consumption_charge": [.1,.1,.3]}
  env = MicrogridEnv(dummy_data_dict)
  env.reset()


def test_env_compatibility():
  dummy_data_dict = {"energy_demand": [1,2,3], 
                     "solar_irradiance": [.4,.4,.4],
                     "wind_speed": [.3,.4,1.5], 
                     "rate_consumption_charge": [.1,.1,.3]}
  env = MicrogridEnv(dummy_data_dict)
  config = AlgorithmConfig()
  
  # RLlib requires environments to adhere to the "modern" gym environments. This
  # can be checked via the `check_gym_environments` function, which raises an
  # exception if the environment is not compatible.
  check_gym_environments(env, config)

def test_gym_box():
  b = Box(0,1)
  assert b.contains(np.array([.5], dtype="float32"))