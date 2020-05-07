# crtm_poll

Python scripts for polling different data from CRTM.

* [docker](https://hub.docker.com/r/cgupm/crtm_poll)

## Features

* CRTM intercity buses:
   * Get the stop times for all the bus lines in a given stop.
   * Get the stop times for all the bus lines for every given stop code in a
      file.
   * Get the parsed stop times for all the bus lines for every given stop code
      in a file in CSV format.
   * Run a periodic daemon that executes one of the possible functions and
      stores the output a given file.
   * Perform a test to find out the optimal number of parallel connections
      when polling the server.

## Installation

```bash
pip3 install git+git://github.com/cgupm/crtm_poll
```

## Docker

You can use the *Dockerfile* to build a minimal image containing this tool and
its dependencies or directly use the [public
image](https://hub.docker.com/r/cgupm/crtm_poll):

```bash
docker run -it --rm -v "${PWD}:/home/user" -v /etc/localtime:/etc/localtime:ro --user $(id -u):$(id -g) cgupm/crtm_poll
```

## Usage

Once installed, this package provides a command line script that can be run as
follows:

```bash
crtm_poll --help
crtm_poll gst 8_17491
```

## Testing

Tests can be run executing `pytest` or `make test` within the project's
directory.

## License

GPLv3

## Author Information

cgupm: c.garcia-maurino (at) alumnos.upm.es
