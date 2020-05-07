import sys
import asyncio
from aiohttp import (
        ClientSession,
        TCPConnector,
        ClientTimeout,
        client_exceptions
)
import datetime
import json
from filelock import FileLock
import pathlib
import logging

logger = logging.getLogger()


def fetch_log(fetch_log=None, *args):
    """Write the passed arguments as CSV to fetch_log if set.

    Arguments:
        fetch_log (str): Path to the fethc log file.
        *args (object): CSV line column values.
    """
    if (fetch_log):
        csv_columns = 'actual_date,cod_stop,resp_time,resp_status,' \
                      'resp_length,timeout,connection_error,' \
                      'max_connections,timeout_time'
        log_csv = ",".join([str(arg) for arg in args])
        logger.debug("CSV fetch log line: " + log_csv)
        with FileLock(fetch_log + '.lock', timeout=10):
            path_exists = pathlib.Path(fetch_log).exists()
            with open(fetch_log, 'a+') as f:
                if (path_exists):
                    f.write('\n')
                else:
                    f.write(csv_columns + '\n')
                f.write(log_csv)


async def fetch(cod_stop, session, fetch_conf):
    """Fetch the stops waiting time for a given stop reusing a session.

    Passes some additional data to the fetch_log function. The  CSV column
    names are:
    'actual_date, cod_stop, resp_time, resp_status, resp_length, timeout,
        connection_error, max_connections, timeout_time'

    Arguments:
        cod_stop (str): The stop code in CRTM's format (e.g. 8_17491).
        session (object): The aiohttp ClientSession.
        fetch_conf (dict): Dictionary with configuration parameters for
            fetching the content.

    Returns:
        str: Response text.
    """
    global counter

    actual_time = None
    resp_time = None
    resp_status = None
    resp_length = None
    timeout = None
    connection_error = None

    url = 'https://www.crtm.es/widgets/api/GetStopsTimes.php'
    params = {
                'codStop': cod_stop,
                'type': 1,
                'orderBy': 2,
                'stopTimesByIti': 3
            }
    actual_time = datetime.datetime.now()
    try:
        async with session.get(url, params=params) as response:
            dt_2 = datetime.datetime.now()
            resp_time = (dt_2 - actual_time).total_seconds()
            resp_status = response.status
            resp_text = await response.text()
            resp_length = len(resp_text)
            timeout = False
            connection_error = False
            logger.info("Response time: " + str(resp_time)
                        + " code: " + str(resp_status)
                        + " length: " + str(resp_length))
            fetch_log(fetch_conf['log'], actual_time, cod_stop,
                      resp_time, resp_status,
                      resp_length, timeout, connection_error,
                      fetch_conf['max_connections'], fetch_conf['timeout'])
            return resp_text
    except asyncio.TimeoutError:
        dt_2 = datetime.datetime.now()
        resp_time = (dt_2 - actual_time).total_seconds()
        timeout = True
        connection_error = False
        logger.warning("Timeout")
        fetch_log(fetch_conf['log'], actual_time, cod_stop,
                  resp_time, resp_status,
                  resp_length, timeout, connection_error,
                  fetch_conf['max_connections'], fetch_conf['timeout'])
    except client_exceptions.ClientConnectorError:
        dt_2 = datetime.datetime.now()
        resp_time = (dt_2 - actual_time).total_seconds()
        timeout = False
        connection_error = True
        logger.warning("Connection error")
        fetch_log(fetch_conf['log'], actual_time, cod_stop,
                  resp_time, resp_status,
                  resp_length, timeout, connection_error,
                  fetch_conf['max_connections'], fetch_conf['timeout'])


async def run(cod_stops, fetch_conf):
    """Async function that generates a aiohttp ClientSession and fetches the
    given stops.

    Arguments:
        cod_stops (list): List of stop codes in CRTM's format (e.g. 8_17491).
        fetch_conf (dict): Dictionary with configuration parameters for
            fetching the content.

    Returns:
        list: The responses.
    """
    tasks = []

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    connector = TCPConnector(limit=fetch_conf['max_connections'])
    timeout = ClientTimeout(total=fetch_conf['timeout'])
    async with ClientSession(connector=connector, timeout=timeout) as session:
        for cod_stop in cod_stops:

            task = asyncio.ensure_future(fetch(cod_stop, session, fetch_conf))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
        return responses


def get_stop_times_batch(cod_stops, fetch_conf):
    """Get the stop times for all the bus lines for the given stops.

    Arguments:
        cod_stops (list): List of stop codes in CRTM's format (e.g. 8_17491).
        fetch_conf (dict): Dictionary with configuration parameters for
            fetching the content.

    Returns:
        list: API answers in JSON format.
        float: Total spent time in seconds.
    """

    dt_1 = datetime.datetime.now()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(cod_stops, fetch_conf))
    loop.run_until_complete(future)
    dt_2 = datetime.datetime.now()

    json_array = list(filter(None, future.result()))
    total_time = (dt_2 - dt_1).total_seconds()

    return json_array, total_time


def get_stop_times(cod_stop, fetch_conf):
    """Get the stop times for all the bus lines in a given stop.

    Arguments:
        cod_stop (str): The stop code in CRTM's format (e.g. 8_17491).
        fetch_conf (dict): Dictionary with configuration parameters for
            fetching the content.

    Returns:
        list: API answer in JSON format.
        float: Request time in seconds.
    """
    json_array, total_time = get_stop_times_batch([cod_stop], fetch_conf)

    try:
        json = json_array[0]
        time = total_time

        return json, time
    except IndexError:
        logger.error("Empty answer")
        sys.exit(1)


gstbp_csv_columns = 'actual_date,cod_stop,cod_line,cod_issue,' \
                    'eta,destination_stop'


def get_stop_times_batch_parsed(cod_stops, fetch_conf):
    """Get the stop times for all the bus lines for the given stops parsing
    the JSON answer to CSV.

    The CSV column names are:
    'actual_date,cod_stop,cod_line,cod_issue,eta,destination_stop'

    Arguments:
        cod_stops (list): List of stop codes in CRTM's format (e.g. 8_17491).

    Returns:
        list: Parsed API answers in CSV format.
        float: Total spent time in seconds.
    """

    json_array, total_time = get_stop_times_batch(cod_stops, fetch_conf)

    csv_array = []

    for stop in json_array:
        try:
            split_stop = stop.split('{', 1)
        except AttributeError:
            logger.warning("Empty answer")
            continue

        if (len(split_stop) > 1):
            stop = '{' + split_stop[1]

        try:
            stop_json = json.loads(stop)
        except ValueError:
            logger.warning("json error")
            continue

        try:
            times = stop_json['stopTimes']['times']['Time']
            for time in times:
                selected_fields = [
                        stop_json['stopTimes']['actualDate'],
                        stop_json['stopTimes']['stop']['codStop'],
                        time['line']['codLine'],
                        time['codIssue'],
                        time['time'],
                        time['destinationStop']['codStop'],
                        ]
                row = ','.join(selected_fields)
                csv_array.append(row)
        except (KeyError, TypeError):
            logger.warning("Answer without times")
            continue
        except Exception as e:
            logger.warning("Unknown error: " + str(e))
            continue

    return csv_array, total_time
