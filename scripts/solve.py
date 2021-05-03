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

here = os.path.dirname(os.path.abspath(__file__))
offset = "../.."  
matrix_path = os.path.join(here, offset, "maxiconda-envs/specs/matrix.yaml")
primary_packages_path = os.path.join(here, offset, "maxiconda-envs/specs/primary_packages.yaml")
solutions_root = os.path.join(here, offset, "maxiconda-envs/specs/solutions")

def main():
    OS, CPU, PY = get_running_env()

    matrix_file = os.path.join(here, matrix_path) 
    if not os.path.exists(matrix_file):
        print(f"couldn't find '{matrix_path}'")
        print("maxiconda-envs not checked out ?")
        sys.exit(1)
    with open(matrix_file) as fd:
        matrix = yaml.load(fd, Loader=yaml.FullLoader)
    try:
        designator = matrix[OS][CPU][PY]
    except KeyError:
        print(f"Current {OS}/{CPU}/{PY} not found in '{matrix_file}'")
        sys.exit(1)

    primary_packages_file = os.path.join(here, primary_packages_path)
    if not os.path.exists(matrix_file):
        print(f"couldn't find '{primary_packages_path}'")
        print("maxiconda-envs not checked out ?")
        sys.exit(1)
    with open(primary_packages_file) as fd:
        primary_packages = yaml.load(fd, Loader=yaml.FullLoader)
    for environment in primary_packages:
        print(f"{designator.split('_')[0]}/{designator.split('_')[1]}/{environment}:")

        print("   primary packages:")
        packages = primary_packages[environment]
        for package in packages:
            print(f"      {package}")

        if "python" not in packages:
            print("   including in primary packages:")
            print("      python")
            packages.append("python")

        packages_to_exclude = reduce(packages, designator)
        if not packages_to_exclude == []:
            print("   excluding from primary packages:")
            for package in packages_to_exclude:
                packages.remove(package)
                print(f"      {package}")
        
        print("   solution:")
        solution = solve(designator, environment, packages)
        print(f"      python = {solution['python']}")
        print(f"      {len(solution['primary'])} primary packages:")
        for package in solution['primary']:
            if package != 'python':
                print(f"         {package} = {solution['primary'][package]}")
        print(f"      {len(solution['secondary'])} secondary packages:")
        for package in solution['secondary']:
            print(f"         {package} = {solution['secondary'][package]}")

def solve(designator, environment, primary_packages):
    """

    """
    retval = {}
    OS_CPU, PY = designator.split('_')
    primary_packages_file = os.path.join(here, "primary_packages.txt")
    with open(primary_packages_file, "w") as fd:
        for package in primary_packages:
            fd.write(f"{package}\n")

    command = f'bash -c "mamba create -n xxxx -c conda-forge --file {primary_packages_file} --json --dry-run > solution.json"'
    result = subprocess.run(command, shell=True)

    with open('solution.json', 'r') as json_file:
        data = json.load(json_file)
    packages = {}
    for element in data['actions']['LINK']:
        packages[element['name']] = element['version']

    secondary_packages = list(packages)
    for primary_package in primary_packages:
        secondary_packages.remove(primary_package)

    solution_file = os.path.join(solutions_root, OS_CPU, PY, f"{environment}.txt")
    if not os.path.exists(os.path.dirname(solution_file)):
        os.makedirs(os.path.dirname(solution_file))
    with open(solution_file, 'w') as fd:
        fd.write(f"# {OS_CPU}/{PY}/{environment}\n")

        fd.write(f"\npython {packages['python']}\n")
        retval['python'] = packages['python']

        fd.write(f"\n# {len(primary_packages)-1} primary packages :\n\n")
        retval['primary'] = {}
        for primary_package in sorted(primary_packages):
            if primary_package != 'python':
                fd.write(f"{primary_package} = {packages[primary_package]}\n")
                retval['primary'][primary_package] = packages[primary_package]

        fd.write(f"\n# {len(secondary_packages)} secondary packages :\n\n")
        retval['secondary'] = {}
        for secondary_package in sorted(secondary_packages):
            fd.write(f"{secondary_package} = {packages[secondary_package]}\n")
            retval['secondary'][secondary_package] = packages[secondary_package]

    os.unlink("solution.json")
    os.unlink("primary_packages.txt")

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

def get_conda_forge_packages(designator):
    """
    This function returns all packages that exist for the given OS/CPU/PY
    """
    OS_CPU = designator.split('_')[0]
    PY = designator.split('_')[1]

    arch_packages = f"https://conda.anaconda.org/conda-forge/{OS_CPU}/repodata.json.bz2"
    noarch_packages = "https://conda.anaconda.org/conda-forge/noarch/repodata.json.bz2"
    retval = {}

    arch_json_bz2 = requests.get(arch_packages).content
    arch_json = bz2.decompress(arch_json_bz2) 
    arch = json.loads(arch_json)
    for package in arch['packages']:
        if arch['packages'][package]['build'].startswith('py'):
            if not arch['packages'][package]['build'].startswith(PY):
                continue
        if arch['packages'][package]['name'] not in retval:
            retval[arch['packages'][package]['name']] = []
        if arch['packages'][package]['version'] not in retval[arch['packages'][package]['name']]:
            retval[arch['packages'][package]['name']].append(arch['packages'][package]['version'])

    noarch_json_bz2 = requests.get(noarch_packages).content
    noarch_json = bz2.decompress(noarch_json_bz2) 
    noarch = json.loads(noarch_json)
    for package in noarch['packages']:
        if noarch['packages'][package]['name'] not in retval:
            retval[noarch['packages'][package]['name']] = []
        if noarch['packages'][package]['version'] not in retval[noarch['packages'][package]['name']]:
            retval[noarch['packages'][package]['name']].append(noarch['packages'][package]['version'])

    return retval

def get_running_env():
    """ 
    This function will determine on what environment is running and returns the tuple (OS, CPU, PY). 
    """
    
    OS = platform.system()
    if OS == "Darwin":
        OS = "MacOS"
    if OS not in ["Linux", "Windows", "MacOS"]:
        raise Exception("'{OS}' not supported.")

    is_64bits = sys.maxsize > 2**32
    if not is_64bits:
        raise Exception("only 64 bit platforms are supported.")
    CPU = platform.processor()
    if CPU not in ["x86_64", "aarch64"]:  # what is the M1 returning?!? ... I presume `aarch64`
        raise Exception(f"'{CPU}' not supported.")

    if platform.python_implementation() == "CPython":
        PY = f"py{''.join(platform.python_version_tuple()[:2])}"
    elif platform.python_implementation() == "PyPy":
        PY = f"pypy{''.join(platform.python_version_tuple()[:2])}"
    else:
        raise Exception(f"'{platform.python_implementation()}' not supported.")

    return OS, CPU, PY

if __name__ == '__main__':
    main()
