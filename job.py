from functools import wraps
from typing import Callable

def coroutine(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        gen = f(*args, **kwargs)
        gen.send(None)
        return gen

    return wrap

class Job:
    def __init__(
        self, 
        target: Callable, 
        args: tuple | None = None, 
        kwargs: dict | None = None,
    ) -> None:
        self.__args = args or ()
        self.__kwargs = kwargs or {}
        self.__coroutine = target(*self.__args, **self.__kwargs)

    def run(self) -> None:
        self.__coroutine.send(None)