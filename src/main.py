import pandas as pd
import numpy as np
import os

def import_data():
    # Read the solar irradiance and wind speed data from file
    # Read the rate of consumption charge date from file
    file_SolarIrradiance = "../data/SolarIrradiance.csv"
    file_WindSpeed = "../data/WindSpeed.csv"
    file_rateConsumptionCharge = "../data/rate_consumption_charge.csv"

    # Read the solar irradiance
    data_solar = pd.read_csv(file_SolarIrradiance)
    solarirradiance = np.array(data_solar.iloc[:, 3])
    # Solar irradiance measured by MegaWatt / km^2

    # Read the wind speed
    data_wind = pd.read_csv(file_WindSpeed)
    windspeed = 3.6 * np.array(data_wind.iloc[:, 3])
    # Wind speed measured by km/h = 1/3.6 m/s

    # Read the rate of consumption charge
    data_rate_consumption_charge = pd.read_csv(file_rateConsumptionCharge)
    rate_consumption_charge = np.array(data_rate_consumption_charge.iloc[:, 4])
    # Rate of consumption charge measured by 10^4 $/ MegaWatt = 10 $/kWh

    print(windspeed[0])


def main():
    import_data()

if __name__ == "__main__":
    main()



