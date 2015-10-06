# Intro

Basic simulation, at the moment only works in a grid where x and y positions
are satisfying ``x % 2 == 0`` or ``y % 2 == 0``.
Currently one driver informs the other about informs the other on the route
he plans to traverse, hence the other driver plans his route according to the
route of the one who was "first" to enter are. 

There is no graph underlying this implementation, hence for more generic
implementation more work is needed.

To clone the project use command:  
``
git clone https://scm.in.tu-clausthal.de/git/parking
``

To resolve the certificate problems follow this [link](https://scm.in.tu-clausthal.de/projects/redmine-git-svn-help/wiki/Resolve_SSL_certificate_error_with_Git).

To run the simulation Matplotlib is necessary. Running ``simulation.py`` will
give the basic impression of simulation.

# TODO
[ ] Graph  
[ ] Conversion of graph to adjacency matrix  
[ ] Shortest paths calculation on adjacency matrix  
[ ] Car following model (when there are many drivers)  
[ ] OSM import  
[ ] Conversion of OSM to our Graph structure  
