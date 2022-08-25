import argparse
from importlib import import_module
import sys
import textwrap

from cfconfig.cloud_formation import cloud_command, AWScontext
from cfconfig.cloud_config import CloudConfig

from functools import cached_property

class cached:
    context = None

    def __init__(self, dir, module, context, config, command):
        self.dir = dir
        self.module_name = module
        self.context = context
        self.config = config
        self.command = command

    @cached_property
    def module(self):
        sys.path.append(self.dir)
        globals()[self.module_name] = import_module(self.module_name)

        return globals()[self.module_name]

    @cached_property
    def template(self):
        if self.command in ['template-json', 'template-python', 'build']:
            return self.module.template()
        else:
            return None

    @cached_property
    def stacks(self):
        return CloudConfig(self.context, self.config, config_only=True).stacks

    def deploy(self, stack):
        return self.module.deploy(self.context,
                                  stack,
                                  self.template)         

resources = None

def exec():
    DESCRIPTION = """
        Generate deploy AWS CloudFormation Stacks constructed with CFconfig.
        
        [deploy commands]:

        -> template-json: print the json of the template
        -> template-python: print the python of the template
        -> build: deploy the template
        -> status: print the status of the deploy
        -> output-json: print the outputs of the stack in JSON
        -> output-python: print the output of the stack in Python
        -> events: print the event history of the stack up to --limit=N entries
    """

    parser = argparse.ArgumentParser(
        prog='makedeploy',
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(DESCRIPTION),
    )

    parser.add_argument("role", help="aws restricted user role ARN (required)")
    parser.add_argument("profile", help="aws credentials profile (required)")
    parser.add_argument("environment", help="AWS environment (required)")
    parser.add_argument("dir", help="directory containing the CFconfig module")
    parser.add_argument("module", help="module containing a deploy(role, profile, environment, stack, template=True|False) hook")
    parser.add_argument("config", help="a cloud-config.json file")

    parser.add_argument("command", help="execute [command]")

    parser.add_argument("--limit", help="limit output to N entries", 
                        type=int, 
                        required=False, 
                        default=None)
   
    args = parser.parse_args()

    print(f"makedeploy: [role] -> %s\n[profile] -> %s\n[environment] -> %s\n[module] -> (%s,%s)\n[config] -> %s\n[command] -> %s" 
          % (args.role, args.profile, args.environment, args.dir, args.module, args.config, args.command))

    context = AWScontext(role=args.role, profile=args.profile, environment=args.environment)

    resources = cached(args.dir, 
                       args.module, 
                       context,
                       args.config,
                       args.command)
    
    print("executing on stacks: " + ",".join(resources.stacks))

    for stack in resources.stacks:
        print("deploying stack -> " + stack)

        cloud_command(resources.deploy(stack),        
                      args.command,
                      limit=args.limit)

if __name__ == "__main__":
    exec()
