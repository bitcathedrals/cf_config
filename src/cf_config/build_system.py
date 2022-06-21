from config import CloudConfig, module_dir

import sys
from pprint import pprint

class BuildSystem(CloudConfig):
    def __init__(self):
        super().__init__(name='build_system', directory=module_dir())



if __name__ == '__main__':
    build_config = BuildSystem()

    env = sys.argv[1]
    key = sys.argv[2]

    lookup = build_config["%s:%s" % (env, key)]

    if lookup:
        print("[Found]")
        pprint(lookup)