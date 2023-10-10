# in5460-mex1

Mandatory exercise 1 for Artificial Intelligence for Energy Informatics.

[**Assignment**](https://drive.google.com/file/d/1pIJbfPNUTzSqmtWR1NDfasgdQB9se5Tb/view) | Deadline 17.10.2023 kl 23:59

## To-dos

* Look at datasets (ranges, time ranges)
* Copy and look at given code snippets, maybe run the code
* How to put everything at easygrid?
* `train` function
* How can we create reasonable train/val/test splits?
* (Format dates in csv's to datetime)

## Questions

1. What should be take from the big dataset? I.e. the load data? Which dataset should we use for gathering the residential load data? There are many columns in the household load data, like `Electricity:Facility [kW](Hourly)`, `Fans:Electricity [kW](Hourly)`, or `Cooling:Electricity [kW](Hourly)`. Which columns of the load data should we use? Should we use the overall consumption of the household?
    * Felix' dataset is good
    * just `Electricity:Facility [kW](Hourly)`
    * 25 households: sum up overall electricity consumption
2. Why do the time ranges of the datasets differ so much? (for instance: year 2004 for YM3, and 2016 for solar irradiance) Should we just assume that the yearly data is the same? Why are the solar/wind/rate consumption datasets only for half of a year? (around 4320 hours vs 365*24=8760?) And if yes, when in the year do they start?
    * TA will make sure that we have a full year for the small/too short datasets
    * load another year is fine
    * one column was shifted to the top
3. Where can we find how to calculate $E_g(t)$ and $E_b(t)$? (For $E_w(t)$ and $E_s(t)$ the formulas are given, are we missing something?)
    * should be in the code
4. Why are the tables `rate_consumption_charge.csv` and `SolarIrradiance.csv` the same?
    * Maybe we need to extract different columns from the same table? YES
5. Why is there an additional column in the `WindSpeed.csv` dataset that maps any number `x.y` to `x.5`?
    * TA will write an email about that and update the assignment
6. Where can we find the $\delta_{omc}$ values for the different generation methods?
    * Maybe they are the $\gamma_{omc}$ in the tables. 

* any RL is fine
* pay attention to numbers: GW vs MW
* TA will provide information about `Delta_t`


## Run module
```shell
python ./src/main.py
```


## Environment setup

With conda
```bash
conda create --name ai4ei python=3.11
conda activate ai4ei
conda install -c conda-forge jupyter numpy pandas seaborn matplotlib
pip install gym
```

With venv
```shell
python -m venv venv
```

```shell
source venv/bin/activate
```

```shell
pip install -r requirements.txt
```

Install project to environment, which works both with conda and pip:

```bash
pip install -e .
```

This is required to run training with rllib.

## Scenario

* **State:** energy price on market, current demand, current energy production capacity (solar/wind), current battery charge status
* **Reward:** combination of costs and money obtained by utility grid
    * overall "reward" (to be minimized): $C(t)=E_u(t)+O_m(t)-S_u(t)$, with:
      * $E_u(t)=E(t)\cdot P_g(t)$: energy purchased from grid 
      * $O_m(t)$: microgrid operational cost 
      * $S_u(t)$: reward of energy sold back 
    * long term goal: $\min\sum_{t=0}^\infty C(t)$
* **Actions** at each point in time (FIXME AREN'T THERE MORE?): 
    1. support the energy load (buy)
    2. sell back to utility grid (sell)
    3. store energy in the battery (do nothing)


## Conventions
* The main unit used for energy is kWh (prices need to be adapted accordingly!)


## Datasets

* **[SolarIrradiance.csv:](https://drive.google.com/file/d/1SUjtybPtUzwSEDQoqXbMNijEeDi8QF8m/view)** According to the provided code, we should only extract the `[W/m^2]` column from this dataset
* **[rate_consumption_charge.csv/electricity price:](https://drive.google.com/file/d/1uxM9TC401TBwjcdxe3i7TAxSo9tPNWi1/view)** The provided code extracts the `Grid Electricity Price` (weird formatting: `Grid Elecricity Price锛?/kWh锛?2016`, could be `$/kWh`)
* **[WindSpeed.csv:](https://drive.google.com/file/d/1X87VRm88-Tp2cs9zjmOB0R6wTxJl8QBf/view)** The provided code takes only column at index 3, which are the weird rounded values
* **[Residential load profiles](https://data.openei.org/files/153/RESIDENTIAL_LOAD_DATA_E_PLUS_OUTPUT.zip)**: Check out data source [here](https://data.openei.org/submissions/153)


## RL software

* **[pymgrid](https://github.com/Total-RD/pymgrid)** is discontinued, we looked at its successor python-microgrid
* **[python-microgrid](https://github.com/ahalev/python-microgrid/tree/master)** can be used "to generate and simulate a large number of microgrids"; according to their [data section](https://github.com/ahalev/python-microgrid/tree/master#data), they als use OpenEI load data and PV datasets ("Data in pymgrid are based on TMY3 (data based on representative weather)", this might be EnergyPlus)
* **[easygrid:](https://github.com/YannBerthelot/easygrid/tree/main)** a simple version based on [OpenAI gym](https://github.com/openai/gym), maybe we should use this to get started
* **[example tutorial](https://github.com/Wenuka/RL_for_energy_tutorial)** an example project that is very similar to ours
* **[gym environments](https://www.gymlibrary.dev//content/environment_creation/#)** tutorial on how to create a RL environment
* **[Intro to RLlib](https://medium.com/distributed-computing-with-ray/intro-to-rllib-example-environments-3a113f532c70)**
    * “PPO” means Proximal Policy Optimization, which is the method we’ll use in RLlib for reinforcement learning. That allows for minibatch updates to optimize the training process. For more details see the [RLlib documentation about PPO](https://docs.ray.io/en/latest/rllib-algorithms.html?highlight=ppo#proximal-policy-optimization-ppo), as well as the original paper [“Proximal Policy Optimization Algorithms” by Schulman, et al.](https://arxiv.org/abs/1707.06347), which describes the benefits of PPO as “a favorable balance between sample complexity, simplicity, and wall-time.”
    * We shouldn't use MultiDiscrete distributions in our actions space since [they are broken in ray](https://github.com/ray-project/ray/issues/39421).