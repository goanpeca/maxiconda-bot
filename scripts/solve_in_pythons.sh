#!/usr/bin/env bash

# Copyright (c) Semi-ATE
# Distributed under the terms of the MIT License

set -ex

eval $(conda shell.bash hook)

# Latest 3.6 CPython
conda create -n py36 mamba python=3.6 --yes
conda activate py36
mamba install --file ./maxiconda-bot/requirements.txt --yes
python ./maxiconda-bot/scripts/solve.py

# # Latest 3.6 PyPy
# conda create -n pypy36 mamba pypy3.6 --yes
# conda activate pypy36
# mamba install --file ./maxiconda-bot/requirements.txt --yes
# pypy3.6 ./maxiconda-bot/scripts/solve.py

# Latest 3.7 CPython
conda create -n py36 mamba python=3.6 --yes
conda activate py36
mamba install --file ./maxiconda-bot/requirements.txt --yes
python ./maxiconda-bot/scripts/solve.py

# # Latest 3.7 PyPy
# conda create -n pypy37 mamba pypy3.7 --yes
# conda activate pypy37
# mamba install --file ./maxiconda-bot/requirements.txt --yes
# pypy3.7 ./maxiconda-bot/scripts/solve.py

# Latest 3.8 CPython
conda create -n py38 mamba python=3.8 --yes
conda activate py38
mamba install --file ./maxiconda-bot/requirements.txt --yes
python ./maxiconda-bot/scripts/solve.py

# Latest 3.9 CPython
conda create -n py39 mamba python=3.9 --yes
conda activate py39
mamba install --file ./maxiconda-bot/requirements.txt --yes
python ./maxiconda-bot/scripts/solve.py
