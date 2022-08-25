# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com
from abc import ABC, abstractmethod
import os.path
import logging

import boto3
from botocore.config import Config

from collections import OrderedDict, namedtuple
from functools import cached_property

from pprint import pprint
from time import sleep
from json import dumps

DEFAULT_REGION = 'us-west-2'
DEBUG_STREAM = 'boto3.resources'

BUILD_PROFILE = 'build-system'

TEMPLATE_VERSION = "2010-09-09"
POLICY_VERSION = "2012-10-17"

USER_TYPE = "AWS::IAM::User"
GROUP_TYPE = "AWS::IAM::Group"
ROLE_TYPE = "AWS::IAM::Role"
ACCESS_TYPE = "AWS::IAM::AccessKey"

PARAMETER_ACCCOUNT = "AWS::AccountId"

BUILT_COMPLETE_STATUS = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']

BUILT_FAILED_STATUS = ['CREATE_FAILED', 'UPDATE_FAILED']

BUILT_ROLLBACK_STATUS = ['ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']

BUILT_IN_PROGRESS_STATUS = ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS']

CF_RESOURCE = 'cloudformation'

AWScontext = namedtuple('AWScontext', ['role', 'profile', 'environment'])

def build_tags(given_tags):
    tags = []

    for name, value in given_tags.items():
        tags.append(
            {
                'Key': name,
                'Value': value          
            }
        )

    return tags

class CloudFormationTemplate(ABC):
    built = None
    
    env = None
    tags = []

    def __init__(self, context, **tags):
        self.env = context.environment
        self.tags = build_tags(tags)

    def build_output(self, key, value):
        return (
            key,
            {
                "Value": value
            }
        )

    def build_attribute(self, name, env=None, attribute="Arn"):
        if env:
            name = self.env + name
        
        return {
            "Fn::GetAtt" : [name, attribute]
         }

    def build_reference(self, name, env=None):
        identifier = name

        if env:
            identifier = env + name
        
        return {
            "Ref" : identifier
        }

    def build_resource(self, name, resource_type, *policies, path=None, depends=None, **properties):
        name = self.env + name
        
        res = (
            name,
            OrderedDict([
                ("Type", resource_type)
            ])
        )

        if path:
            res[1]["Path"] = path

        if properties:
            res[1]["Properties"] = { **properties }

        if policies:
            if "Properties" not in res[1]:
                res[1]["Properties"] = OrderedDict()

            res[1]["Properties"]["Policies"] = policies

        if self.tags:
            if "Properties" not in res[1]:
                res[1]["Properties"] = OrderedDict()

            if res[1]["Type"] not in [ GROUP_TYPE, ACCESS_TYPE ]:
                res[1]["Properties"]["Tags"] = self.tags

        if depends:
            res[1]["DependsOn"] = depends

        return res

    def build_statement(self, actions, resources=[], permission="Allow", deny_other=False, **extra_args):
        statement = OrderedDict([
            ("Effect", permission)
        ])

        if actions:
            if isinstance(actions, list):
                statement["Action"] = actions
            else:
                statement["Action"] = [ actions ]

        if resources:
            if isinstance(resources, list):
                statement["Resource"] = resources
            else:
                statement["Resource"] = [ resources ]

        if extra_args:
            statement.update(extra_args)

        constructed = [ statement ]

        if deny_other:
            others = {
                "Effect": "Deny",
                "Action": statement["Action"],
                "NotResource": statement["Resource"]
            }

            constructed.append(others)

        return constructed

    def build_policy(self, name, *statements):
        name = self.env + name

        collect = []

        for decl in statements:
            collect = collect + decl

        return {
            "PolicyName" : name,
            "PolicyDocument" : {
                "Version": POLICY_VERSION,
                "Statement" : collect
            }
        }
        

    def build_template(self, resources, policies, outputs):
        self.built = OrderedDict([
                                  ("AWSTemplateFormatVersion", TEMPLATE_VERSION),
                                  ("Resources", OrderedDict())
                                ])

        for res in resources:
            self.built["Resources"] = OrderedDict(resources)

        if policies:
            self.built["Policies"] = policies

        if outputs:
            self.built["Outputs"] = OrderedDict(outputs)

        return self.built

    @abstractmethod
    def construct():
        pass

    @cached_property
    def template(self):
        self.construct()

        return self.built

    @property
    def json(self):
        return dumps(
            self.template,
            indent=2
        ) + "\n"

    @property
    def python(self):
        return self.template
    
    def print(self):
        pprint(self.template)

        return self.template


