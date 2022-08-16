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


pprint(sys.path)

import cf_config.cloud_formation
import deploy

#
# manual
#

# reload_modules()

def debug_template(write=True):
    template = deploy.CFBuildSystem("dev")

    if write:
        file = open("deploy.json", "w")

        file.write(template.json)

        file.close()

    return template

def test_deploy():
    cloud = deploy.CloudFormationExecute(
        'test-stack',
        debug_template(write=False),
        'dev',
        profile='root'
    )

    return cloud

templ = debug_template()

test_stack = test_deploy()

test_stack.build()

pprint(test_stack.status)

pprint(test_stack.success)

pprint(test_stack.finished)

print(test_stack.json)

print(test_stack.find(name='test-stack'))

from cf_config.cloud_config import CloudConfig

test_dir="/Users/michaelmattie/coding/cf-config/tests"

config = CloudConfig(test_dir,"root")

config.write_module(test_dir,"test_module")
