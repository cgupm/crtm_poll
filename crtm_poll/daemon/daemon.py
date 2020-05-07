from datetime import datetime
from filelock import FileLock
import itertools
import logging
from multiprocessing import Pool
import pathlib
import random
import sys
import time

logger = logging.getLogger()


def start_daemon(func, func_args, output_file, interval=60, processes=5,
                 max_conn_test=None, fetch_conf={}):
    """Start a daemon that infinitely spawns a given function asynchronously
    every interval and writes the output to a file.

    Arguments:
        func (callable): Function to execute.
        func_args (list): Arguments to pass to the executed function.
        output_file (str): Path to the file were to append the results.
        interval (int): Number of seconds between spawns (the spawning period).
        processes (int): Maximum number of simultaneously running spawned
            processes.
        max_conn_test (list): Test different maximum (simultaneous) connections
            in random order. Pass 4 integer values: start, stop, step and
            repetition (e.g. `list(5, 101, 5, 1)`).
        fetch_conf (dict): Configuration parameters for fetching the content.
    """
    pool = Pool(processes=processes)
    max_conn_values = None
    if (max_conn_test):
        if (len(max_conn_test) == 4):
            max_conn_start = max_conn_test[0]
            max_conn_stop = max_conn_test[1]
            max_conn_step = max_conn_test[2]
            max_conn_repeat = max_conn_test[3]
            max_conn_values = list(range(max_conn_start, max_conn_stop,
                                         max_conn_step))
            random.shuffle(max_conn_values)
            max_conn_values = list(itertools.chain.from_iterable(
                                    itertools.repeat(x, max_conn_repeat)
                                    for x in max_conn_values))
            logger.debug(max_conn_values)
        else:
            sys.exit(1)
    while True:
        if (max_conn_test):
            if (len(max_conn_values) > 0):
                fetch_conf['max_connections'] = max_conn_values.pop(0)
        logger.info("Spawned process at " + str(datetime.now()))
        pool.apply_async(exec_and_write, (func, func_args, output_file,
                                          fetch_conf))
        if (max_conn_test):
            if (len(max_conn_values) < 1):
                while pool._cache:
                    time.sleep(1)
                logger.info("Finished max_conn_test")
                pool.close()
                pool.join()
                sys.exit(0)
        time.sleep(interval)


def exec_and_write(func, func_args, output_file, fetch_conf):
    """Execute a given function with the given args and write the output to the
    given file preventing collisions with a lock.

    Arguments:
        func (callable): Function to execute.
        func_args (list): Arguments to pass to the executed function.
        output_file (str): Path to the file were to append the results.
        fetch_conf (dict): Configuration parameters for fetching the content.
    """
    result, time = func(func_args, fetch_conf)
    logger.info("Total iteration time: " + str(time) + "s")
    with FileLock(output_file + '.lock', timeout=60):
        path_exists = pathlib.Path(output_file).exists()
        with open(output_file, 'a+') as f:
            if (path_exists):
                f.write('\n')
            f.write('\n'.join(result))
    logger.info("Finished process at " + str(datetime.now()))
