class InputValueError(Exception):
    def __init__(self, function_name):
        self.function_name = function_name
    def __str__(self):
        return f'Bad input for function {self.function_name}'

class FunctionRunningError(Exception):
    def __init__(self, function_name, error_info):
        self.function_name = function_name
        self.error_info = error_info
    def __str__(self):
        return f'Error {self.error_info} occur when running function {self.function_name}'

class ConfigFileError(Exception):
    def __init__(self, file_name, problem_item):
        self.file_name = file_name
        self.problem_item = problem_item
    def __str__(self):
        return f'Config File {self.file_name} need recheck, item {self.problem_item} is detected to have problem'
    
class CommandRunningError(FunctionRunningError):
    def __init__(self, function_name, command):
        super().__init__(function_name, 'os command runing error')
        self.command = command
    def __str__(self):
        return f'Error occur when running command {self.command} in logged_run function'