from __future__ import print_function
import json
import sys
import os
import gzip

# TODO: add run configuration, i.e. occupancy of parking spaces.
# TODO: Generate for each run occupancy by POIid if config doesn't match, i.e
# too few/many runs,parkingspaces configured,
# TODO: allow dot access to config dict members, it would clean up a lot of code
# TODO: look for common use patterns of config in other classes and create
# helper methods


class Configuration(object):

    def __init__(self, p_args, p_configdir):

        self._defaultconfig = {
            "simulation": {
                "forceroutefile": False,
                "routefile": "reroute.rou.xml",
                "resourcedir": "resources",
                "sumoport": 8873,
                "headless": True,
                "verbose": False,
                "runs": 10,
                "runconfiguration": "config.runs.json.gz",
                "resulttimestamped": False,
                "parkingspaces": {
                    "total": 400,
                    "free": 5,
                },
                "vehicles": 5,
                "coopratioPhase2": 1.0,
                "coopratioPhase3": 0.0,
                "mixed_traffic": {
                    "ratio": -1.0,
                    "coopPhase2": False,
                    "coopPhase3": False,
                    "coop_vehicles": -1,
                    "non_coop_vehicles": -1
                }
            },
            "vehicle": {
                "parking": {
                    "distance": {
                        "min": 12.0,
                        "max": 30.0,
                    },
                    "duration": 12.0,
                },
                "maxspeed": {
                    "phase1": 27.778,
                    "phase2": 8.333,
                    "phase3": 8.333,
                },
                "phase3randomprob": 0.1,
                "weights": {
                    "coop": {
                        "distance": 1,
                        "selfvisit": 2000,
                        "externalvisit": 2000,
                        "externalplanned": 100,
                    },
                    "noncoop": {
                        "distance": 1,
                        "selfvisit": 2000,
                        "externalvisit": 0,
                        "externalplanned": 0,
                    },
                },
            },
        }

        self._configuration = {}
        self._runconfiguration = {}

        self._configdir = p_configdir
        self._args = p_args

        # create fresh config.jason and dir if not exists
        if not os.path.isdir(self._configdir):
            os.mkdir(self._configdir)

        print("* checking whether {} exists".format(p_args.config))
        if not os.path.isfile(p_args.config):
            self._configuration = json.loads(json.dumps(self._defaultconfig))
            self._writeCfg(self._configuration, p_args.config)
        else:
            fp = open(p_args.config, 'r')
            self._configuration = json.load(fp)
            print("* loaded existing config {}".format(p_args.config))

        self._overrideConfig(p_args)
        self._sanitycheck()

        self._runcfgfilename = os.path.join(
                self._configdir,
                self._configuration["simulation"]["runconfiguration"])

        self._runconfiguration = self._readRunCfg(p_args)
        self._mixed_traffic_configuration = self._configuration["simulation"]["mixed_traffic"]

    def getCfg(self, p_key):
        """ Get configuration

        Args:
            p_key: the key to get the configuration out of dictionary
        Returns:
            dict: configuration for a given key
        """
        return self._configuration[p_key]

    def getRunCfg(self, p_key):
        """ Get a running configuration

        Args:
            p_key: the key to get the configuration out of dictionary
        Returns:
            dict: configuration for a given key
        """
        return self._runconfiguration.get(p_key)

    def getMixedTrafficCfg(self, p_key=None):
        '''
        get values of the mixed traffic configuration by key
        :param p_key: key of the config
        :return: value at config key
        '''
        return self._mixed_traffic_configuration[p_key]

    def _writeCfg(self, p_config, p_location, p_sort_keys=True, p_indent=4,
                  p_separators=(',', ' : ')):
        if sys.version_info > (3, ):
            fp = open(p_location, 'w')
        elif p_location.endswith(".gz"):
            fp = gzip.GzipFile(p_location, 'w')
        else:
            fp = open(p_location, mode="w")

        json.dump(p_config, fp, sort_keys=p_sort_keys, indent=p_indent,
                  separators=p_separators)
        fp.close()

    def _overrideConfig(self, p_args):
        """ Override values with provided argparse parameters

        Args:
            p_args (argparse object):
        """
        if p_args.parkingspaces is not None:
            self._configuration["simulation"]["parkingspaces"]["free"] = \
                    p_args.parkingspaces
        if p_args.psv is not None:
            self._configuration["simulation"]["vehicles"] = p_args.psv
        if p_args.coopratioPhase2 is not None:
            self._configuration["simulation"]["forcecooperationphasetwo"] = \
                    p_args.coopratioPhase2
        if p_args.coopratioPhase3 is not None:
            self._configuration["simulation"]["forcecooperationphasethree"] = \
                    p_args.coopratioPhase3
        if p_args.sumoport is not None:
            self._configuration["simulation"]["sumoport"] = p_args.sumoport
        if p_args.resourcedir is not None:
            self._configuration["simulation"]["resourcedir"] = \
                    p_args.resourcedir
        if p_args.runs is not None:
            self._configuration["simulation"]["runs"] = p_args.runs
        if p_args.runconfiguration is not None:
            self._configuration["simulation"]["runconfiguration"] = \
                    p_args.runconfiguration
        if p_args.headless:
            self._configuration["simulation"]["headless"] = True
        if p_args.gui:
            self._configuration["simulation"]["headless"] = False
        if p_args.verbose:
            self._configuration["simulation"]["verbose"] = True
        if p_args.resulttimestamped:
            self._configuration["simulation"]["resulttimestamped"] = True

        if p_args.mixed_traffic is not None:
            # split arguments
            mixed_traffic_args = p_args.mixed_traffic
            mixed_ratio, phase_2, phase_3 = self._convert_mixed_traffic_args(mixed_traffic_args)
            coop_vehicles = self._calculate_num_of_coop_vehicles(mixed_ratio,
                                                                 self._configuration["simulation"]["vehicles"])
            non_coop_vehicles = self._configuration["simulation"]["vehicles"] - coop_vehicles
            # set configuration with correct types
            self._configuration["simulation"]["mixed_traffic"]["ratio"] = mixed_ratio
            self._configuration["simulation"]["mixed_traffic"]["coopPhase2"] = phase_2
            self._configuration["simulation"]["mixed_traffic"]["coopPhase3"] = phase_3
            self._configuration["simulation"]["mixed_traffic"]["coop_vehicles"] = coop_vehicles
            self._configuration["simulation"]["mixed_traffic"]["non_coop_vehicles"] = non_coop_vehicles

    def _sanitycheck(self):
        """ Sanity checks of the config """
        # raise exception if gui mode requested with > 1 run
        sim_headless = self._configuration["simulation"]["headless"]
        sim_runs = self._configuration["simulation"]["runs"]
        if not sim_headless and sim_runs > 1:
            message = "Number of runs can't exceed 1, if run in GUI mode."
            raise BaseException(message)

        # raise exception if headless mode requested  AND number of parking
        # spaces < vehicles in the static case this produces an endless loop of
        # at least one vehicle searching for a free space.  In Gui mode this
        # behavior is acceptable
        sim_free_parkings = self._configuration["simulation"]["parkingspaces"]["free"]
        if sim_headless and sim_free_parkings < self._configuration["simulation"]["vehicles"]:
            message = ("Number of parking spaces must be at least equal to"
                       "number of vehicles, if run in headless mode.")
            raise BaseException(message)

        # raise an exception if provided basedir does not exist
        if not os.path.isdir(self._configuration["simulation"]["resourcedir"]):
            message = ("The provided directory {} does not exist for argument"
                       "--resourcedir").format(
                              self._configuration["simulation"]["resourcedir"])
            raise BaseException(message)

        self._sanity_check_mixed_traffic()

    def existRunCfg(self):
        return len(self._runconfiguration) > 0

    def isRunCfgOk(self, p_runid):
        """ Check running configuration

        Args:
            p_runid (int?): running ID
        Returns:
            bool: ...
        """
        sim_cfg = self._configuration["simulation"]
        # phase 1: check if runcfg for given runid exists
        if not self._runconfiguration.get(str(p_runid)):
            print("There exists no run configuration for runid {}.".format(p_runid))
            return False

        # phase 2: check for enough stored runs
        if len(self._runconfiguration) < sim_cfg["runs"]:
            print("/!\ Run config does not match simulation parameters. "
                  "Expecting {} runs, read {} runs from {} config instead. "
                  "".format(sim_cfg["runs"], len(self._runconfiguration),
                            self._runcfgfilename))
            return False

        # phase 3: check for enough available parkingspaces in each run (i.e.
        # #available parkingspaces >= #vehicles)
        # contains amount of runs with mismatching available parkingspaces
        tmp_vals = self._runconfiguration[str(p_runid)]["parkingspaces"].values()
        l_available = [v for v in tmp_vals if v["available"]]
        # l_available = filter(lambda v: v["available"],
        #                 self._runconfiguration[str(p_runid)]["parkingspaces"].values())

        if len(l_available) < sim_cfg["vehicles"]:
            print("/!\ Run config does not match simulation parameters. "
                  "Expecting at least {} available parking spaces due to {} "
                  "searching vehicles. Found only {} in run {}"
                  "".format(sim_cfg["parkingspaces"]["free"],
                            sim_cfg["vehicles"],
                            len(l_available),
                            p_runid))
            return False
        return True

    def _readRunCfg(self, p_args):
        print("* reading run cfg {}".format(self._runcfgfilename))
        if not os.path.isfile(self._runcfgfilename):
            return {}

        if sys.version_info > (3, ):
            fp = open(self._runcfgfilename, mode="r")
        elif self._runcfgfilename.endswith(".gz"):
            fp = gzip.GzipFile(self._runcfgfilename, 'r')
        else:
            fp = open(self._runcfgfilename, mode="r")

        l_runcfg = json.load(fp)

        fp.close()

        return l_runcfg

    def writeCfg(self):
        """ Write configuration """
        print("* writing configuration to {}".format(self._args.config))
        self._writeCfg(self._configuration, self._args.config)
        print("  -> done.")

    def writeRunCfg(self):
        """ Write run configuration """
        print("* writing run configuration to {}".format(self._runcfgfilename))
        self._writeCfg(self._runconfiguration,
                       self._runcfgfilename,
                       p_sort_keys=True,
                       p_indent=None,
                       p_separators=(',', ':'))
        print("  -> done.")

    def updateRunCfgParkingspaces(self, p_run, p_parkingspaces):
        """ Update parking spaces in run configuration """
        l_run = str(p_run)
        if not self._runconfiguration.get(l_run):
            self._runconfiguration[l_run] = {}
        self._runconfiguration[l_run]["parkingspaces"] = {}

        for i_parkingspace in p_parkingspaces:
            self._runconfiguration[l_run]["parkingspaces"][str(i_parkingspace.name)] = {
                "name": i_parkingspace.name,
                "available": i_parkingspace.available,
                "edgeID": i_parkingspace.edgeID,
                "position": i_parkingspace.position
            }
        if self._configuration["simulation"]["parkingspaces"]["total"] != len(p_parkingspaces):
            self._configuration["simulation"]["parkingspaces"]["total"] = len(p_parkingspaces)
            self.writeCfg()

    def updateRunCfgVehicle(self, p_run, p_vcfg):
        """ Update vehicle in run configuration

        Args:
            p_run (int?): number of run???
            p_vcfg (dict): dictionary representing a vehicle???
        """
        l_run = str(p_run)
        if not self._runconfiguration.get(l_run):
            self._runconfiguration[l_run] = {}
        if not self._runconfiguration.get(l_run).get("vehicles"):
            self._runconfiguration[l_run]["vehicles"] = {}
        self._runconfiguration[l_run]["vehicles"][p_vcfg["name"]] = p_vcfg

        # ---- helper for new mixed traffic ---- #

    def _convert_mixed_traffic_args(self, mixed_traffic_args):
        '''
        parses the command line argument for cooperative traffic in phase 2 and phase 3
        only if "true" or "True" was given, the cooperation with mixed traffic will work
        :param mixed_traffic_args: parsed commandline arguments of mixed traffic
        :return: float for ratio of mixed traffic, bool cooperate in phase2, bool cooperate in phase3
        '''
        # convert values
        mixed_ratio = float(mixed_traffic_args[0])
        m_phase2 = False
        m_phase3 = False
        if (mixed_traffic_args[1] == "True") or (mixed_traffic_args[1] == "true"):
            m_phase2 = True
        if (mixed_traffic_args[2] == "True") or (mixed_traffic_args[2] == "true"):
            m_phase3 = True

        return mixed_ratio, m_phase2, m_phase3

    def _calculate_num_of_coop_vehicles(self, ratio, vehicles):
        '''
        Calculates the number of cooperative cars by given ratio:
        number of cooperative vehicles = int( round(ratio * number of all vehicles))
        :param ratio: float between 0.0 and 1.0
        :param vehicles: total number of vehicles
        :return: number of cooperative vehicles
        '''
        # vehicle type is int, ratio is float
        num_of_vehicles_coop = 0
        if ratio < 0.0 or ratio > 1.0:
            return num_of_vehicles_coop  # just a dummy, not needed cause of sanity check!
        else:
            num_of_vehicles_coop = int(round(ratio * vehicles))
            return num_of_vehicles_coop

    def _sanity_check_mixed_traffic(self):
        """
        Checks if mixed traffic configuration is runnable.
        checks:
            - ratio is between 0.0 and 1.0 (including)
            - if one of the coop phases are true
            - number of cooperative / non cooperative vehicles is greater than 0
            - number of coop + non coop is the same as total vehicles
        :return:
        """
        mixed_traffic_confg = self._configuration["simulation"]["mixed_traffic"]
        # raise exception if mixed traffic has been set but the ratio is not [0,1] and min one phase is True
        if mixed_traffic_confg["ratio"] == -1.0:
            print("* no use of mixed traffic")
        else:
            print("* use of mixed traffic")
            if mixed_traffic_confg["ratio"] < 0.0 or mixed_traffic_confg["ratio"] > 1.0:
                message = ("The mixed traffic ratio must be between 0.0 and 1.0. Got: {}".format(
                    self._configuration["simulation"]["mixed_traffic"]["ratio"]))
                raise BaseException(message)
            if (mixed_traffic_confg["coopPhase2"] is False) and (mixed_traffic_confg["coopPhase3"] is False):
                message = (
                    "Phase2 = {}, Phase3 = {}. One phase must be True. Otherwise all smart cars are dump cars.".format(
                        mixed_traffic_confg["coopPhase2"], mixed_traffic_confg["coopPhase3"]))
                raise BaseException(message)
            if mixed_traffic_confg["coop_vehicles"] < 0 or mixed_traffic_confg["non_coop_vehicles"] < 0:
                message = ("got negative number of vehicles: coop = {} , non_coop = {}".format(
                    mixed_traffic_confg["coop_vehicles"], mixed_traffic_confg["non_coop_vehicles"]))
                raise BaseException(message)
            if (mixed_traffic_confg["coop_vehicles"] + mixed_traffic_confg["non_coop_vehicles"]) != \
                    self._configuration["simulation"]["vehicles"]:
                message = ("Total number of mixed Traffic [{}] must be equal to number of vahicles [{}].".format(
                    (mixed_traffic_confg["coop_vehicles"] + mixed_traffic_confg["non_coop_vehicles"]),
                    self._configuration["simulation"]["vehicles"]))
                raise BaseException(message)
