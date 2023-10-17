import pandas as pd
import numpy as np
import os


# NOTE: We assume here that all time series have the identical starting point and no NAs

def get_energy_demand_data(k=25, region="CA"):
    if isinstance(region, list):
        region = tuple(region)
    if isinstance(region, tuple):
        region = tuple(f"USA_{r}" for r in region)
    else:
        region = f"USA_{region}"

    data_path = "data/residential_load_data_base"
    files = os.listdir(data_path)

    files_sample = [file for file in files if file.startswith(region)]
    
    household_demand = []
    for file in files_sample:
        df = pd.read_csv(data_path + "/" + file)
        if df['Electricity:Facility [kW](Hourly)'].shape[0] >= 8640:
            household_demand.append(df['Electricity:Facility [kW](Hourly)'])

    household_demand = household_demand[:k]
    if len(household_demand) < k:
        raise Exception(f"WARNING: Found only {len(household_demand)} < {k} households. Either decrease k or change "
                        f"region(s)")

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
    rate_consumption_charge *= 10  # increasing energy buying price by factor 10 to make more plausible
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
    
    data_dict = {"energy_demand": energy_demand,
                "solar_irradiance": solar_irradiance,
                "wind_speed": wind_speed,
                "rate_consumption_charge": rate_consumption_charge}
        
    return data_dict


def get_test_dict(k=10, region="CA", sample_size=800, seed=None):
    """Create artificial test data"""
    solar_irradiance, wind_speed, rate_consumption_charge = get_environment_data()
    energy_demand = get_energy_demand_data(k=k, region=region)
    
    # Set seed for reproducibility
    if seed:
        np.random.seed(seed)
    
    # Sample 800 random indices
    random_indices = np.random.choice(len(energy_demand), size=sample_size, replace=False)

    # Sample randomly from train data + random variation
    test_dict = {
        "energy_demand": energy_demand[random_indices] * np.random.normal(loc=1, scale=0.1, size=sample_size),
        "solar_irradiance": solar_irradiance[random_indices] * np.random.normal(loc=1, scale=0.1, size=sample_size),
        "wind_speed": wind_speed[random_indices] * np.random.normal(loc=1, scale=0.1, size=sample_size),
        "rate_consumption_charge": rate_consumption_charge[random_indices]
    }
    return test_dict
