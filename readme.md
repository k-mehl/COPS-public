# COPS Simulation

Requirements:
- Python 2.7 (required by SUMO)
- SUMO 0.25.0 or later

Start the simulation with e.g.
python runner.py 20 10
(this will create 20 available parking spaces and 10 searching vehicles).

Cooperative routing can be switched on by adding 'coop':
python runner.py 20 10 coop
(currently only works if all arguments are given)