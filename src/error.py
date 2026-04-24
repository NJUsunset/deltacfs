"""Custom exception hierarchy for the deltacfs pipeline.

All exceptions accept a function_name (the name of the function that raised
the error) so that error messages can identify the source location without
requiring a full traceback.
"""


class InputValueError(Exception):
    """Raised when user-provided input fails validation."""

    def __init__(self, function_name):
        self.function_name = function_name

    def __str__(self):
        return f'Bad input for function {self.function_name}'


class FunctionRunningError(Exception):
    """Raised when a pipeline function encounters an unrecoverable error."""

    def __init__(self, function_name):
        self.function_name = function_name

    def __str__(self):
        return f'Error occur when running function {self.function_name}'


class ConfigFileError(Exception):
    """Raised when a config file contains invalid or missing values."""

    def __init__(self, file_name, problem_item):
        self.file_name = file_name
        self.problem_item = problem_item

    def __str__(self):
        return (
            f'Config File {self.file_name} need recheck, '
            f'item {self.problem_item} is detected to have problem'
        )


class CommandRunningError(FunctionRunningError):
    """Raised when a subprocess invoked via logged_run exits with non-zero."""

    def __init__(self, function_name, command):
        super().__init__(function_name)
        self.command = command

    def __str__(self):
        return (
            f'Error occur when running command {self.command} '
            f'in logged_run function'
        )
