from get_data import load_data
from microgrid_env import MicrogridEnv


def main():
    solarirradiance, windspeed, rate_consumption_charge = load_data()
    print(solarirradiance)

    # grid = MicrogridEnv()


if __name__ == "__main__":
    main()



