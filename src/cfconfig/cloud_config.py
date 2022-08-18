# copyright (2022) Michael Mattie - codermattie@runbox.com

from os import path
from datetime import datetime

from json import dumps, loads

from functools import cached_property

from .cloud_formation import CloudFormationExecute

from pprint import pprint

class CloudConfig:
    environment = None
    profile = None
    config_dir = None

    ignore = []

    stacks_list = {}
        
    table = {}

    reserved = [ "env", "stacks", "ignore" ]

    def insert_into_table(self, key, value, source="static"):
        print(f"[%s]: adding key -> %s" % (source, key))
        self.table[source + "_" + key] = value

    def read_stack_outputs(self):
        for stack_name in self.stacks_list:
            stack = CloudFormationExecute(stack_name,
                                          None,
                                          self.environment,
                                          profile=self.profile)

            for key,value in stack.output.items():
                if key not in self.ignore:
                    self.insert_into_table(key, value, source=stack_name)
                else:
                    print(f"[%s]: ignoring key -> %s" % (stack_name,key))

    def read_config(self):
        config_path = self.config_dir + "/cloud-config.json"

        if not path.isfile(config_path):
            raise Exception(f"cloud-config.json not found at %s" % config_path)

        f = open(config_path, "r")

        config_contents = loads(f.read())

        self.environment = config_contents["env"]

        self.stacks_list = config_contents["stacks"]

        if "ignore" in config_contents:
            self.ignore = config_contents["ignore"]

        for key, value in config_contents.items():
            if key not in self.reserved:
                self.insert_into_table(key, value)
    
    def __init__(self, dir, profile):
        self.profile = profile
        self.config_dir = dir

        self.read_config()
        self.read_stack_outputs()


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

