from src import constant, exception_process
import logging

def timer(func):
    """
    decorator to measure function working time and record them
    """
    def wrapper(*args, **kwargs):
        import time, inspect
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        params = bound_args.arguments
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logged_print(f"{func.__name__} active time: {end-start:.6f}s", params['logger'])
        return result
    return wrapper


def initlogger(file_level=logging.INFO, console_level=logging.WARNING) -> logging.Logger:
    '''
    initialize log module, create log file 
    
    create log folder, create main function logger

    Args:
        file_level(int): log level for log file, must chosen in logging.DEBUG, logging.INFO, logging.WARNING and logging.ERROR
        console_level(int): log level for console prompt, must chosen in logging.DEBUG, logging.INFO, logging.WARNING and logging.ERROR
    
    Returns:
        logger(logging.Logger): main function logger
    
    Raises:
        exception_process.FunctionRuningError: if function raise Exception type other than exception_process.InputValueError

    Notes: log file will be stored in ./LOG_PREFIX/ folder
    '''
    try:
        # input value check
        if not file_level == (logging.DEBUG or logging.INFO or logging.WARNING): raise exception_process.InputValueError('initlogger')
        if not console_level == (logging.DEBUG or logging.INFO or logging.WARNING): raise exception_process.InputValueError('initlogger')

        # create log folder to store file
        from os import makedirs
        makedirs(constant.LOG_PREFIX, exist_ok=True)

        # create main logger and set to record all log info
        logger = logging.getLogger('main')
        logger.setLevel(logging.DEBUG)

        from datetime import datetime
        file_handler = logging.FileHandler(constant.LOG_PREFIX + f'Calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log')
        file_handler.setLevel(file_level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
    
    except exception_process.InputValueError as e:
        print('Bad input for initialising log system, please check code, program exiting')
        exit()
    
    except Exception as e:
        raise exception_process.FunctionRunningError('initlogger', e)


def setlogger(name='UnknownModule') -> logging.Logger:
    '''
    automatic create subloggers under main function
    
    Args:
        name(str): the name used to mark this sub logger
    
    Returns:
        logger(logging.Logger):
    '''
    logger = logging.getLogger('main.' + name)
    
    return logger

@timer
def logged_run(command, logger) -> int:
    '''
    run os code and record output

    Args:
        command(list[str]): a list combined with code section, segregation respect \
            with space when them are typed in console
        logger(logging.Logger): 
    
    Returns:
        returncode(int): mark whether command run sucessfully
    '''
    import subprocess, threading
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
        args=(process.stdout, logging.DEBUG)
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
        raise exception_process.CommandRunningError(logged_run, command)
    else:
        logger.info(f"program exit with success when running command {command}")
        
    return process.returncode


def logged_input(prompt, logger, valid_input):
    while True:
        try:
            print(prompt, end='', flush=True)
            
            user_input = input()
            
            logger.info(f"INPUT PROMPT: {prompt.rstrip()}")
            logger.info(f"USER RESPONSE: {user_input}")

            if user_input in valid_input:
                return user_input
            else:
                raise exception_process.InputValueError(logged_input)
        
        except exception_process.InputValueError as e:
            logger.warning(e)
            logged_print('Bad input, please retry', logger)


def logged_print(prompt, logger):
    logger.info(prompt)
    print(prompt)
    return 0