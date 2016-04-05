from __future__ import print_function
import json
import os
import gzip

# todo: add run configuration, i.e. occupancy of parking spaces.
# todo Generate for each run occupancy by POIid if config doesn't match, i.e too few/many runs,parkingspaces configured,


class Configuration(object):

    def __init__(self, p_args, p_configdir):

        self._defaultconfig = {
          "simulation" : {
              "routefile" : "reroute.rou.xml",
              "resourcedir" : "resources",
              "sumoport" : 8873,
              "headless" : True,
              "runs" : 10,
              "runconfiguration" : "config.runs.json.gz",
              "parkingspaces" : {
                  "total" : 400,
                  "free" : 5,
              },
              "vehicles" : 5,
              "coopratioPhase2": 0.0,
              "coopratioPhase3": 0.0,
          },
          "vehicle" : {
              "parking" : {
                  "distance" : {
                      "min" : 12.0,
                      "max" : 30.0,
                  },
                  "duration" : 12.0,
              },
              "maxspeed" : {
                  "phase1" : 27.778,
                  "phase2" : 8.333,
                  "phase3" : 8.333,
              },
              "weights" : {
                  "coop" : {
                      "distance" : 1,
                      "selfvisit" : 2000,
                      "externalvisit" : 2000,
                      "externalplanned" : 100,
                  },
                  "noncoop" : {
                      "distance" : 1,
                      "selfvisit" : 2000,
                      "externalvisit" : 0,
                      "externalplanned" : 0,
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

        self._runcfgfilename = os.path.join(self._configdir, self._configuration.get("simulation").get("runconfiguration"))

        self._runconfiguration = self._readRunCfg(p_args)




    def getCfg(self, p_key):
        return self._configuration.get(p_key)

    def getRunCfg(self, p_key):
        return self._runconfiguration.get(p_key)

    def _writeCfg(self, p_config, p_location, p_sort_keys=True, p_indent=4, p_separators=(',', ' : ')):
        if p_location.endswith(".gz"):
            fp = gzip.GzipFile(p_location, 'w')
        else:
            fp = open(p_location, mode="w")

        json.dump(p_config, fp, sort_keys=p_sort_keys, indent=p_indent, separators=p_separators)
        fp.close()

    ## override values with provided argparse parameters
    # @p_args argparse object
    def _overrideConfig(self, p_args):
        if p_args.parkingspaces != None:
            self._configuration["simulation"]["parkingspaces"]["free"] = p_args.parkingspaces
        if p_args.psv != None:
            self._configuration["simulation"]["vehicles"] = p_args.psv
        if p_args.coopratioPhase2 != None:
            self._configuration["simulation"]["forcecooperationphasetwo"] = p_args.coopratioPhase2
        if p_args.coopratioPhase3 != None:
            self._configuration["simulation"]["forcecooperationphasethree"] = p_args.coopratioPhase3
        if p_args.sumoport != None:
            self._configuration["simulation"]["sumoport"] = p_args.sumoport
        if p_args.resourcedir != None:
            self._configuration["simulation"]["resourcedir"] = p_args.resourcedir
        if p_args.runs != None:
            self._configuration["simulation"]["runs"] = p_args.runs
        if p_args.runconfiguration != None:
            self._configuration["simulation"]["runconfiguration"] = p_args.runconfiguration
        if p_args.headless:
            self._configuration["simulation"]["headless"] = True
        if p_args.gui:
            self._configuration["simulation"]["headless"] = False

    ## Sanity checks of config
    def _sanitycheck(self):
        # raise exception if gui mode requested with > 1 run
        if not self._configuration.get("simulation").get("headless") and self._configuration.get("simulation").get("runs") > 1:
            message = "Number of runs can't exceed 1, if run in GUI mode."
            raise StandardError(message)

        # raise exception if headless mode requested  AND number of parking spaces < vehicles
        # in the static case this produces an endless loop of at least one vehicle searching for a free space.
        # In Gui mode this behavior is acceptable
        if self._configuration.get("simulation").get("headless") and self._configuration.get("simulation").get("parkingspaces").get("free") < self._configuration.get("simulation").get("vehicles"):
            message = "Number of parking spaces must be at least equal to number of vehicles, if run in headless mode."
            raise StandardError(message)

        # raise an exception if provided basedir does not exist
        if not os.path.isdir(self._configuration.get("simulation").get("resourcedir")):
            message = "The provided directory {} does not exist for argument --resourcedir".format(self._configuration.get("simulation").get("resourcedir"))
            raise StandardError(message)

    def existRunCfg(self):
        return len(self._runconfiguration) > 0

    def isRunCfgOk(self, p_runid):
        # phase 1: check if runcfg for given runid exists
        if not self._runconfiguration.get(str(p_runid)):
            print("There exists no run configuration for runid {}.".format(p_runid))
            return False

        # phase 2: check for enough stored runs
        if len(self._runconfiguration) < self._configuration.get("simulation").get("runs"):
            print("/!\ run config does not match simulation parameters. Expecting {} runs, read {} runs from config instead. ".format(
                      self._configuration.get("simulation").get("runs"), len(self._runconfiguration), self._runcfgfilename
                  ))
            return False

        # phase 3: check for enough available parkingspaces in each run (i.e. #available parkingspaces >= #vehicles)
        # contains amount of runs with mismatching available parkingspaces
        l_available = filter(lambda (k,v): v.get("available"),
                        self._runconfiguration.get(str(p_runid)).get("parkingspaces").items())

        if len(l_available) < self._configuration.get("simulation").get("vehicles"):
            print("/!\  run config does not match simulation parameters. Expecting at least {} available parking spaces due to {} searching vehicles. Found only {} in run {}".format(
                self._configuration.get("simulation").get("parkingspaces").get("free"),
                self._configuration.get("simulation").get("vehicles"),
                len(l_available),
                p_runid))
            return False
        return True

    def _readRunCfg(self, p_args):
        print("* reading run cfg {}".format(self._runcfgfilename))
        if not os.path.isfile(self._runcfgfilename):
            return {}

        if self._runcfgfilename.endswith(".gz"):
            fp = gzip.GzipFile(self._runcfgfilename, 'r')
        else:
            fp = open(self._runcfgfilename, mode="r")

        l_runcfg = json.load(fp)

        fp.close()

        return l_runcfg


    def writeCfg(self):
        print("* writing configuration to {}".format(self._args.config))
        self._writeCfg(self._configuration, self._args.config)
        print("  -> done.")

    def writeRunCfg(self):
        print("* writing run configuration to {}".format(self._runcfgfilename))
        self._writeCfg(self._runconfiguration, self._runcfgfilename, p_sort_keys=True, p_indent=None, p_separators=(',',':'))
        print("  -> done.")

    def updateRunCfgParkingspaces(self, p_run, p_parkingspaces):
        l_run = str(p_run)
        if not self._runconfiguration.get(l_run):
            self._runconfiguration[l_run] = {}
        self._runconfiguration.get(l_run)["parkingspaces"] = {}

        for i_parkingspace in p_parkingspaces:
            self._runconfiguration.get(l_run).get("parkingspaces")[str(i_parkingspace.name)] = {
                "name" : i_parkingspace.name,
                "available" : i_parkingspace.available,
                "edgeID" : i_parkingspace.edgeID,
                "position" : i_parkingspace.position
            }
        if self._configuration["simulation"]["parkingspaces"]["total"] != len(p_parkingspaces):
            self._configuration["simulation"]["parkingspaces"]["total"] = len(p_parkingspaces)
            self.writeCfg()

    def updateRunCfgVehicle(self, p_run, p_vcfg):
        l_run = str(p_run)
        if not self._runconfiguration.get(l_run):
            self._runconfiguration[l_run] = {}
        if not self._runconfiguration.get(l_run).get("vehicles"):
            self._runconfiguration.get(l_run)["vehicles"] = {}
        self._runconfiguration.get(l_run).get("vehicles")[p_vcfg.get("name")] = p_vcfg
