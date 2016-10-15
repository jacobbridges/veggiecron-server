"""
src/utils/config_parser.py

The application configurations are in a YAML file in the top directory of the project. This file
is for utilities associated with that config file.
"""

import os
import yaml

from yaml.scanner import ScannerError


class ConfigParser(object):
    """Parse the contents of the application config.yaml."""

    def __init__(self):

        # Parse the server config file
        server_config = None
        try:
            server_config = yaml.load(open('config.yaml', 'r'))
        except FileNotFoundError:
            file_path = os.path.abspath('config.yaml')
            print('Error: Could not locate config.yaml at {}'.format(file_path))
            exit()
        except ScannerError as e:
            print(e)
            print('Error: Improper YAML in config.yaml.')
            exit()
        finally:
            if type(server_config) is not dict:
                print('Error: Unknown error while parsing config.yaml.')
                exit()

        # Add the parsed data as attributes to this object
        self.app_env = server_config['app']['env']
        self.app_name = server_config['app']['name']
        self.app_key = server_config['app']['key']
        self.host = server_config['key']
        self.port = server_config['port']
        self.db_file = server_config['db_file']
