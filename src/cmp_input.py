from src import constant, error, logger_all
from pyproj import Geod
from os import makedirs, listdir
import math

cmp_log = logger_all.setlogger('cmp_input')

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

    cmp_log.debug(f'receiving_fault_array read result: O_lon: {O_lon}, O_lat: {O_lat}, O_depth: {O_depth}, length: {length}, width: {width}, strike: {strike}, dip_angle: {dip_angle}')

    geod = Geod(ellps="WGS84")

    depth_diff = target_depth - O_depth
    horizontal_offset = depth_diff / math.tan(math.radians(dip_angle))
    width_offset = depth_diff / math.sin(math.radians(dip_angle))

    if math.isnan(horizontal_offset): raise error.FunctionRunningError('observation_array_on_fault')
    if math.isnan(width_offset): raise error.FunctionRunningError('observation_array_on_fault')

    cmp_log.debug(f'depth_diff: {depth_diff}, horizontal_offset: {horizontal_offset}, width_offset: {width_offset}')
    
    assert depth_diff >= 0, 'depth_diff overwhelm'
    assert width_offset <= width, 'width_offset overwhelm'

    # Determine the starting point's projection at the target depth
    proj_lon, proj_lat, _ = geod.fwd(O_lon, O_lat, (strike + 90) % 360, horizontal_offset * 1000)
    proj_lon, proj_lat = (round(proj_lon, 4), round(proj_lat, 4))

    if math.isnan(proj_lon) or math.isnan(proj_lat):
        raise error.FunctionRunningError('observation_array_on_fault')

    cmp_log.debug(f'proj_lon, proj_lat: {proj_lon}, {proj_lat}')

    # Generate points along the fault's strike direction
    num_points = int(length / observation_distance) + 1

    assert num_points > 2

    cmp_log.debug(f'num_points: {num_points}')

    for i in range(num_points):
        distance_along_strike = i * observation_distance
        point_lon, point_lat, _ = geod.fwd(proj_lon, proj_lat, strike, distance_along_strike * 1000)
        if math.isnan(point_lon) or math.isnan(point_lat):
            raise error.FunctionRunningError('observation_array_on_fault')
        point_lon, point_lat = (round(point_lon, 4), round(point_lat, 4))

        cmp_log.debug(f'distance_along_strike: {distance_along_strike}, point_lon, point_lat: {point_lon} {point_lat}')

        observation_points.append((point_lon, point_lat))

    cmp_log.debug(f'observation_points construct result: {observation_points}')

    return observation_points


def build_cmp_input(depth, observation_distance, configs):
    # build up pscmp input file

    cmp_log.debug(f'input parameters: depth {depth}, observation_distance: {observation_distance}, configs: {configs}')
    
    dir = constant.TEMP_PREFIX + 'cmp/' + str(depth)

    makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/cmp/
    # or the function will skip writing if there is any file in target folder
    if (len(listdir(dir)) != 0):
        cmp_log.warning(f'cmp file for depth {depth} already exists, skipping...')
        return 0
    
    # calculate observation array
    observation_array = []
    with open(constant.CONFIG_PREFIX + 'receiving_fault.dat', 'r') as receiving_fault:
        for line in receiving_fault:
            stripped_line = line.strip()
            
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            
            try:
                observation_points = observation_array_on_fault(split_line, depth, observation_distance)
                observation_array.extend(observation_points)

            except AssertionError as e:
                cmp_log.warning(f'observation array walking out of receiving fault, reason: {e}, skip this point')
    
    assert len(observation_array) > 0, 'observation_array empty'
    
    cmp_log.debug(f'observation_array construct result: {observation_array}')

    with open(constant.TEMP_PREFIX + 'cmp_input/' + str(depth) + '.cmp', 'a') as cmp_input, open(constant.CONFIG_PREFIX + 'source_fault.dat', 'r') as source_fault:
        try:
            cmp_input.write('0\n')
            cmp_input.write(f'{len(observation_array)}\n')

            newline_count = 0
            for point in observation_array:
                newline_count += 1
                cmp_input.write(f'{point}')
                cmp_input.write('\n') if newline_count == 6 else cmp_input.write(' ')
            
            cmp_input.write(f'\n{configs[0][0]}\n')
            if (configs[0][0] == 1): cmp_input.write(f'{configs[0][0]} {configs[0][1]} {configs[0][2]} {configs[0][3]}\n')
            cmp_input.write(f'{configs[1][0]}\n')
            if (configs[1][0] == 1): 
                cmp_input.write(f'{configs[1][0]} {configs[1][1]} {configs[1][2]} ')
                cmp_input.write(f'{configs[1][3]} {configs[1][4]} {configs[1][5]} ')
                cmp_input.write(f'{configs[1][6]} {configs[1][7]} {configs[1][8]}\n')
            
            cmp_input.write(f"'{constant.TEMP_PREFIX}cmp/{depth}/'\n")
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
            
            cmp_input.write(f"'{constant.TEMP_PREFIX}grn/{depth}/'\n")
            cmp_input.write("'uz' 'ur' 'ut'\n")
            cmp_input.write("'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n")
            cmp_input.write("'tr' 'tt' 'rot' 'gd' 'gr'\n")

            for line in source_fault:
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith('#'):
                    continue
                cleaned_line = ' '.join(stripped_line.split())
                cmp_input.write(cleaned_line + '\n')
        
        except Exception as e:
            raise error.FunctionRunningError('build_cmp_input(write)')

    logger_all.logged_print(f'build pscmp input file for depth {depth}...', cmp_log)