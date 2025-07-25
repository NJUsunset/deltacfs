from src import constant, errors, logger_all, settings
from os import makedirs, listdir

grn_log = logger_all.setlogger('grn_input')


def build_grn_input(depth, calculation_settings):
    # build up psgrn input file in specified depth

    dir = constant.TEMP_PREFIX + 'grn/' + str(depth)

    makedirs(dir, exist_ok=True)

    # override option will override any possible exist former file in temp/grn/
    # or the function will skip writing if there is any file in target folder
    if (listdir(dir)):
        grn_log.warning(f'grn file for depth {depth} already exists, skipping...')
        return 0
    
    # compose grn input file
    with open(constant.TEMP_PREFIX + 'grn_input/' + str(depth) + '.grn', 'a') as grn_input, \
        open(constant.CONFIG_PREFIX + 'model.dat', 'r') as model:
        
        try:
            grn_input.write(f'{depth} {calculation_settings[0][1]} \n')
            grn_input.write(f'{calculation_settings[1][0]} {calculation_settings[1][1]} {calculation_settings[1][2]} {calculation_settings[1][3]}\n')
            grn_input.write(f'{calculation_settings[2][0]} {calculation_settings[2][1]} {calculation_settings[2][2]}\n')
            grn_input.write(f'{calculation_settings[3][0]} {calculation_settings[3][1]}\n')
            grn_input.write(f'{calculation_settings[4][0]}\n')
            grn_input.write(f'{calculation_settings[5][0]}\n')
            grn_input.write(f"'{constant.TEMP_PREFIX}grn/{depth}/'\n")
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
        
        except Exception as e:
            raise errors.FuncError('build_grn_input')
    
    logger_all.logged_print(f'build psgrn input file for depth {depth}...', grn_log)

    return dir