def cf_default_config(region, retries=6, mode='standard'):
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

    context = None
    stack_name = None

    config = None 

    tags = []

    template = None

    def __init__(
        self,
        context,
        stack_name, 
        template,
        region=DEFAULT_REGION,
        config=None, 
        debug=False,
        **kwargs
    ):
        self.context = context
        self.stack_name = stack_name
        self.template = template

        if config:
            self.config = config
        else:
            self.config = cf_default_config(region)

        session_default = {
            'profile_name': context.profile
        }
            
        boto3.setup_default_session(**session_default)

        if debug:
            boto3.set_stream_logger(DEBUG_STREAM, logging.DEBUG)

        kwargs['region'] = region
        kwargs['environment'] = context.environment

        self.tags = build_tags(kwargs)

    @property
    def role_credentials(self):
        sts_client = boto3.client('sts')

        assume = sts_client.assume_role(
            RoleArn=self.context.role,
            RoleSessionName="CFBuildSession"
        )

        return assume['Credentials']

    @property
    def role_resource(self):
            creds = self.role_credentials

            return boto3.resource(
                CF_RESOURCE,
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
            )

    @property
    def root_resource(self):
        return boto3.resource(
            CF_RESOURCE
        )

    @cached_property
    def resource(self):
        if self.context.profile == 'root':
            return self.root_resource                                      

        return self.role_resource

    def reset_resource(self):
        del self.resource
        return None

    @cached_property
    def existing(self):
        return self.resource.Stack(self.stack_name)

    @property
    def output(self):
        data = {}

        for out in self.existing.outputs:
            data[out['OutputKey']] = out['OutputValue']

        return data

    def events(self, *attributes, filter=None, limit=None):
        if limit:
            events = self.existing.events.limit(limit)
        else:
            events = self.existing.events.all()

        if not events:
            return []

        summaries = []

        for ev in events:
            if filter and ev.resource_status not in filter:
                continue

            event_data = OrderedDict()

            for requested in attributes:
                event_data[requested] = getattr(ev, requested, None)

            summaries.append(event_data)

        if 'timestamp' in attributes:
            return sorted(summaries, key=lambda x: x['timestamp'], reverse=True)

        return summaries

    @property
    def status(self):
        return self.events(
                'logical_resource_id',
                'resource_status',
                'resource_status_reason',
                'stack_id',
                'timestamp',
                count=1
            )

    @property
    def failure(self):
        return self.events(
                'logical_resource_id',
                'resource_status',
                'resource_status_reason',
                'stack_id',
                'timestamp',
                filter=BUILT_FAILED_STATUS,
            )

    @property
    def success(self):
        return self.events(
                'logical_resource_id',
                'resource_status',
                'resource_status_reason',
                'stack_id',
                'timestamp',
                filter=BUILT_COMPLETE_STATUS
            )

    @property
    def finished(self):
        return self.events(
                'logical_resource_id',
                'resource_status',
                'resource_status_reason',
                'stack_id',
                'timestamp',
                filter=BUILT_COMPLETE_STATUS + BUILT_FAILED_STATUS + BUILT_ROLLBACK_STATUS,
                count=1
            )

    @property
    def json(self):
        return dumps(
            self.output,
            indent=2
        )

    def print(self):
        pprint(self.output)
        return

    @property
    def template_object(self):
        return self.template

    def pending(self):
        return not self.finished

    def find(
            self,  
            name=None, 
            status_filter=BUILT_COMPLETE_STATUS + BUILT_ROLLBACK_STATUS + BUILT_FAILED_STATUS, 
            limit=None
        ):
        
        if not name:
            name = self.stack_name

        found = []

        if limit:
            stack_list = self.resources = self.resource.stacks.limit(limit)
        else:
            stack_list = self.resources = self.resource.stacks.all()

        for stack in stack_list:
            if stack.stack_name == name and stack.stack_status in status_filter:
                found.append(stack)

        return found

    def create(self, rollback=True, **kwargs):

        create = {
            'StackName': self.stack_name,
            'DisableRollback': not rollback,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': self.template.json
        }

        if self.tags:
            create['Tags'] = self.tags

        if kwargs:
            create.update(kwargs)

        return self.resource.create_stack(**create)

    def update(self, rollback=True, **kwargs):
        update = {
            'StackName': self.stack_name,
            'DisableRollback': not rollback,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': self.template.json
        }

        if self.tags:
            update['Tags'] = self.tags

        if kwargs:
            update.update(kwargs)

        return self.existing.update(**update)

    def build(self, rollback=True):
        search = self.find()

        if search:
            return self.update(rollback=rollback)
        else:
            return self.create(rollback=rollback)

        return None

    def wait(self, quiet=True):
        while True:
            pending = self.pending()

            if pending is None:
                break

            if not quiet:
                print(self.stack_name + " status: " + getattr(pending[0],'resource_status_reason','unknown'))

            sleep(1)

def cloud_command(executor, command, limit=None):

    if command == "template-json":
        print(executor.template_object.json + "\n")
        return False

    if command == "template-python":
        executor.template_object.print()
        return False

    if command == "build":
        executor.build()
        return True

    if command == "status":
        pprint(executor.status)
        return False
        
    if command == "output-json":
        print(executor.json)
        return False

    if command  == "output-python":
        executor.print()
        return False

    if command == "events":
        pprint(executor.events(limit))
        return False

    print("unknown command: %s" % command)
    return False
