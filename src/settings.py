from src import constant, exception_process, logger_all
from pyproj import Proj, Transformer
from os.path import exists
import math

settings_log = logger_all.setlogger('settings')

def prepare_observe_points(receive_fault, observation_max_interval) -> tuple:
    '''
    generate observe points with fault parameter receving

    using transform between espg:32650 and espg:4326 to generate observe points respect rectangular mesh, \
    will return depth list, vertice list and observe points list in a tuple

    Args:
        receive_fault(array): parameters of receive fault, should be list in order of \
            longtitude, latitude, depth, length, width, strike and dip
        observation_max_interval(float): the ceiling of intervals between two closest observe points, unit in kelometer
    
    Returns:
        tuple: including three lists:
            - depth_list(list[float]): list of observe points depth which covers all observe points
            - vertice(list[tuple]): list of points which belongs to rectangulars that descrete fault plane
            - observe_points(list[tuple]): list of observe points, which is in the centre of those rectangulars
    
    Raises:
        exception_process.FunctionRuningError: if function raise Exception
    '''
    
    # changing this value to control length/width ratio of mesh unit. when equals 1.0, the unit is square
    observation_rec_ratio = 1.0

    # preparing empty list
    depth_list = []
    vertice = []
    observe_points = []

    # reading data from receive_fault list and turn strings into float for calculation
    O_lon = float(receive_fault[1])
    O_lat = float(receive_fault[2])
    O_depth = float(receive_fault[3])
    length = float(receive_fault[4])
    width = float(receive_fault[5])
    strike = float(receive_fault[6])
    dip_angle = float(receive_fault[7])

    settings_log.debug(f'receive_fault read result: O_lon: {O_lon}, O_lat: {O_lat}, O_depth: {O_depth}, \
                       length: {length}, width: {width}, strike: {strike}, dip_angle: {dip_angle}')

    # construct transform
    proj_ll = Proj("epsg:4326")
    proj_xy = Proj("epsg:32648") # EPSG：32648 covers 102°E to 108°E in northern hemisphere, unit in meter, be caution!
    ll2xy = Transformer.from_proj(proj_ll, proj_xy, always_xy=True)
    xy2ll = Transformer.from_proj(proj_xy, proj_ll, always_xy=True)

    # transform start point to local coordinate
    O_lon_local, O_lat_local = ll2xy.transform(O_lon, O_lat)
    
    # find number of points in horizontal direction and vertical direction
    hori_number = math.ceil(length/(observation_max_interval * observation_rec_ratio))
    verti_number = math.ceil(width/observation_max_interval)

    settings_log.debug(f'horizontal_interval: {length/hori_number}, vertical_interval: {width/verti_number}')

    # assure actual interval meet max interval
    assert width/verti_number <= observation_max_interval, 'vertical interval oversize'
    assert length/hori_number <= observation_max_interval * observation_rec_ratio, 'horizontal interval oversize'
    
    from numpy import linspace
    xs_local = linspace(O_lon_local, O_lon_local + length*1000, hori_number + 1)
    ys_local = linspace(O_lat_local, O_lat_local + width*1000, verti_number + 1)

    for j in range(verti_number):
        for i in range(hori_number):
            vertex_lon, vertex_lat = xy2ll.transform(xs_local[i], ys_local[j])
            vertex_depth = O_depth + width / verti_number * j / math.tan(math.radians(dip_angle))
            vertice.append((vertex_lon, vertex_lat, vertex_depth))
            settings_log.debug(f'vertice: ({vertex_lon}, {vertex_lat}, {vertex_depth})')

    for j in range(verti_number - 1):
        for i in range(hori_number - 1):
            op_lon, op_lat = xy2ll.transform(0.5*(xs_local[i] + xs_local[i+1]), 0.5*(ys_local[j] + ys_local[i+1]))
            op_depth = O_depth + width / verti_number * (j+0.5) / math.tan(math.radians(dip_angle))
            observe_points.append((op_lon, op_lat, op_depth))
            depth_list.append(op_depth)
            settings_log.debug(f'observation_point: ({op_lon}, {op_lat}, {op_depth})')

    settings_log.debug(f'depth list construct result: {depth_list}')
    settings_log.debug(f'vertice construct result: {vertice}')
    settings_log.debug(f'observe points construct result: {observe_points}')

    return depth_list, vertice, observe_points


