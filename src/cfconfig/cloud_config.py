# copyright (2022) Michael Mattie - codermattie@runbox.com

from os import path
from datetime import datetime
from re import sub
from json import loads

from .cloud_formation import CloudFormationExecute

class CloudConfig:
    reserved = [ "stacks", "ignore" ]

    ignore = []

    table = {}

    configuration = []

    def insert_into_table(self, key, value, source='static'):
        print(f"[%s]: adding key -> %s" % (source, key))
        self.table[key] = value

    def read_stacks(self, stacks_list, environment, profile):

        for stack_name in stacks_list:
            stack = CloudFormationExecute(stack_name,
                                          None,
                                          environment,
                                          profile=profile)

            for key,value in stack.output.items():
                if key not in self.ignore:
                    self.insert_into_table(key, value, source=stack_name)
                else:
                    print(f"[%s]: ignoring key -> %s" % (stack_name, key))

    def read_config(self, config, environment):
        if not path.isfile(config):
            raise Exception(f"CFconfig error: %s config not found" % self.config_file)

        f = open(config, "r")

        config = loads(f.read())

        if environment not in config:
            raise Exception(f"CFconfig error: %s environment not found in -> %s" % (environment, 
                                                                                    config))

        aws_env = config[environment]

        if "stacks" in aws_env:
            stacks_list = aws_env["stacks"]
        else:
            raise Exception(f"CFconfig WARNING: %s environment does not have \"stacks\" list -> %s" % 
                                                                                    (environment, 
                                                                                     config))
        if "ignore" in aws_env:
            self.ignore = aws_env["ignore"]
        
        for key, value in aws_env.items():
            if key not in self.reserved:
                self.insert_into_table(key, value)

        return stacks_list

    def generate_configuration(self):
        for config, value in self.table.items():
            cleaned = config.upper().replace('-','_')

            constant_name = sub('/^' + self.environment + '/','', cleaned)
 
            if isinstance(value, str):
                constant_value = "\"%s\"" % value
            else:
                constant_value = str(value)
            
            self.configuration.append("%s=%s" % (constant_name, constant_value))

        self.configuration.sort()

    def __init__(self, profile, config, environment):
        self.environment = environment

        stacks = self.read_config(config, environment)
        self.read_stacks(stacks, environment, profile)

        self.generate_configuration()
        
    def __getitem__(self, config):
        if config in self.table:
            return self.table[config]
        
        raise Exception("CFconfig unknown config: %s" % config)

    def print_configuration(self):
        print("\n".join(self.configuration))
        print("\n") 

    def write_configuration(self):
        f = open(self.output, "w")
 
        f.write(f'# Config Generated @ %s\n\n' % datetime.now().isoformat())

        f.write("\n".join(self.configuration))
        f.write("\n")

        f.close()

