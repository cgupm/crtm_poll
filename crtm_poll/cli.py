"""Console script for crtm_poll."""
import sys
import click
import click_log
from crtm_poll.crtm_api import stop_times
from crtm_poll.daemon import daemon
import random
import pathlib
from filelock import FileLock
import logging

logging.basicConfig(stream=sys.stderr)
logger = logging.getLogger()
click_log.basic_config(logger)

# Dictionary with configuration parameters for fetching the content
fetch_conf = {}


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click_log.simple_verbosity_option(logger)
@click.option('--fetch-log', nargs=1, help='Write fetch logs in CSV format.',
              type=click.Path(exists=False,
                              file_okay=True,
                              dir_okay=False,
                              writable=True), default=None)
@click.option('--timeout', nargs=1, help='Fetching timeout in seconds per '
              'session.', type=click.INT, default=40, show_default=True)
@click.option('--max-connections', nargs=1, help='Maximum simultaneous '
              'connections per fetching process.', type=click.INT,
              default=100, show_default=True)
def main(fetch_log, timeout, max_connections):
    """Console script for crtm_poll.
    """
    fetch_conf['log'] = fetch_log
    fetch_conf['timeout'] = timeout
    fetch_conf['max_connections'] = max_connections


@click.command(name='gst',
               help="Get the stop times for all the bus lines in a given stop."
               )
@click.argument('cod_stop')
def get_stop_times(cod_stop):
    """Wrapper around stop_times.get_stop_times
    """
    logger.debug("cod_stop: "+str(cod_stop))
    json, time = stop_times.get_stop_times(cod_stop, fetch_conf)
    print(json)
    logger.info("Request time: " + str(time) + " s")


main.add_command(get_stop_times)


def load_stops_file(stops_file):
    """Read file with stop codes (one by line) to array.

    Arguments:
        stops_file (str): Path to the file containing the stop codes
            (one by line)

    Returns:
        list: List of stop codes
    """
    logger.debug("stops_file: "+str(stops_file))
    cod_stops = []
    with open(stops_file) as f:
        for line in f:
            cod_stops.append(line.rstrip('\n'))
    logger.debug("cod_stops: "+str(cod_stops))
    random.shuffle(cod_stops)
    return cod_stops


@click.command(name='gstb',
               help="Get the stop times for all the bus lines for every given"
               " stop code in a file, one per line. In JSON format."
               )
@click.argument('stops_file', type=click.Path(exists=True,
                                              file_okay=True,
                                              dir_okay=False,
                                              readable=True))
def get_stop_times_batch(stops_file):
    """Wrapper around stop_times.get_stop_times_batch

    Keyword arguments:
    stops_file -- path to the file containing the stop codes (one by line)
    """
    cod_stops = load_stops_file(stops_file)
    json_array, total_time = stop_times.get_stop_times_batch(cod_stops,
                                                             fetch_conf)
    print('\n'.join(json_array))
    logger.info("Requests total time: " + str(total_time) + " s")


main.add_command(get_stop_times_batch)


@click.command(name='gstbp',
               help="Get the parsed stop times for all the bus lines for every"
               " given stop code in a file, one per line. In CSV format."
               )
@click.argument('stops_file', type=click.Path(exists=True,
                                              file_okay=True,
                                              dir_okay=False,
                                              readable=True))
def get_stop_times_batch_parsed(stops_file):
    """Wrapper around stop_times.get_stop_times_batch_parsed

    Keyword arguments:
    stops_file -- path to the file containing the stop codes (one by line)
    """
    cod_stops = load_stops_file(stops_file)
    csv_array, total_time = stop_times.get_stop_times_batch_parsed(cod_stops,
                                                                   fetch_conf)
    print('\n'.join(csv_array))
    logger.info("Requests total time: " + str(total_time) + " s")


main.add_command(get_stop_times_batch_parsed)


@click.command(name='daemon',
               help="Run a periodic daemon that executes one of the possible "
               "functions and stores the output a given file."
               )
@click.option('--interval', nargs=1, help='Period of the daemon in seconds. '
              '(Default: 60)', default=60, type=click.INT)
@click.option('--processes', nargs=1, help='Maximum spawned fetching '
              'processes. (Default: 5)', default=5, type=click.INT)
@click.option('--max-conn-test', nargs=4, help='Test different maximum '
              '(simultaneous) connections in random order. Pass 4 integer '
              'values: start, stop, step and repetition (e.g. 5 101 5 1).',
              type=click.INT)
@click.argument('function', nargs=1,
                type=click.Choice(
                            ['gstb', 'gstbp'],
                            case_sensitive=False
                                 ))
@click.argument('stops_file', type=click.Path(exists=True,
                                              file_okay=True,
                                              dir_okay=False,
                                              readable=True))
@click.argument('output_file', type=click.Path(exists=False,
                                               file_okay=True,
                                               dir_okay=False,
                                               writable=True))
def start_daemon(function, stops_file, output_file, interval, processes,
                 max_conn_test):
    """Wrapper around daemon.start_daemon

    Keyword arguments:
    function -- acronym of the function to execute among the supported ones
    stops_file -- path to the file containing the stop codes (one by line)
    output_file -- path to the file were to append the results
    interval -- period of the daemon in seconds
    processes -- maximum spawned fetching processes
    max_conn_test -- Test different maximum (simultaneous) connections in
                     random order. Pass 4 integer values: start, stop, step
                     and repetition (e.g. 5 101 5 1).
    """
    logger.info("Starting daemon...")
    if (function == 'gstb'):
        func = stop_times.get_stop_times_batch
    elif (function == 'gstbp'):
        path_exists = pathlib.Path(output_file).exists()
        print(path_exists)
        if (not path_exists):
            with FileLock(output_file + '.lock', timeout=60):
                with open(output_file, 'a+') as f:
                    f.write(stop_times.gstbp_csv_columns)
        func = stop_times.get_stop_times_batch_parsed

    cod_stops = load_stops_file(stops_file)
    daemon.start_daemon(func, (cod_stops), output_file, interval, processes,
                        max_conn_test, fetch_conf)


main.add_command(start_daemon)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
