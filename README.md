# maxiconda-bot

This is a bot, implemented with github actions that runs the 2 actions once every day.

## solving action

The bot will checkout the `maxiconda-envs` repository and solve
the environments in `maxiconda-envs/specs/primary_packages.yaml`
for the current OS/CPU/PY by means of the `solve.py` script.
This script dumps it's output to `maxiconda-envs/specs/solutions/`
in a directory structure `OS/PY/`.

The bot of course has to check the results back in (straight to master)

## consolidate action

The bot is organized that a bunch of processes do the solving for the
different OS/CPU/PY combinations, once all have been done (successfuly)
the `consolidate.py` script has to run. This script checks out
`maxiconda-envs` and writes the found solutions togheter in one .XLSX
file called `maxiconda_envs.xlsx` located in the highest level of the
`maxiconda-envs` repo. The README.md of the `maxicodna-envs` points 
to the **LATEST RELEASE** of `maxiconda-envs` (eow: the maxiconda-envs.xlsx
is an asset)
