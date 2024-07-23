
from time import time
from loguru import logger


def time_function(func):
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        logger.info(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func