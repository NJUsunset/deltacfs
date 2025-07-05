import logging
import subprocess
import threading
import datetime
import os
from src import constant

def setlogger():
    os.makedirs(constant.LOG_PREFIX, exist_ok=True)
    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)

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
    try:
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
            raise Exception('code running error')
        else:
            logger.info(f"program exit with success when running command {command}")
            
        return process.returncode
    
    except Exception as e:
        logger.exception(f"unknown error")


def logged_input(prompt, logger):
    while True:
        try:
            print(prompt, end='', flush=True)
            
            user_input = input()
            
            logger.info(f"INPUT PROMPT: {prompt.rstrip()}")
            logger.info(f"USER RESPONSE: {user_input}")
            
            if user_input != ('y' or 'no-override' or 'n'):
                logger.error('Bad input')
                raise ValueError
            else:
                return user_input
        
        except ValueError as e:
            print('Bad input, please retry')
        
        except KeyboardInterrupt:
            print('User keyboard interupt, exiting...')
            exit(0)
    