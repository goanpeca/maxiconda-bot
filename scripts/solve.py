#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script will solve all environments in maxiconda-envs/specs/primary_packages.yaml 
against the current OS/CPU/PY and write the results in maxiconda/specs/solutions/OS_CPU/PY
in ONE text file per environment.
"""
import sys
import os
import platform
import yaml
import requests
import bz2
import json
import subprocess
from pathlib import Path
from typing import Tuple

# Constants
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
ROOT = REPO_ROOT.parent
MATRIX_FPATH = ROOT / "maxiconda-envs/specs/matrix.yaml"
PRIMARY_PACKAGES_FPATH = ROOT / "maxiconda-envs/specs/primary_packages.yaml"
SOLUTIONS_PATH = ROOT / "maxiconda-envs/specs/solutions"
CACHE = {}


def get_running_env(python_version: str = '', py_implementation: str = '') -> Tuple[str, str, str]:
    """ 
    This function will determine on what environment is running and returns the tuple (OS, CPU, PY).

    Parameters
    ----------
    python_version : str, optional
        Python version string. Example: '3.8'.

    Returns
    -------
    tuple
        TODO:
    """
    OS = platform.system()
    if OS == "Darwin":
        OS = "MacOS"

    if OS not in ["Linux", "Windows", "MacOS"]:
        raise Exception("'{OS}' not supported.")

    is_64bits = sys.maxsize > 2**32
    if not is_64bits:
        raise Exception("only 64 bit platforms are supported.")

    CPU = platform.machine()
    if OS == "Windows":
        CPU = "x86_64" if CPU == "AMD64" else CPU

    if CPU not in ["AMD64", "x86_64", "aarch64"]:  # what is the M1 returning?!? ... I presume `aarch64`
        raise Exception(f"'{CPU}' not supported.")

    if python_version and "." in python_version:
        # Python version provided as a string. Example '3.8'
        python_version_str = "".join(python_version.split("."))
    else:
        # Python version provided by current process environment
        python_version_str = "".join(platform.python_version_tuple()[:2])

    py_implementation = py_implementation if py_implementation else platform.python_implementation()
    py_implementation = py_implementation.lower()

    if py_implementation == "cpython":
        PY = f"py{python_version_str}"
    elif py_implementation == "pypy":
        PY = f"pypy{python_version_str}"
    else:
        raise Exception(f"'{platform.python_implementation()}' not supported.")

    return OS, CPU, PY


def main(python_version: str, py_implementation: str, matrix_fpath: Path, primary_packages_fpath: Path, solutions_path: Path):
    """
    Run main process to generate environment packages.
    """
    OS, CPU, PY = get_running_env(python_version, py_implementation)
    if PY.startswith("pypy"):
        package_name = f"pypy{python_version}"
        package_name_version = f"pypy{python_version}"
    else:
        package_name = f"python"
        package_name_version = f"python={python_version}"

    if not matrix_fpath.is_file():
        print(f"couldn't find '{matrix_fpath}'")
        print("maxiconda-envs not checked out ?")
        sys.exit(1)

    with open(matrix_fpath) as fd:
        matrix = yaml.load(fd, Loader=yaml.FullLoader)

    try:
        designator = matrix[OS][CPU][PY]
    except KeyError:
        print(f"Current {OS}/{CPU}/{PY} not found in '{matrix_fpath}'")
        # sys.exit(1)
        return

    if not primary_packages_fpath.is_file():
        print(f"couldn't find '{primary_packages_fpath}'")
        print("maxiconda-envs not checked out ?")
        sys.exit(1)

    with open(primary_packages_fpath) as fd:
        primary_packages = yaml.load(fd, Loader=yaml.FullLoader)

    for environment in primary_packages:
        print(f"\n\n# {designator.split('_')[0]}/{designator.split('_')[1]}/{environment}:")

        print("   primary packages:")
        packages = primary_packages[environment]
        for package in packages:
            print(f"      {package}")

        if package_name not in packages:
            python = package_name_version
            print("   including in primary packages:")
            print(f"      {python}")
            packages.append(package_name)

        packages_to_exclude = reduce(packages, designator)
        if not packages_to_exclude == []:
            print("   excluding from primary packages:")
            for package in packages_to_exclude:
                packages.remove(package)
                print(f"      {package}")
        
        print("   solution:")
        solution = solve(designator, environment, packages, solutions_path, python_version)
        if solution:
            print(f"      {package_name} = {solution[package_name]}")
            print(f"      {len(solution['primary'])} primary packages:")
            for package in solution['primary']:
                if package != package_name:
                    print(f"         {package} = {solution['primary'][package]}")

            print(f"      {len(solution['secondary'])} secondary packages:")
            for package in solution['secondary']:
                print(f"         {package} = {solution['secondary'][package]}")
        else:
            print(f"No solution found!")


def run_mamba(pkgs, channels=["conda-forge"]):
    """
    Run mamba dry run 
    """
    cmd = ["mamba", "create", "--name", "test_env", "--dry-run", "--json"] + pkgs
    for channel in channels:
        cmd.append("--channel")
        cmd.append(channel)

    print("\nCommand: '" + " ".join(cmd) + "'\n")
    print("\nRunning conda dry solve for these packages:\n")
    for pkg in pkgs:
        print(f"  * {pkg}")
    print("\n")

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, _ = p.communicate()
    data = {}
    try:
        data = json.loads(stdout)
    except Exception:
        pass

    return data


def solve(designator, environment, primary_packages, solutions_path, python_version):
    """
    """
    retval = {}
    OS_CPU, PY = designator.split('_')

    if PY.startswith("pypy"):
        package_name = f"pypy{python_version}"
        package_name_version = f"pypy{python_version}"
    else:
        package_name = f"python"
        package_name_version = f"python={python_version}"


    primary_pkgs = primary_packages[:]
    primary_pkgs.remove(package_name)
    data = run_mamba(primary_pkgs + [package_name_version])

    if not data:
        return

    packages = {}
    for element in data['actions']['LINK']:
        packages[element['name']] = element['version']

    secondary_packages = list(packages)
    for primary_package in primary_packages:
        secondary_packages.remove(primary_package)

    solution_fpath = solutions_path / OS_CPU / PY / f"{environment}.txt"
    if not solution_fpath.is_file():
        os.makedirs(solution_fpath.parent, exist_ok=True)

    with open(solution_fpath, 'w') as fh:
        fh.write(f"# {OS_CPU}/{PY}/{environment}\n")

        fh.write(f"\n{package_name} {packages[package_name]}\n")
        retval[package_name] = packages[package_name]

        fh.write(f"\n# {len(primary_packages)-1} primary packages :\n\n")
        retval['primary'] = {}
        for primary_package in sorted(primary_packages):
            if primary_package != package_name:
                fh.write(f"{primary_package} = {packages[primary_package]}\n")
                retval['primary'][primary_package] = packages[primary_package]

        fh.write(f"\n# {len(secondary_packages)} secondary packages :\n\n")
        retval['secondary'] = {}
        for secondary_package in sorted(secondary_packages):
            fh.write(f"{secondary_package} = {packages[secondary_package]}\n")
            retval['secondary'][secondary_package] = packages[secondary_package]

    # os.unlink("solution.json")

    return retval

def reduce(packages, designator):
    """ 
    This function will return a list of packages that need to be removed from packages
    because they don't exist on conda-forge for the designator.
    """
    retval = []
    available_packages = get_conda_forge_packages(designator)
    for package in packages:
        if not package in available_packages:
            retval.append(package)

    return retval


def get_repodata(url):
    """
    Get repodata from url poitning to anaconda.org bz2 files.

    If url has been already downloaded in a session, it will use the data from
    cache.

    Parameters
    ----------
    url : str
        Url to repodata.

    Returns
    -------
    dict
        Repodata dictionary.
    """
    global CACHE
    if url not in CACHE:
        arch_json_bz2 = requests.get(url).content
        arch_json = bz2.decompress(arch_json_bz2) 
        arch = json.loads(arch_json)
        CACHE[url] = arch
    else:
        arch = CACHE[url]

    return arch


def get_conda_forge_packages(designator):
    """
    This function returns all packages that exist for the given OS/CPU/PY.
    """
    OS_CPU = designator.split('_')[0]
    PY = designator.split('_')[1]

    arch_packages = f"https://conda.anaconda.org/conda-forge/{OS_CPU}/repodata.json.bz2"
    noarch_packages = "https://conda.anaconda.org/conda-forge/noarch/repodata.json.bz2"
    retval = {}

    arch = get_repodata(arch_packages)
    for package in arch['packages']:
        if arch['packages'][package]['build'].startswith('py'):
            if not arch['packages'][package]['build'].startswith(PY):
                continue

        if arch['packages'][package]['name'] not in retval:
            retval[arch['packages'][package]['name']] = []

        if arch['packages'][package]['version'] not in retval[arch['packages'][package]['name']]:
            retval[arch['packages'][package]['name']].append(arch['packages'][package]['version'])

    noarch = get_repodata(noarch_packages)
    for package in noarch['packages']:
        if noarch['packages'][package]['name'] not in retval:
            retval[noarch['packages'][package]['name']] = []

        if noarch['packages'][package]['version'] not in retval[noarch['packages'][package]['name']]:
            retval[noarch['packages'][package]['name']].append(noarch['packages'][package]['version'])

    return retval


if __name__ == '__main__':
    for python_version in ["3.6", "3.7", "3.8", "3.9"]:
        for py_implementation in ["cpython", "pypy"]:
            if platform.system() == "Linux" and python_version == "3.7":
                continue

            main(
                python_version,
                py_implementation,
                matrix_fpath=MATRIX_FPATH,
                primary_packages_fpath=PRIMARY_PACKAGES_FPATH,
                solutions_path=SOLUTIONS_PATH,
            )
