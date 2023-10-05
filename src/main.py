from get_data import get_data_dict
from microgrid_env import MicrogridEnv


def main():
    data_dict = get_data_dict()

    grid = MicrogridEnv()
    # Print some random stuff for testing
    print("GridEnv observation:", grid.get_observation())
    print("Cost of epoch:", grid.microgrid.cost_of_epoch())
    print("--------------")
    print(grid.microgrid.print_microgrid())


if __name__ == "__main__":
    main()



