from src import constant, errors, logger_all
from typing import Callable
import logging


settings_log = logger_all.setlogger('settings')



def depth_name(depth: float) -> str:
    """
    turn float depth into string form and replace . with _ to avoid suffix problem

    Args:
        depth(float):
    
    Returns:
        depth_name(str)
    
    Raises:
        errors.OverlimitError: raise when depth minus zero
    """
    try:
        assert depth >= 0.0
        return f'{depth:.2f}'.replace('.', '_')
    
    except AssertionError as e:
        raise errors.OverlimitError from e



def interact_and_clean(logger: logging.Logger) -> None:
    """
    ask user to save data and make clean

    Args:
        logger(logging.Logger)
    
    Returns:
        (None)
    
    Raises:
        errors.InputError:
        errors.FuncError:
        errors.UnexpectedError:
    """
    try:
        valid_input = ['Confirm', 'ALL', 'exit']
        run = logger_all.logged_input('The program will erase all file in output adn temp folder\n \
                                        all privious data will be loss, please save them before further action\n \
                                        type Confirm below to make further run, \
                                        ALL option will additionally clean log file: (Confirm/ALL/exit)\n', logger, valid_input)

        from shutil import rmtree
        try:
            if run == 'exit':
                logger_all.logged_print('accept input to exit program, program stopping...', logger)
                exit()
            elif run == 'Confirm':
                logger_all.logged_print('accept confirmation, program cleaning...', logger)
                logger.debug('cleaning existing green function set...')
                rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
                rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
                logger.debug('cleaning existing deltacfs...')
                rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
                rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
                logger.debug('cleaning existing output file...')
                rmtree(constant.OUTPUT_PREFIX, ignore_errors=True)
                logger.info('clean process finished')
            elif run == 'ALL':
                logger_all.logged_print('accept all clean confirmation, program cleaning...', logger)
                logger.debug('cleaning existing green function set...')
                rmtree(constant.TEMP_PREFIX + 'grn/', ignore_errors=True)
                rmtree(constant.TEMP_PREFIX + 'grn_input/', ignore_errors=True)
                logger.debug('cleaning existing deltacfs...')
                rmtree(constant.TEMP_PREFIX + 'cmp/', ignore_errors=True)
                rmtree(constant.TEMP_PREFIX + 'cmp_input/', ignore_errors=True)
                logger.debug('cleaning existing output file...')
                rmtree(constant.OUTPUT_PREFIX, ignore_errors=True)
                logger.debug('cleaning existing log file...')
                rmtree(constant.LOG_PREFIX, ignore_errors=True)
                logger.info('clean process finished')
        
        except Exception as e:
            raise errors.FuncError('rmtree') from e
    
    except (errors.InputError, errors.FuncError, errors.UnexpectedError) as e:
        raise e
    
    except Exception as e:
        raise errors.UnexpectedError



def empty_assertion(r_settings: list[list[str]]) -> None: ...



def calculation_setting_assertion(r_settings: list[list[str]]) -> None:
    """
    assertion func for calculation_setting data check, only function when quoted by read_settings

    Args:
        r_settings(list[list[str]]): input data to check
    
    Returns:
        (None)
    
    Raises:
        AsssertionError:
    
    Note:
        need to be sure data structure is correct MANUALLY or program will raise errors.UnexpectedError
    """
    assert r_settings, 'input parameter'
    assert float(r_settings[0][0]) > 0.1, 'interval maxinum'
    assert constant.TOF.contains(int(r_settings[0][1])), 'continent/ocean switch'
    assert float(r_settings[1][1]) <= float(r_settings[1][2]), 'horizontal distance'
    assert float(r_settings[1][3]) >= 1.0, 'sample ratio'
    assert int(r_settings[2][0]) >= 1
    assert float(r_settings[2][1]) <= float(r_settings[2][2])
    assert constant.AC.contains(float(r_settings[4][0]))
    assert constant.ZO.contains(float(r_settings[5][0]))



