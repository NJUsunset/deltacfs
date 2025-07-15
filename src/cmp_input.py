from src import constant, exception_process, logger_all, settings
from os import makedirs, listdir
import math

cmp_log = logger_all.setlogger('cmp_input')

def build_cmp_input(depth_number, observation_points_array, configs):
    # build up pscmp input file

    cmp_log.debug(f'input parameters: depth {depth_number}, configs: {configs}')
    
    dir = constant.TEMP_PREFIX + 'cmp/' + str(depth_number)

    makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/cmp/
    # or the function will skip writing if there is any file in target folder
    if (len(listdir(dir)) != 0):
        cmp_log.warning(f'cmp file for depth number {depth_number} already exists, skipping...')
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
                vertice, observation_points = settings.observation_array_on_fault(split_line, observation_max_interval)
                observation_array.extend(observation_points)

            except AssertionError as e:
                cmp_log.warning(f'observation array walking out of receiving fault, reason: {e}, skip this point')
    
    assert len(observation_array) > 0, 'observation_array empty'
    
    cmp_log.debug(f'observation_array construct result: {observation_array}')

    with open(constant.TEMP_PREFIX + 'cmp_input/' + str(depth_number) + '.cmp', 'a') as cmp_input, open(constant.CONFIG_PREFIX + 'source_fault.dat', 'r') as source_fault:
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
            
            cmp_input.write(f"'{constant.TEMP_PREFIX}cmp/{depth_number}/'\n")
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
            
            cmp_input.write(f"'{constant.TEMP_PREFIX}grn/{depth_number}/'\n")
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
            raise exception_process.FunctionRunningError('build_cmp_input(write)')

    logger_all.logged_print(f'build pscmp input file for depth number {depth_number}...', cmp_log)