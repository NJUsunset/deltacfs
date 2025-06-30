import numpy
import pandas
import math
import os
from pyproj import Geod
from constant import *
import grn_input
import cmp_input

if __name__ == '__main__':
    print('INFO: setup all files in config folder before running this script.')
    print('INFO: calculate.py running...')
    ifgrn = input('INFO: Do you want to calculate green function set? (y/n): ')
    ifoverridegrn = input('INFO: Do you want to override existed green function set? (y/n): ')
    ifcmp = input('INFO: Do you want to calculate deltacfs? (y/n): ')
    ifoverridecmp = input('INFO: Do you want to override existed deltacfs? (y/n): ')
    if ifgrn == 'y':
        print('INFO: grn_input.py running...')
        depth_range = grn_input.depth_minmax()
        depth_step, calculation_settings = grn_input.calculation_setting()
        overide = False
        if ifoverridegrn == 'y':
            overide = True
        for depth_number in range(depth_range[0], depth_range[1] + 1):
            grn_input.build_grn_input(depth_number, calculation_settings, overide)
    if ifcmp == 'y':
        print('INFO: cmp_input.py running...')
        overide = False
        if ifoverridecmp == 'y':
            overide = True
        cmp_input.build_cmp_input(overide)
    print('INFO: calculate.py finished.')