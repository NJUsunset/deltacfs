from src import constant, errors, logger_all, settings
from os import makedirs, listdir
import math

inp_log = logger_all.setlogger('input')


def build_grn_input(depth: float, calculation_settings: list[list[str]]) -> None:
    """
    build up psgrn input file in specified depth

    Args:
        depth(float):
        calculation_settings(list[list[str]]):
    
    Returns:
        (None)
    """
    dir = constant.TEMP_PREFIX + 'grn/' + settings.depth_name(depth)

    makedirs(dir, exist_ok=True)

    # skip if same depth
    if (listdir(dir)):
        inp_log.warning(f'grn file for depth {depth} already exists, \
                        folder path is {dir}, skipping...')
        return None
    
    # compose grn input file
    with open(dir.replace('grn/', 'grn_input/') + '.grn', 'a') as grn_input, \
        open(constant.CONFIG_PREFIX + 'model.dat', 'r') as model:
        
        grn_input.write(f'{depth} {calculation_settings[0][1]} \n')
        grn_input.write(f'{calculation_settings[1][0]} {calculation_settings[1][1]} {calculation_settings[1][2]} {calculation_settings[1][3]}\n')
        grn_input.write(f'{calculation_settings[2][0]} {calculation_settings[2][1]} {calculation_settings[2][2]}\n')
        grn_input.write(f'{calculation_settings[3][0]} {calculation_settings[3][1]}\n')
        grn_input.write(f'{calculation_settings[4][0]}\n')
        grn_input.write(f'{calculation_settings[5][0]}\n')
        grn_input.write(f"'{dir}/'\n")
        grn_input.write("'uz' 'ur' 'ut'\n" \
                        "'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n" \
                        "'tr' 'tt' 'rot' 'gd' 'gr'\n")
        
        # append model info from model.dat
        for line in model:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            cleaned_line = ' '.join(stripped_line.split())
            grn_input.write(cleaned_line + '\n')
    
    logger_all.logged_print(f'build psgrn input file for depth {depth}...', inp_log)



def build_cmp_input(depth: float, observe_points: list[tuple[float, float, float]], configs: list[list[str]]) -> None:
    """
    build up pscmp input file

    Args:
        depth(float):
        observe_points(list[tuple[float, float, float]]): store in (lon, lat, depth)
        configs(list[list[str]]):
    
    Returns:
        (None)
    """
    inp_log.debug(f'input parameters: depth {depth}, observe_points: {observe_points}, configs: {configs}')
    
    dir = constant.TEMP_PREFIX + 'cmp/' + settings.depth_name(depth)

    makedirs(dir, exist_ok=True)

    # skip if exist
    if (listdir(dir)):
        inp_log.warning(f'cmp file for depth number {depth} already exists, \
                        folder path is {dir}, skipping...')
        return None

    with open(dir.replace('cmp/', 'cmp_input/'), 'a') as cmp_input, open(constant.CONFIG_PREFIX + 'source_fault.dat', 'r') as source_fault:
        cmp_input.write('0\n')
        cmp_input.write(f'{len(observe_points)}\n')

        newline_count = 0
        for point in observe_points:
            newline_count += 1
            cmp_input.write(f'{(point[0], point[2])}')
            cmp_input.write('\n') if newline_count == 6 else cmp_input.write(' ')
        
        cmp_input.write(f'\n{configs[0][0]}\n')
        if (configs[0][0] == 1): cmp_input.write(f'{configs[0][0]} {configs[0][1]} {configs[0][2]} {configs[0][3]}\n')
        cmp_input.write(f'{configs[1][0]}\n')
        if (configs[1][0] == 1): 
            cmp_input.write(f'{configs[1][0]} {configs[1][1]} {configs[1][2]} ')
            cmp_input.write(f'{configs[1][3]} {configs[1][4]} {configs[1][5]} ')
            cmp_input.write(f'{configs[1][6]} {configs[1][7]} {configs[1][8]}\n')
        
        cmp_input.write(f"'{dir}/'\n")
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
        
        cmp_input.write(f"'{dir.replace('cmp/', 'grn/')}/'\n")
        cmp_input.write("'uz' 'ur' 'ut'\n")
        cmp_input.write("'szz' 'srr' 'stt' 'szr' 'srt' 'stz'\n")
        cmp_input.write("'tr' 'tt' 'rot' 'gd' 'gr'\n")

        for line in source_fault:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('#'):
                continue
            cleaned_line = ' '.join(stripped_line.split())
            cmp_input.write(cleaned_line + '\n')

    logger_all.logged_print(f'build pscmp input file for depth {depth}...', inp_log)