def depth_minmax(): 
    # get min and max depth from file "receive_fault.dat", return array (depth_min, depth_max)
    depth = []
    depth_stretch = []
    with open(constant.CONFIG_PREFIX + 'receive_fault.dat', 'r') as receive_fault:
        for line in receive_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            split_line = stripped_line.split()
            depth.append(float(split_line[3]))
            depth_stretch.append(float(split_line[3]) + float(split_line[5]) * math.sin(math.radians(float(split_line[7]))))

    settings_log.debug(f'print depth_minmax reading result: O_depth {depth}, dip {depth_stretch}')

    depth_min = math.floor(min([min(depth), min(depth_stretch)]))
    depth_max = math.ceil(max([max(depth), max(depth_stretch)]))
    depth_range = [depth_min, depth_max]

    assert depth_min >= 0, 'depth_min'
    assert depth_max > depth_min, 'depth_range'

    settings_log.debug(f'print depth_minmax calculation result: depth_stretch {depth_stretch}, depth_range {depth_range}')

    return depth_range


def calculation_setting():
    # read calculation settings from file "calculation_setting.dat", return a float depth_step and a list storing other info

    calculation_settings = []

    with open(constant.CONFIG_PREFIX + 'calculation_setting.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            calculation_settings.append(values)
    depth_step = float(calculation_settings[0][0])

    assert depth_step > 0, 'depth_step'

    settings_log.debug(f'print calculation_setting output: depth_step {depth_step}, calculation_settings {calculation_settings}')

    return depth_step, calculation_settings



def config():
    # read config.dat file and return a list with info
    configs = []

    with open(constant.CONFIG_PREFIX + 'config.dat', 'r') as calculation_setting:
        for line in calculation_setting:
            if not line.strip() or line.startswith('#'):
                continue
            values = line.strip().split()
            configs.append(values)
    
    settings_log.debug(f'config.dat read result: {configs}')

    assert constant.TOF.contains(int(configs[0][0])), 'insar(1/0)'
    if len(configs[0]) > 1:
        assert constant.COS.contains(float(configs[0][1])), 'insar cosine value'
        assert constant.COS.contains(float(configs[0][2])), 'insar cosine value'
        assert constant.COS.contains(float(configs[0][3])), 'insar cosine value'
    assert constant.TOF.contains(int(configs[1][0])), 'icmb'
    if len(configs[1]) > 1:
        assert float(configs[1][1]) > 0, 'friction factor'
        assert constant.ANGLE1.contains(float(configs[1][3])), 'strike'
        assert constant.ANGLE2.contains(float(configs[1][4])), 'dip'
        assert constant.ANGLE3.contains(float(configs[1][5])), 'slip'
    
    settings_log.debug(f'configs: {configs}')

    return configs

def combine_file(filename, depth):
    
    settings_log.debug(f'will operate file {constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename}')
    
    assert exists(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename), f'empty output file in {depth}'

    with open(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename, 'r') as read_file, \
        open(constant.OUTPUT_PREFIX + filename, 'a') as write_file:
        
        with open(constant.OUTPUT_PREFIX + filename, 'r') as temp_file:
            if (temp_file.read() == ''):
                settings_log.debug(f'{filename} is found empty when processing depth {depth}, preparing to write title in it')
                write_file.write('depth[km] ')
                write_file.write(read_file.readline())
            
        for i, line in enumerate(read_file):
            if i <= 2: continue

            stripped_line = line.strip()
            cleaned_line = ' '.join(stripped_line.split())
            write_file.write(str(depth) + ' ')
            write_file.write(cleaned_line + '\n')
    
    settings_log.debug(f'successfully rewrite file {filename} at depth {depth} to output file')