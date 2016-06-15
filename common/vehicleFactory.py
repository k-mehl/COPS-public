import random
import sumolib
import os


def generatePsvDemand(p_num, p_resourcedir="", p_routefile="reroute.rou.xml",
                      p_edgefile="reroute.edg.xml"):
    """ Generate a random demand of vehicles for the parking space search and
    create the corresponding XML file

    Args:
        p_num (int): Number of vehicles
        p_resourcedir (str): Base path name for SUMO related resources
        p_edgefile (str):  Filename to read edges, default: reroute.edg.xml
        p_routefile (str): Filename to write routes, default: reroute.rou.xml
    """
    # create seperate lists for possible origin or destination edges
    origins = []
    destinations = []
    # parse edges XML file for all network edges
    for edge in sumolib.output.parse(os.path.join(p_resourcedir, p_edgefile),
                                     ['edge']):
        # if the edge ID contains "entry": use it as origin only;
        # otherwise: use it as destination only
        if "entry" in str(edge.id):
            origins.append(str(edge.id))
        else:
            destinations.append(str(edge.id))

    # open routes XML file for write access
    f = open(os.path.join(p_resourcedir, p_routefile), 'w')

    # define tab as 4 spaces
    tab = "    "
    # base string for vehicle trip data
    veh = '<trip id="veh{0}" depart="0" from="{1}" to="{2}" type="Car" ' + \
            'color="0,1,0"/>\n'

    # write header
    f.write("<vehicles>\n")
    # write definitions of 'Car' type
    f.write(tab + '<vType accel="1.0" decel="5.0" id="Car" length="4.0"' + \
            ' maxSpeed="100.0" sigma="0.0"/>\n')
    # for each vehicle, select random O/D from possible origins/destinations
    # and write trip info to XML file
    for i in range(p_num):
        origin = random.choice(origins)
        dest = random.choice(destinations)
        f.write(tab + veh.format(i, origin, dest))
    # write footer
    f.write("</vehicles>")
    # close the XML file
    f.close()
