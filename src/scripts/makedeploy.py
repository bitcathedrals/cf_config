import argparse
from importlib import import_module
import os

from cfconfig.cloud_formation import cloud_command

def importer(dir, module):
    os.path.append(dir)
    globals()[module] = import_module(module)

    return globals()[module]

def deployer(dir, module, profile, environment, command):
    if command in ['template-json', 'template-python', 'build']:
        template = True
    else:
        template = False

    return importer(dir, module).deploy(profile, environment, template=template)

def exec():
    parser = argparse.ArgumentParser("Generate deploy AWS CloudFormation Stacks constructed with CFconfig.")

    parser.add_argument("profile", help="aws credentials profile (required)")
    parser.add_argument("environment", help="AWS environment (required)")
    parser.add_argument("dir", help="directory containing the CFconfig module")
    parser.add_argument("module", help="module containing a build(profile,environment) hook")

    COMMAND = """
        [deploy commands]:

        -> template-json: print the json of the template
        -> template-python: print the python of the template
        -> build: deploy the template
        -> status: print the status of the deploy
        -> output-json: print the outputs of the stack in JSON
        -> output-python: print the output of the stack in Python
        -> events: print the event history of the stack up to --limit=N entries
    """

    parser.add_argument("command", help=COMMAND)

    parser.add_argument("--limit", help="limit output to N entries", type=int, required=False, default=10)
   
    args = parser.parse_args()

    cloud_command(deployer(args.dir, args.module, args.profile, args.environment),
                                 args.command,
                                 args.limit)

if __name__ == "__main__":
    exec()
