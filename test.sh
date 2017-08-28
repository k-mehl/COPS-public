#!/usr/bin/env bash

# mainly to do quick integration tests with different parameter combination and
# see if anything fails since I have no time to write tests atm

common="--parkingspaces 10 --parking-search-vehicles 5 --headless --runs 1"

# first argument is phase 2 ratio, second argument is phase 3 ratio
testfun () {
    echo -e "\n\e[1mPhase 2 = $1, Phase 3 = $2\e[0m"
    python3 main.py \
        $common \
        --cooperative-ratio-phase-two $1 \
        --cooperative-ratio-phase-three $2 \
        >/dev/null

    if [ $? -eq 0 ]; then
        echo -e "\e[1;32mPASSED\e[0m"
    else
        echo -e "\e[1;31mFAILED\e[0m"
    fi
}

testfun 1 1
testfun 1 0
testfun 0 1
