# copyright (2022) Michael Mattie - michael.mattie.employers@gmail.com

import os
import inspect
from json import dumps, loads

_config_files = ['all.json', 'dev.json', 'test.json', 'prod.json']

def module_dir():
    filename = inspect.stack()[0][1]
    return os.path.dirname(filename)

class CloudConfig:
    chained = None

    environments = {
        'all': {},
        'dev': {},
        'test': {},
        'prod': {}
    }

    def __init__(self, name, *chained, directory=None):
        self.name = name

        if chained:
            self.chained = sorted(changed, key=lambda x: x.name)
        else:
            self.chained = []

        if directory:
            self.update_from_directory(directory)

    def _lookup(self, super_key):
        env, key = super_key.split(':')

        if env in self.environments:
            if key in self.environments[env]:
                return self.environments[env][key]

        if key in self.environments['all']:
            return self.environments['all'][key]

        return None

    def __getitem__(self, super_key):
        found = self._lookup(super_key)
        
        if found:
            return found

        for config in self.chained:
            found = config[super_key]

            if found:
                return found

        return None

    def __setitem__(self, super_key, value):
        env, key = super_key.split(":")

        if env not in self.environments:
            raise Exception("environment: %s not found in config table" % env)

        self.environments[env][key] = value

        return value


    def update_all(self, new_config):
        self.environments['all'].update(new_config)

    def update_dev(self, new_config):
        self.environments['dev'].update(new_config)

    def update_test(self, new_config):
        self.environments['test'].update(new_config)

    def update_prod(self, new_config):
        self.environments['prod'].update(new_config)

    def update_from_directory(self, directory):
        for path in _config_files:
            file = os.path.join(directory, path)

            if os.path.exists(file):
                config_handle = open(file, 'r')

                json_raw = config_handle.read()

                config_dict = loads(json_raw)

                if isinstance(config_dict, dict) and config_dict:
                    env = path.split('.')[0]

                    self.environments[env].update(config_dict)
                

