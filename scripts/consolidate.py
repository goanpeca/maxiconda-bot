#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script will consolidate all the solutions in maxiconda-envs/specs/solutions/
in the form of an xlsx file called `maxiconda.xlsx`.
Each environment is a separate tab, and the primary- and secondary packages are
separated (and sorted alphabetically)
"""
import sys
import os
import pyxlsx

here = os.path.dirname(os.path.abspath(__file__))
offset = "../.."  
solutions_root = os.path.join(here, offset, "maxiconda-envs/specs/solutions")

def main():
    print("running {__file__.replace(here, '')}")

if __name__ == '__main__':
    main()
