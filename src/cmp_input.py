TEST = False
from src.constant import *
from pyproj import Geod
import math
import os
if __name__ == '__main__':
    print('INFO: cmp_input.py testing...')
    TEST = True


def observation_array_on_fault(receiving_fault_array, target_depth, observation_distance):
    # Generate points along the fault plane at a specified depth with a given horizontal spacing.
    
    observation_points = []

    O_lon = float(receiving_fault_array[1])
    O_lat = float(receiving_fault_array[2])
    O_depth = float(receiving_fault_array[3])
    length = float(receiving_fault_array[4])
    width = float(receiving_fault_array[5])
    strike = float(receiving_fault_array[6])
    dip_angle = float(receiving_fault_array[7])

    geod = Geod(ellps="WGS84")

    depth_diff = target_depth - O_depth
    horizontal_offset = depth_diff / math.tan(math.radians(dip_angle))
    width_offset = depth_diff / math.sin(math.radians(dip_angle))
    
    if (depth_diff < 0) or (width_offset > width):
        return observation_points

    # Determine the starting point's projection at the target depth
    dip_direction = (strike + 90) % 360
    proj_lon, proj_lat, _ = geod.fwd(O_lon, O_lat, dip_direction, horizontal_offset * 1000)

    # Generate points along the fault's strike direction
    num_points = int(length / observation_distance) + 1

    for i in range(num_points):
        distance_along_strike = i * observation_distance
        point_lon, point_lat, _ = geod.fwd(proj_lon, proj_lat, strike, distance_along_strike * 1000)
        observation_points.append((point_lon, point_lat))

    return observation_points


if TEST:
    receiving_fault_array = [1, 120.0, 30.0, 5.0, 10.0, 5.0, 45.0, 30.0]
    target_depth = 30.0
    observation_distance = 1.0

    # Generate points along the fault
    points = observation_array_on_fault(receiving_fault_array, target_depth, observation_distance)

    # Output the generated points
    print("Generated points along the fault:")
    for point in points:
        print(f"Longitude: {point[0]:.6f}, Latitude: {point[1]:.6f}")


def config():
    # read config.dat file and return a list with info
    configs = []

    with open(CONFIG_PREFIX + 'config.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            configs.append(values)

    return configs


if TEST:
    configs = config()

if TEST:
    depth_number = 1
    depth_list = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, \
                  0.7, 0.8, 0.9, 1.0, 1.1 ,1.2 ,1.3, \
                  1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]


def build_cmp_input(depth, observation_distance, configs):
    # build up pscmp input file

    dir = TEMP_PREFIX + 'cmp/' + str(depth)

    os.makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/cmp/
    # or the function will skip writing if there is any file in target folder
    if (len(os.listdir(dir)) != 0):
        print(f'INFO: cmp file for depth {depth} already exists, skipping...')
        return 0
    
    # calculate observation array
    observation_array = []
    with open(CONFIG_PREFIX + 'receiving_fault.dat', 'r') as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            observation_points = observation_array_on_fault(split_line, depth, observation_distance)
            for point in observation_points:
                observation_array.append(observation_points)

    with open(TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp', 'a') as cmp_input, \
        open(CONFIG_PREFIX + 'source_fault.dat', 'r') as source_fault:
        cmp_input.write('0\n')
        cmp_input.write(f'{len(observation_array)}\n')

        newline_count = 0
        for point in observation_array:
            newline_count += 1
            cmp_input.write(f'({point[0]}, {point[1]}) ')
            if (newline_count == 6): cmp_input.write('\n')
        
        cmp_input.write(f'\n{configs[0][0]}\n')
        if (configs[0][0] == 1): cmp_input.write(f'{configs[0][0]} {configs[0][1]} {configs[0][2]} {configs[0][3]}\n')
        cmp_input.write(f'{configs[1][0]}\n')
        if (configs[1][0] == 1): 
            cmp_input.write(f'{configs[1][0]} {configs[1][1]} {configs[1][2]} ')
            cmp_input.write(f'{configs[1][3]} {configs[1][4]} {configs[1][5]} ')
            cmp_input.write(f'{configs[1][6]} {configs[1][7]} {configs[1][8]}\n')
        
        cmp_input.write(f"'{TEMP_PREFIX}cmp/{depth}/'\n")
        cmp_input.write('0 0 0\n')
        cmp_input.write("'ux.dat' 'uy.dat' 'uz.dat'\n")
        cmp_input.write('0 0 0 0 0 0\n')
        cmp_input.write("'sxx.dat' 'syy.dat' 'szz.dat' 'sxy.dat' 'syz.dat' 'szx.dat'\n")
        cmp_input.write('0 0 0 0 0\n')
        cmp_input.write("'tx.dat' 'ty.dat' 'rot.dat' 'gd.dat' 'gr.dat'\n")
        cmp_input.write(f'{configs[2][0]}\n')

        snapshot_count = 0
        while (snapshot_count < int(configs[2][0])):
            cmp_input.write(f'{configs[3 + snapshot_count][0]} {configs[3 + snapshot_count][1]}\n')
            snapshot_count += 1
        
        cmp_input.write(f"'{TEMP_PREFIX}grn/{depth}/'\n")
        cmp_input.write("'uz' 'ur' 'ut'\n")
        cmp_input.write("'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n")
        cmp_input.write("'tr' 'tt' 'rot' 'gd' 'gr'\n")

        for line in source_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            cleaned_line = ' '.join(stripped_line.split())
            cmp_input.write(cleaned_line + '\n')

    if TEST: print(f'INFO: building pscmp input file for depth {depth_number}...')


if TEST:
    build_cmp_input(depth_number, 1.0, configs, True)