def config_assertion(r_settings: list[list[str]]) -> None:
    """
    assertion func for config.json data check, only function when quoted by read_settings

    Args:
        r_settings(list[list[str]]): input data to check
    
    Returns:
        (None)
    
    Raises:
        AsssertionError:
    
    Note:
        need to be sure data structure is correct MANUALLY or program will raise errors.UnexpectedError
    """
    assert r_settings, 'input parameter'
    assert constant.TOF.contains(int(r_settings[0][0])), 'insar(1/0)'
    if len(r_settings[0]) > 1:
        assert constant.COS.contains(float(r_settings[0][1])), 'insar cosine value'
        assert constant.COS.contains(float(r_settings[0][2])), 'insar cosine value'
        assert constant.COS.contains(float(r_settings[0][3])), 'insar cosine value'
    assert constant.TOF.contains(int(r_settings[1][0])), 'icmb'
    if len(r_settings[1]) > 1:
        assert float(r_settings[1][1]) > 0, 'friction factor'
        assert constant.ANGLE1.contains(float(r_settings[1][3])), 'strike'
        assert constant.ANGLE2.contains(float(r_settings[1][4])), 'dip'
        assert constant.ANGLE3.contains(float(r_settings[1][5])), 'slip'



def prepare_observe_points(receive_fault: list[str], observe_max_interval: float) -> tuple[list[float], list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    '''
    generate observe points with fault parameter receving

    using transform between espg:32650 and espg:4326 to generate observe points respect rectangular mesh, \
    will return depth list, vertice list and observe points list

    Args:
        receive_fault(list[str]): parameters of receive fault, should be list in order of \
            longtitude, latitude, depth, length, width, strike and dip
        observe_max_interval(float): the ceiling of intervals between two closest observe points, unit in kelometer and must > 0.1
    
    Returns:
        tuple:
            - depth_list(list[float]): observe points depth which covers every observe points
            - vertice(list[tuple]): points which belongs to rectangulars that descrete fault plane
            - observe_points(list[tuple]): observe points at the centre of those rectangulars
    
    Raises:
        errors.InputError:
        errors.OutputError:
        errors.FuncError:
        errors.MathError: 
        errors.OverlimitError: if calculated interval dont meet given max interval
        errors.UnexpectedError:
    '''
    try:
        # changing this value to control length/width ratio of mesh unit. when equals 1.0, the unit is square
        observation_rec_ratio = 1.0

        # preparing empty list
        depth_list: list[float] = []
        vertice: list[tuple] = []
        observe_points: list[tuple] = []

        try:
            # reading data from receive_fault list and turn strings into float for calculation
            O_lon = float(receive_fault[1])
            O_lat = float(receive_fault[2])
            O_depth = float(receive_fault[3])
            length = float(receive_fault[4])
            width = float(receive_fault[5])
            strike = float(receive_fault[6])
            dip_angle = float(receive_fault[7])

            assert observe_max_interval >= 0.1
        
        except AssertionError as e:
            raise errors.InputError('observe_max_interval')
        
        except Exception as e:
            raise errors.InputError('receive_fault')


        settings_log.debug(f'receive_fault read result: O_lon: {O_lon}, O_lat: {O_lat}, O_depth: {O_depth}, \
                        length: {length}, width: {width}, strike: {strike}, dip_angle: {dip_angle}')


        # construct transform
        try:
            from pyproj import Proj, Transformer
            proj_ll = Proj("epsg:4326")
            proj_xy = Proj("epsg:32648") # EPSG：32648 covers 102°E to 108°E in northern hemisphere, unit in meter, be caution!
            ll2xy = Transformer.from_proj(proj_ll, proj_xy, always_xy=True)
            xy2ll = Transformer.from_proj(proj_xy, proj_ll, always_xy=True)

        except Exception as e:
            raise errors.FuncError('pyproj transform') from e


        try:
            # transform start point to local coordinate
            O_lon_local, O_lat_local= ll2xy.transform(O_lon, O_lat)
            
            # find number of points in horizontal direction and vertical direction
            from math import ceil
            hori_number = ceil(length/(observe_max_interval * observation_rec_ratio))
            verti_number = ceil(width/observe_max_interval)
        
        except Exception as e:
            raise errors.MathError from e


        settings_log.debug(f'horizontal_interval: {length/hori_number}, vertical_interval: {width/verti_number}')

        try:
            # assure actual interval meet max interval
            assert width/verti_number <= observe_max_interval, 'vertical interval oversize'
            assert length/hori_number <= observe_max_interval * observation_rec_ratio, 'horizontal interval oversize'

        except AssertionError as e:
            raise errors.OverlimitError from e
        

        try:
            from numpy import linspace
            xs_local = linspace(O_lon_local, O_lon_local + length*1000, hori_number + 1)
            ys_local = linspace(O_lat_local, O_lat_local + width*1000, verti_number + 1)

            from math import tan, radians
            for j in range(verti_number):
                for i in range(hori_number):
                    vertex_lon, vertex_lat = xy2ll.transform(xs_local[i], ys_local[j])
                    vertex_depth = O_depth + width / verti_number * j / tan(radians(dip_angle))
                    vertice.append((vertex_lon, vertex_lat, vertex_depth))
                    settings_log.debug(f'vertice: ({vertex_lon}, {vertex_lat}, {vertex_depth})')

            for j in range(verti_number - 1):
                for i in range(hori_number - 1):
                    op_lon, op_lat = xy2ll.transform(0.5*(xs_local[i] + xs_local[i+1]), 0.5*(ys_local[j] + ys_local[i+1]))
                    op_depth = O_depth + width / verti_number * (j+0.5) / tan(radians(dip_angle))
                    observe_points.append((op_lon, op_lat, op_depth))
                    depth_list.append(op_depth)
                    settings_log.debug(f'observation_point: ({op_lon}, {op_lat}, {op_depth})')
        
        except Exception as e:
            raise errors.MathError from e
        

        try:
            assert depth_list, 'depth list empty'
            assert vertice, 'vertice empty'
            assert observe_points, 'observe points empty'
        
        except AssertionError as e:
            raise errors.OutputError from e


        settings_log.debug(f'depth list construct result: {depth_list}')
        settings_log.debug(f'vertice construct result: {vertice}')
        settings_log.debug(f'observe points construct result: {observe_points}')

        return depth_list, vertice, observe_points

    except (errors.InputError, errors.OutputError, errors.FuncError, errors.MathError, errors.OverlimitError) as e:
        raise e
    
    except Exception as e:
        raise errors.UnexpectedError from e



def read_settings(file_name: str, assertion: Callable[[list[list[str]]], None] = empty_assertion) -> list[list[str]]:
    """
    read and return settings from given file in LOG_PREFIX

    Args:
        file_name(str): the config file name with suffix in CONFIG_PREFIX to read
        assertion(Callable[[list[list[str]]], None]): the assertion to justify output data
    
    Returns:
        r_settings(list[list[str]])

    Returns:
        errors.InputError:
        errors.FuncError:
        errors.UnexpectedError:                                                                     
    """
    try:
        r_settings: list[list[str]] = []

        try:
            with open(constant.CONFIG_PREFIX + file_name, 'r') as read_setting:
                for line in read_setting:
                    if not line.strip() or line.startswith('#'):
                        continue
                    values = line.strip().split()
                    r_settings.append(values)
        
        except Exception as e:
            raise errors.FuncError from e

        try:
            assertion(r_settings)

        except AssertionError as e:
            raise errors.InputError from e

        settings_log.debug(f'print read_settings output: read_settings {r_settings}')

        return r_settings
    
    except (errors.InputError, errors.FuncError) as e:
        raise e
    
    except Exception as e:
        raise errors.UnexpectedError from e



def combine_file(filename, depth):
    
    settings_log.debug(f'will operate file {constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename}')
    
    from os.path import exists
    assert exists(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename), f'empty output file in {depth}'

    with open(constant.TEMP_PREFIX + 'cmp/' + str(depth) + '/' + filename, 'r') as read_file, \
        open(constant.OUTPUT_PREFIX + filename, 'a') as write_file:
        
        with open(constant.OUTPUT_PREFIX + filename, 'r') as temp_file:
            if (not temp_file.read()):
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