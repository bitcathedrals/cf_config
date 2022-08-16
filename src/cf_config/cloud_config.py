# copyright (2022) Michael Mattie - codermattie@runbox.com

from os import path
from datetime import datetime

from json import dumps, loads

from functools import cached_property

from .cloud_formation import CloudFormationExecute

class CloudConfig:
    environment = None
    profile = None
    config_dir = None

    table = {}

    @cached_property
    def stack_list(self):
        f = open(self.config_dir + "/stacks.json", "r")

        stack_file = loads(f.read())    

        self.environment = stack_file["env"]

        return stack_file["stacks"]
        
    def read_stack_outputs(self):
        for stack_name in self.stack_list:
            stack = CloudFormationExecute(stack_name,
                                          None,
                                          self.environment,
                                          profile=self.profile)

            for key,value in stack.output.items():
                self.table[stack_name + "_" + key] = value

    def read_static_config(self):
        static_path = self.config_dir + "/static.json"

        if not path.isfile(static_path):
            return

        f = open(static_path, "r")

        static_contents = loads(f.read())

        for key, value in static_contents.items():
            self.table["static" + "_" + key] = value

    def __init__(self, dir, profile):
        self.profile = profile
        self.config_dir = dir

        self.read_stack_outputs()
        self.read_static_config()

    def __getitem__(self, config):
        if config in self.table:
            return self.table[config]
        
        raise Exception("Unknown config: %s" % config)

    def write_module(self, dir, module):
        f = open(dir + "/" + module + ".py", "w")
 
        f.write(f'# Config Generated @ %s\n\n' % datetime.now().isoformat())

        config_data = []

        for config, value in self.table.items():
            constant_name = config.upper().replace('-','_')

            if isinstance(value, str):
                constant_value = "\"%s\"" % value
            else:
                constant_value = str(value)
            
            config_data.append("%s=%s" % (constant_name, constant_value))

        config_data.sort()

        f.write("\n".join(config_data))
        f.write("\n")

        f.close()

