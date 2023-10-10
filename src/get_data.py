import pandas as pd
import numpy as np
import os


# NOTE: We assume here that all time series have the identical starting point and no NAs

def get_energy_demand_data(k=10, region="CA"):
    data_path = "data/residential_load_data_base"
    files = os.listdir(data_path)
    files_sample = [file for file in files if file.startswith(f"USA_{region}")]
    if len(files_sample) < k:
        print("WARNING: Not enough data samples found! Either decrease k or change region")

    household_demand = []
    for file in files_sample[:k]:
        df = pd.read_csv(data_path + "/" + file)
        household_demand.append(df['Electricity:Facility [kW](Hourly)'])
    aggr_household_demand = np.array(household_demand).sum(axis=0)
    aggr_household_demand = aggr_household_demand[:-120]  # Drop 5 days bc other data sources lack these days

    return aggr_household_demand


def get_environment_data():
    # Read the solar irradiance and wind speed data from file
    # Read the rate of consumption charge date from file
    file_SolarIrradiance = "data/SolarIrradiance.csv"
    file_WindSpeed = "data/WindSpeed.csv"
    file_rateConsumptionCharge = "data/rate_consumption_charge.csv"

    # Read the solar irradiance
    data_solar = pd.read_csv(file_SolarIrradiance)
    solarirradiance = np.array(data_solar["Avg Global Horizontal [W/m^2]"])
    # Solar irradiance measured by MegaWatt / km^2

    # Read the wind speed
    data_wind = pd.read_csv(file_WindSpeed)
    windspeed = 3.6 * np.array(data_wind["Wind Speed  "])
    windspeed = windspeed[:-2]  # Drop last two faulty entries
    # Wind speed measured by km/h = 1/3.6 m/s

    # Read the rate of consumption charge
    data_rate_consumption_charge = pd.read_csv(file_rateConsumptionCharge)
    rate_consumption_charge = np.array(data_rate_consumption_charge["Grid Elecricity Price（$/kWh）"])
    # Rate of consumption charge measured by 10^4 $/ MegaWatt = 10 $/kWh

    return solarirradiance, windspeed, rate_consumption_charge


def get_data_dict(k=10, region="CA"):
    solar_irradiance, wind_speed, rate_consumption_charge = get_environment_data()
    energy_demand = get_energy_demand_data(k=k, region=region)

    if not energy_demand.shape[0] == solar_irradiance.shape[0] == wind_speed.shape[0] == rate_consumption_charge.shape[0]:
        print("Household demand:", energy_demand.shape[0])
        print("SolarIrradiance.csv:", solar_irradiance.shape[0])
        print("WindSpeed.csv", wind_speed.shape[0])
        print("rate_consumption_charge.csv:", rate_consumption_charge.shape[0])
        raise Exception("Loaded data is of unequal length!")

    return {"energy_demand": energy_demand,
            "solar_irradiance": solar_irradiance,
            "wind_speed": wind_speed,
            "rate_consumption_charge": rate_consumption_charge}