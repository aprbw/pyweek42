#!/usr/bin/env python3
"""Grain of Doubt - PyWeek 42 Standard Entrypoint.

Follows PyWeek packaging convention: https://pyweek.readthedocs.io/en/latest/packaging.html
"""
import sys

MIN_VER = (3, 10)
if sys.version_info[:2] < MIN_VER:
    sys.exit("This game requires Python {}.{} or later.".format(*MIN_VER))

from main import main

if __name__ == "__main__":
    main()
