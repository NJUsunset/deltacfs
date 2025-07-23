from src import constant, errors
from typing import Callable, Any, IO
import logging



def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    decorator to measure function working time and record them
    """
    def wrapper(*args, **kwargs) -> Callable[..., Any]:
        import time, inspect
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        params = bound_args.arguments
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logged_print(f'{func.__name__} active time: {end-start:.6f}s', params['logger'])
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
        errors.InputError:
        errors.FuncError:
        errors.UnexpectedError:

    Notes: log file will be stored in constant.LOG_PREFIX folder
    '''
    try:
        try:
            # input value check
            valid_input = [logging.DEBUG, logging.INFO, logging.WARNING]
            assert file_level in valid_input 
            assert console_level in valid_input

        except AssertionError as e:
            raise errors.InputError from e


        # create log folder to store file
        try:
            from os import makedirs
            makedirs(constant.LOG_PREFIX, exist_ok=True)

        except Exception as e:
            raise errors.FuncError('make dir') from e


        # create main logger and set to record all log info
        logger = logging.getLogger('main')
        logger.setLevel(logging.DEBUG)
        
        try:
            from datetime import datetime
            file_handler = logging.FileHandler(constant.LOG_PREFIX + f'Calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log')
            file_handler.setLevel(file_level)
        
        except Exception as e:
            raise errors.FuncError('create log file') from e


        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
    
    except (errors.InputError, errors.FuncError) as e:
        raise e

    except Exception as e:
        raise errors.UnexpectedError('logger create') from e



def setlogger(name='UnknownModule') -> logging.Logger:
    '''
    automatic create subloggers under main function
    
    Args:
        name(str): the name used to mark this sub logger
    
    Returns:
        logger(logging.Logger):
    
    Raises:
        errors.UnexpectedError:
    '''
    try:
        logger = logging.getLogger('main.' + name)
        
        return logger
    
    except Exception as e:
        raise errors.UnexpectedError from e



@timer
def logged_run(command: list[str], logger: logging.Logger) -> int:
    '''
    run os code and record output

    Args:
        command(list[str]): a list combined with code section, segregation respect \
            with space when them are typed in console
        logger(logging.Logger): 
    
    Returns:
        returncode(int): mark whether command run sucessfully
    
    Raises:
        errors.RunFailError:
        errors.FuncError:
        errors.UnexpectedError
    '''
    try:
        import subprocess, threading
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        def log_stream(stream: IO[str], level=logging.DEBUG) -> None:
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
        
        try:
            stdout_thread.start()
            stderr_thread.start()
            
            process.wait()
            
            stdout_thread.join()
            stderr_thread.join()

        except Exception as e:
            raise errors.FuncError('thread running') from e
        

        if process.returncode != 0:
            logger.error(f'os running exit with error on command {command}')
            raise errors.RunFailError
        else:
            logger.info(f'os running exit with success on command {command}')
            
        return process.returncode
    
    except (errors.RunFailError, errors.FuncError) as e:
        raise e
    
    except Exception as e:
        raise errors.UnexpectedError from e



def logged_input(prompt: str, logger: logging.Logger, valid_input: list[str]) -> str:
    """
    print prompt on console, receive and verify user input and log what's happened with logger

    Args:
        prompt(str):
        logger(logging.Logger):
        valid_input(list[str]): a list of strings that can pass verification
    
    Returns:
        user_input(str): strings in valid_input which user give
    
    Raises:
        errors.InputError
        errors.FuncError
        errors.UnexpectedError
    """
    try:
        try:
            assert valid_input
        
        except AssertionError as e:
            raise errors.InputError from e
        

        while True:
            try:
                print(prompt, end='', flush=True)
                
                user_input = input()
                
                logger.info(f"INPUT PROMPT: {prompt.rstrip()}")
                logger.info(f"USER RESPONSE: {user_input}")

                if user_input in valid_input:
                    return user_input
                else:
                    raise errors.InputError
            
            except errors.InputError as e:
                logged_print('Bad input, please retry', logger)
            
            except Exception as e:
                raise errors.FuncError('interact')
    

    except (errors.InputError, errors.FuncError) as e:
        raise e

    except Exception as e:
        raise errors.UnexpectedError from e



def logged_print(prompt: str, logger: logging.Logger) -> None:
    """
    print prompt on console and log it with logger

    Args:
        prompt(str):
        logger(logging.Logger):

    Returns:
        (None)
    
    Raises:
        error.UnexpectedError
    """
    try:
        logger.info(prompt)
        print(prompt)

    except Exception as e:
        raise errors.UnexpectedError from e