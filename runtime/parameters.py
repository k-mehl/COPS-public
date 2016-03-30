#default run parameters
DEFAULT_NUMBER_PARKINGSPACES = 5
DEFAULT_NUMBER_SEARCHVEHICLES = 5
DEFAULT_COOPERATION_RATIO = 0.0
DEFAULT_NUMBER_OF_RUNS = 1
DEFAULT_FIXEDSEED = 1

#vehicle parameters
MAXSPEED_PHASE2 = 8.333
PARKING_EVENT_DURATION = 12
MAX_DISTANCE_TO_PARKING = 30.0
MIN_DISTANCE_TO_PARKING = 12.0
#weights in phase 3
#cooperative
DISTANCE_WEIGHT_COOP = 1
SELFVISIT_WEIGHT_COOP = 2000
EXTERNALVISIT_WEIGHT_COOP = 2000
EXTERNALPLANNED_WEIGHT_COOP = 100

#non-cooperative
DISTANCE_WEIGHT_NONCOOP = 1
SELFVISIT_WEIGHT_NONCOOP = 2000
EXTERNALVISIT_WEIGHT_NONCOOP = 0
EXTERNALPLANNED_WEIGHT_NONCOOP = 0