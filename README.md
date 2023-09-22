# in5460-mex1

Mandatory exercise 1 for Artificial Intelligence for Energy Informatics.

[**Assignment**](https://drive.google.com/file/d/1pIJbfPNUTzSqmtWR1NDfasgdQB9se5Tb/view) | Deadline 17.10.2023 kl 23:59

## Questions

1. Why are the tables `rate_consumption_charge.csv` and `SolarIrradiance.csv` the same?
    * Maybe we need to extract different columns from the same table?
2. Why is there an additional column in the `WindSpeed.csv` dataset that maps any number `x.y` to `x.5`?
3. What should be take from the big dataset? I.e. the load data?
4. Where can we find the $\delta_{omc}$ values for the different generation methods?
    * Maybe they are the $\gamma_{omc}$ in the tables.
5. Where can we find how to calculate $E_g(t)$ and $E_b(t)$? (For $E_w(t)$ and $E_s(t)$ the formulas are given, are we missing something?)

## Setup

```bash
conda create --name ai4ei python=3.11
conda activate ai4ei
conda install -c conda-forge jupyter numpy pandas seaborn matplotlib
```

## Scenario

* **State:** energy price on marketcurrent demand, current energy production capacity (solar/wind)
* **Reward:** combination of costs and money obtained by utility grid
    * overall reward: $C(t)=E_u(t)+O_m(t)-S_u(t)$
    * energy purchased from grid $E_u(t)=E(t)\cdot P_g(t)$
    * microgrid operational cost $O_m(t)$
    * reward of energy sold back $S_u(t)$
    * long term goal: $\min\sum_{t=0}^\infty C(t)$
* **Actions** at each point in time: 
    1. support the energy load (buy)
    2. sell back to utility grid (sell)
    3. store energy in the battery (do nothing)

## Datasets

* **[SolarIrradiance.csv:](https://drive.google.com/file/d/18vF2dbKmx-DfytXADhwPhE6PmLTw5bvR/view)** According to the provided code, we should only extract the `[W/m^2]` column from this dataset
* **[rate_consumption_charge.csv/electricity price:](https://drive.google.com/file/d/1OzMEDDsbBO51AyzTs-fNusc-qvVQrI-U/view)** The provided code extracts the `Grid Electricity Price` (weird formatting: `Grid Elecricity Price锛?/kWh锛?2016`, could be `$/kWh`)
* **[WindSpeed.csv:](https://drive.google.com/file/d/101OdwwF1cJIzshD-g0jqydmlqlTJ5HJg/view)** The provided code takes only column at index 3, which are the weird rounded values

## RL software

* **[pymgrid](https://github.com/Total-RD/pymgrid)** is discontinued, we looked at its successor python-microgrid
* **[python-microgrid](https://github.com/ahalev/python-microgrid/tree/master)** can be used "to generate and simulate a large number of microgrids"; according to their [data section](https://github.com/ahalev/python-microgrid/tree/master#data), they als use OpenEI load data and PV datasets ("Data in pymgrid are based on TMY3 (data based on representative weather)", this might be EnergyPlus)
* [**easygrid:**](https://github.com/YannBerthelot/easygrid/tree/main) a simple version based on [OpenAI gym](https://github.com/openai/gym), maybe we should use this to get started