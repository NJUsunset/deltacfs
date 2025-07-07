from src import constant, error
from enum import Enum
import logging
import subprocess
import threading


class Log_level(Enum):
    DEBUG = 5
    INFO = 6
    WARNING = 7

def setlogger(level=Log_level.INFO):
    
    assert level == (Log_level.DEBUG or Log_level.INFO or Log_level.WARNING)

    from os import makedirs
    makedirs(constant.LOG_PREFIX, exist_ok=True)
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)

    from datetime import datetime
    file_handler = logging.FileHandler(constant.LOG_PREFIX + f'Calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log')
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def logged_run(logger, command):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    def log_stream(stream, level):
        for line in iter(stream.readline, ''):
            cleaned_line = line.rstrip('\n')
            if cleaned_line:
                logger.log(level, cleaned_line)
    
    stdout_thread = threading.Thread(
        target=log_stream, 
        args=(process.stdout, logging.INFO)
    )
    stderr_thread = threading.Thread(
        target=log_stream, 
        args=(process.stderr, logging.ERROR)
    )
    
    stdout_thread.start()
    stderr_thread.start()
    
    process.wait()
    
    stdout_thread.join()
    stderr_thread.join()
    
    if process.returncode != 0:
        logger.error(f"program exit with error when running command {command} with exit code {process.returncode}")
        raise error.CommandRunningError(logged_run, command)
    else:
        logger.info(f"program exit with success when running command {command}")
        
    return process.returncode


def logged_input(prompt, logger):
    while True:
        try:
            print(prompt, end='', flush=True)
            
            user_input = input()
            
            logger.info(f"INPUT PROMPT: {prompt.rstrip()}")
            logger.info(f"USER RESPONSE: {user_input}")
            
            valid_input = ['y', 'no-override', 'n']

            if user_input in valid_input:
                return user_input
            else:
                raise error.InputValueError(logged_input)
        
        except error.InputValueError as e:
            logger.warning(e)
            print('Bad input, please retry')
        
        except KeyboardInterrupt as e:
            logger.warning(e)
            logger.warning('program exiting')
            print('User keyboard interupt, program exiting...')
            exit(0)

def logged_print(prompt, logger):
    logger.info(prompt)
    print(prompt)

    return 0