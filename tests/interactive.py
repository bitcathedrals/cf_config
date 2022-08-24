import sys
import os

from pprint import pprint

import cfconfig.cloud_formation
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

from cfconfig.cloud_config import CloudConfig

intel_dir="/Users/michaelmattie/coding/cf_config/tests"
m1_dir="/Users/mattie/coding/cf_config/tests"

config = CloudConfig(intel_dir,"root")
config = CloudConfig(m1_dir,"root")

config.write_module(intel_dir,"test_module")
config.write_module(m1_dir,"test_module")
