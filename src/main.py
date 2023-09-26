from get_data import load_data
from microgrid_env import MicrogridEnv


def main():
    solarirradiance, windspeed, rate_consumption_charge = load_data()

    grid = MicrogridEnv()
    # Print some random stuff for testing
    print(grid.get_observation())
    print(grid.microgrid.print_microgrid())


if __name__ == "__main__":
    main()



