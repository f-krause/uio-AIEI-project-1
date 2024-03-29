import numpy as np


# Parameters of the model

cutin_windspeed = 3 * 3.6
# the cut-in windspeed (km/h = 1/3.6 m/s), v^ci
cutoff_windspeed = 11 * 3.6
# the cut-off windspeed (km/h = 1/3.6 m/s), v^co
rated_windspeed = 7 * 3.6
# the rated windspeed (km/h = 1/3.6 m/s), v^r
charging_discharging_efficiency = 0.95
# the charging - discharging efficiency, eta
# rate_battery_discharge = 2 / 1000  # not used
# the rate for discharging the battery (MegaWatt), b
unit_operational_cost_solar = 0.15 # / 10
# the unit operational and maintenance cost for generating power
# from solar PV (10^4 $/MegaWattHour = 10 $/kWHour), r_omc ^s
unit_operational_cost_wind = 0.085 # / 10
# the unit operational and maintenance cost for generating power
# from wind turbine (10^4 $/MegaWattHour = 10 $/kWHour), r_omc ^w
unit_operational_cost_generator = 0.55 # / 10
# the unit operational and maintenance cost for generating power
# from generator (10^4 $/MegaWattHour = 10 $/kWHour), r_omc ^g
unit_operational_cost_battery = 0.95 # / 10
# the unit operational and maintenance cost for battery storage system
# per unit charging / discharging cycle (10^4 $/MegaWattHour = 10 $/kWHour),
# r_omc ^b

# MANUALLY ADDED
sell_back_energy_price = 0.2
# Price of energy sold to utility grid. According to instructions fixed at  0.2 $/kWh

capacity_battery_storage = 300  # original: 300 / 1000
# the capacity of the battery storage system (MegaWatt Hour = 1000 kWHour), e
soc_max = 0.95 * capacity_battery_storage
# the maximum state of charge of the battery system
soc_min = 0.05 * capacity_battery_storage
# the minimum state of charge of the battery system
area_solarPV = 1400  # original: / (1000 * 1000)
# the area of the solar PV system (km^2 = 1000*1000 m^2), a
efficiency_solarPV = 0.2
# the efficiency of the solar PV system, delta
density_of_air = 1.225
# calculate the rated power of the wind turbine,
# density of air (10^6 kg/km^3 = 1 kg/m^3), rho
radius_wind_turbine_blade = 25 / 1000
# calculate the rated power of the wind turbine,
# radius of the wind turbine blade (km = 1000 m), r
average_wind_speed = 3.952 * 3.6
# calculate the rated power of the wind turbine,
# average wind speed (km/h = 1/3.6 m/s), v_avg (from the windspeed table)
power_coefficient = 0.593
# calculate the rated power of the wind turbine, power coefficient, theta
gearbox_transmission_efficiency = 0.95
# calculate the rated power of the wind turbine,
# gearbox transmission efficiency, eta_t
electrical_generator_efficiency = 0.95
# calculate the rated power of the wind turbine,
# electrical generator efficiency, eta_g
rated_power_wind_turbine_original = 0.5 * density_of_air * np.pi * radius_wind_turbine_blade * \
                                    radius_wind_turbine_blade * average_wind_speed * average_wind_speed * \
                                    average_wind_speed * power_coefficient * gearbox_transmission_efficiency * \
                                    electrical_generator_efficiency
rated_power_wind_turbine = rated_power_wind_turbine_original / (3.6 * 3.6 * 3.6)
# the rated power of the wind turbine, RP_w (MegaWatt = 10^6 W),
# with the radius_wind_turbine_blade measured in km = 10^3m,
# average wind speed measured in km/hour = 3.6 m/s,
# RP_w will be calculated as RP_w_numerical
# then RP_w in MegaWatt = (1 kg/m^3) * (10^3 m) * (10^3 m) * (3.6 m/s) * (3.6 m/s) * (3.6 m/s) * RP_w_numerical
# = 3.6^3 * 10^6 RP_w_numerical W = 3.6^3 RP_w_numerical MegaWatt
number_windturbine = 1
# the number of wind turbine in the onsite generation system, N_w
number_generators = 1
# the number of generators, n_g
rated_output_power_generator = 600  # original: 60 / 1000 before
# the rated output power of the generator in kWh, G_p

# MANUALLY ADDED
delta_t = 1
# time period in hours
blackout_cost = 300
# cost of a blackout, i.e. if production is less than demand
