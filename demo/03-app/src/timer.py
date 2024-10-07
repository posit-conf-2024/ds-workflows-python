
from time import time
from loguru import logger


def time_function(func):
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        total_time = t2 - t1
        if total_time > 0.01:
            logger.info(f'Function {func.__name__!r} executed in {(total_time):.4f}s')
        return result
    return wrap_func