# COPS Simulation

Requirements:
- Python 2.7 (required by SUMO)
- SUMO 0.25.0 or later

Start the simulation with e.g.
python runner.py 20 10
(this will create 20 available parking spaces and 10 searching vehicles).

Cooperative routing can be switched on by specifying a fraction of
cooperative drivers:
python runner.py 20 10 0.6
(this will on average set 60 percent of drivers to select the cooperative route)
(currently only works if all arguments are given).

To start multiple runs without GUI, the wrapper module can be used:
python wrapper.py 100 20 10 0.6
(now the first number specifies the number of runs)
(currently only works if all arguments are given)