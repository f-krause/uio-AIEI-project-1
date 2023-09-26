from get_data import load_data
from microgrid import Microgrid, MicrogridEnv


def main():
    solarirradiance, windspeed, rate_consumption_charge = load_data()
    print(solarirradiance)

    grid = Microgrid()


if __name__ == "__main__":
    main()



