# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com
from abc import ABC, abstractmethod
import os.path

import boto3
from botocore.config import Config

from collections import OrderedDict
from functools import cached_property
import re
from pprint import pprint
from time import sleep
from json import loads, dumps

from json_decorator.json import json_fn

DEFAULT_REGION = 'us-west-2'
DEBUG_STREAM = 'boto3.resources'

BUILD_PROFILE = 'build-system'

TEMPLATE_VERSION = "2010-09-09"
POLICY_VERSION = "2012-10-17"

USER_TYPE = "AWS::IAM::User"
GROUP_TYPE = "AWS::IAM::Group"
ROLE_TYPE = "AWS::IAM::Role"

PARAMETER_ACCCOUNT = "AWS::AccountId"

BUILT_STATUS = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']

def build_tags(**kwargs):
    tags = []

    for name, value in kwargs.items():
        tags.append(
            {
                'Key': name,
                'Value': value          
            }
        )

    return tags

class CloudFormationTemplate(ABC):
    built = None
    tags = []

    def __init__(self, **tags):
        self.tags = build_tags(**tags)

    def build_output(self, key, value):
        return {
            key: {
                "Value": value
            }
        }

    def build_attribute(self, name, attribute="Arn"):
        return {
            "Fn::GetAtt" : [name, attribute]
         }

    def build_reference(self, name):
        return {
            "Ref" : name 
        }

    def build_resource(self, name, resource_type, *inline_policies, path="/", **properties):

        res = {
            name: OrderedDict([
                ("Type", resource_type),
                ("Path", path),
            ])
        }

        if properties:
            res[name]["Properties"] = { **properties }

        if inline_policies:
            res[name]["Policies"] = inline_policies

        if self.tags:
            res[name]["Tags"] = self.tags

        return res

    def build_statement(self, actions, resources=[], permission="Allow", deny_other=False, **extra_args):
        statement = OrderedDict([
            ("Effect", permission),
        ])

        if actions:
            if isinstance(actions, list):
                statement["Action"] = actions
            else:
                statement["Action"] = [ actions ]

        if resources:
            if isinstance(resources, list):
                statement["Resources"] = resources
            else:
                statement["Resources"] = [ resources ]

        if extra_args:
            statement.update(extra_args)

        constructed = [ statement ]

        if deny_other:
            others = {
                "Effect": "Deny",
                "Action": statement["Action"],
                "NotResource": statement["Resources"]
            }

            constructed.append(others)

        return constructed

    def build_policy(self, name, *statements):
        collect = []

        for decl in statements:
            collect = collect + decl

        return {
            name: {
                "PolicyName" : name,
                "PolicyDocument" : {
                    "Version": POLICY_VERSION,
                    "Statement" : collect
                }
            }
        }
        

    def build_template(self, resources, policies, outputs):
        self.built = OrderedDict([("AWSTemplateFormatVersion", TEMPLATE_VERSION),
                                  ("Resources", OrderedDict()),
                                  ("Policies", []),
                                  ("Outputs", OrderedDict())
                                  ])

        for res in resources:
            self.built["Resources"].update(res)

        if policies:
            for pol in policies:
                self.built["Policies"].append(pol)

        if outputs:
            for out in outputs:
                self.built["Outputs"].update(out)


        return self.built

    @abstractmethod
    def construct():
        pass

    @cached_property
    def template(self):
        self.construct()

        return self.built

    @json_fn()
    def json(self):
        return self.template

    def print(self):
        pprint(self.template)

        return self.template


def cf_default_config(region=DEFAULT_REGION, retries=6, mode='standard'):
    return Config(
        region_name = region,
        signature_version = 'v4',
        retries = {
            'max_attempts': retries,
            'mode': mode
        }
    )

