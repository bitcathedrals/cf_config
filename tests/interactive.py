import sys
import importlib
import os

from pprint import pprint

def update_search_path():
    cur = os.getcwd()
    
    for x in ('src', 'CloudFormation'):
        sys.path.append(cur + "/" + x)

def reload_modules():
    importlib.reload(cf_config.cloud_formation)
    importlib.reload(deploy)


update_search_path()

import cf_config.cloud_formation
import deploy

#
# manual
#

# reload_modules()

template = deploy.CFBuildSystem("dev")

# template.print()

# print(template.json)

file = open("test.json", "w")

file.write(template.json)

file.close()
# pprint(sys.path)

