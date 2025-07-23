from inspect import stack, FrameInfo



class Error(Exception):
    """define custom exception type attaching frame infomation"""
    frameinfo: list[FrameInfo]
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.frameinfo = stack()
    def __str__(self) -> str:
        return f'{self.frameinfo} with infomation: ' + super().__str__() if super().__str__() != "" \
            else f'{self.frameinfo}'



class FuncError(Error):
    """intermediate error type for function error"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class RunFailError(FuncError):
    """toleriable error when running os code, could be jumped through and continue program"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class OvertimeError(FuncError):
    """single procedure process time go over the overtime value"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class NumberError(Error):
    """intermediate error type for value error"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()
    


class InputError(NumberError):
    """input value error"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class OutputError(NumberError):
    """output value error"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()
    
    

class MathError(NumberError):
    """math error"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class OverlimitError(NumberError):
    """values that go over the given limits"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class CriticalError(Error):
    """happened in key part which means program need to be shutdown"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()



class UnexpectedError(Error):
    """dealing all other exception"""
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    def __str__(self) -> str:
        return super().__str__()