class CloudFormationExecute:
    environment = None

    stack_name = None
    config = None 

    profile = None
    role = None

    tags = []

    template = None

    def __init__(
        self, 
        stack_name, 
        template, 
        role=None, 
        profile=BUILD_PROFILE, 
        config=None, 
        debug=False,
        **kwargs
    ):

        self.stack_name = stack_name
        self.template = template

        if config:
            self.config = config
        else:
            self.config = cf_default_config()

        session_default = {
            'profile_name': profile
        }

        self.role = role
            
        boto3.setup_default_session(**session_default)

        if debug:
            boto3.set_stream_logger(DEBUG_STREAM, logging.DEBUG)

        tags = build_tags(**kwargs)

    @cached_property
    def session_credentials(self):
        sts_client = boto3.client('sts')

        assume = sts_client.assume_role(
            RoleArn=self.role,
            RoleSessionName="CFBuildSession"
        )

        return assume['Credentials']

    @cached_property
    def cloud_formation(self):                                                 
            creds = self.session_credentials

            return boto3.Resources(
                'cloudformation',
                creds['AccessKeyId'],
                creds['SecretAccessKey'],
                creds['SessionToken']
            )

    def invalidate_cloud_formation(self):
        del self.session_credentials
        del self.cloud_formation

        return

    def output(self):
        execute = self.cloud_formation.describe_stacks(StackName=self.stack_name)

        if "Outputs" not in execute["Stacks"][0]:
            return {}

        data = {}

        for kv in execute["Stacks"][0]["Outputs"]:
            data[kv['OutputKey']] = kv["OutputValue"]

        return data

    def events(self, event_filter=None, count=10):
        execute = self.cloud_formation.describe_stack_events(StackName=self.stack_name)

        events = []

        if count:
            events = execute['StackEvents'][0:min(len(execute['StackEvents']), int(count))]
        else:
            events = execute['StackEvents']

        if event_filter:
            events = [event for event in events if event_filter(event)]

        return events


    @json_fn()
    def output_json(self):
        return self.output()

    def print_output(self):
        pprint(self.output())
        return

    @json_fn()
    def template_json(self):
        return self.template.template

    def print_template(self):
        pprint(self.template.template)
        return

    def status(self):
        execute = self.cloud_formation.describe_stacks(StackName=self.stack_name)

        if "StackStatus" in execute["Stacks"][0]:
            return execute["Stacks"][0]["StackStatus"]

        return None

    def pending(self):
        status = self.status()

        if re.search(r'.*IN_PROGRESS$', status) is None:
            return None

        return status

    def create_stack(self,**kwargs):

        args = {
            'StackName': self.stack_name,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': self.template_json(),
        }

        if self.tags:
            args['Tags'] = tags

        if kwargs:
            args.update(kwargs)

        return self.cloud_formation.create_stack(kwargs)

    def update_stack(self, **kwargs):

        args = {
            'StackName': self.stack_name,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': self.template_json()
        }

        if self.tags:
            args['Tags'] = Tags

        if kwargs:
            args.update(kwargs)

        return self.cloud_formation.update_stack(args)

    def list_stacks(self, *list_filter):
        stacks = self.cloud_formation.list_stacks(StackStatusFilter=list_filter)
    
        result = []

        for stack in stacks['StackSummaries']:

            info = {
                'id': stack['StackId'],
                'name': stack['StackName'],
                'status': stack['StackStatus']
            }

            if 'StackStatusReason' in stack:
                info['reason'] = stack['StackStatusReason']

            result.append(info)

        return result
                
    def find_stack(*list_filter):
        for stack in self.list_stacks(list_filter):
            if stack['name'] == self.stack_name:
                return stack

        return None

    def build_stack(self):
        if find_stack(*BUILT_STATUS):
            self.update_stack()
            return False

        self.create_stack()
        return True

    def validate(self):
        validate = self.cloud_formation.validate_template(TemplateBody=self.template_json())
        
        if isinstance(validate, dict):
            return validate
        
        return None

    def wait_for_complete(self, quiet=True):
        while True:
            pending = self.pending()

            if pending is None:
                break

            if not quiet:
                print(self.stack_name + " status: " + pending)

            sleep(1)

    def reasons_filter(events):
        def extract_status(event):
            status =  event['ResourceStatus']
        
            if 'ResourceStatusReason' in event:
                status = "%s = %s" % (status, event['ResourceStatusReason'])

            return status

        return [extract_status(ev) for ev in events]

def cloud_command(args, executor):
    command = args[1]

    if command == "json-template":
        print(executor.template_json() + "\n")
        return False

    if command == "print-template":
        executor.print_template()
        return False

    if command == "build":
        executor.build_stack()
        return True

    if command == "status":
        pprint(executor.status())
        return False
        
    if command == "json-output":
        print(executor.output_json())
        return False

    if command == "print-output":
        executor.print_output()
        return False

    if command == "events":
        if len(args) > 2:
            pprint(executor.events(count=args[2]))
            return False

        pprint(executor.events())
        return False

    if command == "validate":
        if executor.validate():
            print("Passed Validation")
            return False

        print("Failed Validation")
        return False

    if command == "list":
        pprint(executor.list_stacks())
        return False
        
    if command == "reasons":
        if len(args) > 2:
            pprint(reasons_filter(executor.events(count=args[2])))
            return False

        pprint(reasons_filter(executor.events()))
        return False

    if command == "write":
        file_path = args[2]

        table = {}

        if os.path.isfile(file_path):
            table = loads(open(file_path, 'r').read())

        table.update(executor.output())

        file = open(file_path, 'w')

        file.write(dumps(table, indent=4, sort_keys=True) + "\n")
        file.close()

        return False

    print("unknown command: %s" % command)
    return False










