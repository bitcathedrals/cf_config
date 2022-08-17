from os import path
import sys

def tests_path():
    return path.dirname(__file__)

def cf_config_path():
    return path.realpath(tests_path() + "/../")

def add_cf_config_search_path():
    for modules_dir in ('src', 'CloudFormation'):
        sys.path.append(cf_config_path() + "/" + modules_dir)

add_cf_config_search_path()

from cf_config.cloud_config import CloudConfig

cf_config = CloudConfig(tests_path(), "root")

cf_config.write_module(tests_path(), "config")


