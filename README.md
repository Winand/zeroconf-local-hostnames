# Local hostnames for Docker on Windows
This script allows to register any *.local hostname using [Zeroconf](https://en.wikipedia.org/wiki/Zero-configuration_networking).
Under the hood it uses [python-zeroconf](https://github.com/python-zeroconf/python-zeroconf) library to announce "fake" services
with given hostnames.

Note: Windows can resolve hostnames even if ".local" top level domain isn't specified.

The main purpose of the script is to connect to Docker containers by hostname from applications on the host OS.
The script can collect hostnames from `docker-compose.yml` files.

Note: You also need to [map ports](https://docs.docker.com/compose/compose-file/compose-file-v3/#ports) to be able to actually connect to your container.

## Config
Configuration is read from `config.yml` file:
* `interface` (string) - specifies which interface to use to announce services (hostnames)
* `docker-compose-paths` (list) - docker-compose files to collect hostnames from.
Docker service names are registered along with names in `container_name` and `hostname` fields if specified.
* `hostnames` (list) - list of hostnames to register. It's ignored if any docker-compose files are specified.
