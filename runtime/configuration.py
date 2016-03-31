import json
import jsoncfg
import os

class Configuration(object):

    def __init__(self, p_args, p_configdir):

        self._defaultconfig = {
          "simulation" : {
              "routefile" : "reroute.rou.xml",
              "resourcedir" : "resources",
              "sumoport" : 8873,
              "headless" : True,
              "runs" : 10,
              "parkingspaces" : 5,
              "vehicles" : 5,
              "cooperation" : 0.0,
              "fixedseed" : 1,
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

        # create fresh config.jason and dir if not exists
        if not os.path.isdir(p_configdir):
            os.mkdir(p_configdir)

        print("* checking whether {} exists".format(p_args.config))
        if not os.path.isfile(p_args.config):
            self._configuration = jsoncfg.loads_config((json.dumps(self._defaultconfig)))()
            self._writeDefault(p_args.config)
        else:
            self._configuration = jsoncfg.load_config(p_args.config)()
            print("* loaded existing config {}".format(p_args.config))

        self._overrideConfig(p_args)

    def get(self, p_key):
        return self._configuration.get(p_key)

    def write(self, p_location):
        fp = open(p_location, mode="w")
        json.dump(self._configuration, fp, sort_keys=True, indent=4, separators=(',', ' : '))
        fp.close()

    def _writeDefault(self, p_location):
        fp = open(p_location, mode="w")
        json.dump(self._defaultconfig, fp, sort_keys=True, indent=4, separators=(',', ' : '))
        fp.close()
        print("* wrote new default config to {}".format(p_location))

## override values with provided argparse parameters
    # @p_args argparse object
    def _overrideConfig(self, p_args):
        if p_args.parkingspaces:
            self._configuration["simulation"]["parkingspaces"] = p_args.parkingspaces
        if p_args.psv:
            self._configuration["simulation"]["vehicles"] = p_args.psv
        if p_args.coopratio:
            self._configuration["simulation"]["cooperation"] = p_args.coopratio
        if p_args.sumoport:
            self._configuration["simulation"]["sumoport"] = p_args.sumoport
        if p_args.resourcedir:
            self._configuration["simulation"]["resourcedir"] = p_args.resourcedir
        if p_args.runs:
            self._configuration["simulation"]["runs"] = p_args.runs
        if p_args.headless:
            self._configuration["simulation"]["headless"] = True
        if p_args.gui:
            self._configuration["simulation"]["headless"] = False



