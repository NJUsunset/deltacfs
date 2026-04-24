"""Logging infrastructure for the deltacfs pipeline.

Provides structured logging with both file and console output, plus utilities
for running subprocesses with streamed log capture and interactive prompts.
"""

from src import constant, error
from enum import Enum
import logging
import subprocess
import threading


class Log_level(Enum):
    """Log verbosity levels for pipeline initialisation."""
    DEBUG = 5
    INFO = 6
    WARNING = 7


def initlogger(level=Log_level.INFO):
    """Initialise the root logger with file and console handlers.

    Args:
        level: Log_level enum value controlling output verbosity.
               DEBUG writes all messages to file, ERROR only to console.

    Returns:
        logging.Logger: The configured 'main' logger.

    Raises:
        error.InputValueError: If level is not a recognised Log_level member.
    """
    if level not in (Log_level.DEBUG, Log_level.INFO, Log_level.WARNING):
        raise error.InputValueError('initlogger')

    from os import makedirs
    makedirs(constant.LOG_PREFIX, exist_ok=True)

    logger = logging.getLogger('main')
    logger.setLevel(logging.DEBUG)

    from datetime import datetime
    file_handler = logging.FileHandler(
        constant.LOG_PREFIX
        + f"Calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def setlogger(name='UnknownModule'):
    """Create a child logger under the 'main' hierarchy.

    Args:
        name: Module name used as the logger suffix (e.g. 'cmp_input').

    Returns:
        logging.Logger: Child logger with dotted name 'main.<name>'.
    """
    logger = logging.getLogger('main.' + name)
    return logger


def logged_run(command, logger):
    """Run an external command and stream its stdout/stderr into the logger.

    Stdout is logged at DEBUG level, stderr at ERROR level.  If the
    subprocess returns a non-zero exit code, CommandRunningError is raised.

    Args:
        command: List of command-line arguments (e.g. ['bash', './script']).
        logger: Logger to receive streamed output.

    Returns:
        int: Exit code of the subprocess (0 on success).

    Raises:
        error.CommandRunningError: If the subprocess exits with non-zero status.
    """
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    def log_stream(stream, level):
        for line in iter(stream.readline, ''):
            cleaned_line = line.rstrip('\n')
            if cleaned_line:
                logger.log(level, cleaned_line)

    stdout_thread = threading.Thread(
        target=log_stream,
        args=(process.stdout, logging.DEBUG),
    )
    stderr_thread = threading.Thread(
        target=log_stream,
        args=(process.stderr, logging.ERROR),
    )

    stdout_thread.start()
    stderr_thread.start()

    process.wait()

    stdout_thread.join()
    stderr_thread.join()

    if process.returncode != 0:
        logger.error(
            f"program exit with error when running command {command} "
            f"with exit code {process.returncode}"
        )
        raise error.CommandRunningError(logged_run, command)
    else:
        logger.info(
            f"program exit with success when running command {command}"
        )

    return process.returncode


def logged_input(prompt, logger):
    """Prompt the user for input and validate the response.

    Acceptable responses are 'y', 'no-override', and 'n'.  The prompt and
    user response are written to the log.

    Args:
        prompt: Text displayed to the user (should end with newline).
        logger: Logger for recording the prompt/response pair.

    Returns:
        str: One of {'y', 'no-override', 'n'}.
    """
    valid_input = ['y', 'no-override', 'n']

    while True:
        try:
            print(prompt, end='', flush=True)

            user_input = input()

            logger.info(f"INPUT PROMPT: {prompt.rstrip()}")
            logger.info(f"USER RESPONSE: {user_input}")

            if user_input in valid_input:
                return user_input
            else:
                raise error.InputValueError(logged_input)

        except error.InputValueError as e:
            logger.warning(e)
            logged_print('Bad input, please retry', logger)


def logged_print(prompt, logger):
    """Log a message and echo it to stdout.

    Args:
        prompt: The message string.
        logger: Logger to write the message to.

    Returns:
        int: Always 0.
    """
    logger.info(prompt)
    print(prompt)
    return 0
