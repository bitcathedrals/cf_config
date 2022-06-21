# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com
from abc import ABC, abstractmethod
import os

import boto3
from botocore.config import Config

from collections import OrderedDict
import re
from pprint import pprint
from time import sleep

from json_decorator.json import json_fn

DEFAULT_REGION = 'us-west-2'

class CloudFormationTemplate(ABC):
    built = None

    def build_output(self, key, value):
        return {
            key: {
                "Value": value
            }
        }

    def build_resource(self, name, resource_type, properties):

        return {
            name: { "Type": resource_type,
                    "Properties": { **properties } }
        }

    def build_template(self, resources, outputs):
        self.built = OrderedDict([("AWSTemplateFormatVersion", "2010-09-09"),
                                  ("Resources", {}),
                                  ("Outputs", {})])

        for res in resources:
            self.built["Resources"].update(res)

        for out in outputs:
            self.built["Outputs"].update(out)

        return self.built

    @abstractmethod
    def construct():
        pass

    @json_fn()
    def json(self):
        self.construct()

        return self.built

    def pp(self):
        self.construct()

        pprint(self.built)


def cloud_config(region=DEFAULT_REGION, retries=6, mode='standard'):
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

    roleARN = None

    access_key = None 
    secret_key = None

    client = None

    def __init__(self, stack_name, ARN=None, config=cloud_config()):
            self.stack_name = stack_name
            self.roleARN = ARN

            self.config = config

            self.access_key = os.environ['CF_ACCESS_KEY']
            self.secret_key = os.environ['CF_SECRET_KEY']


    def cf_client(self):
        if self.client is None:
            self.client = boto3.client('cloudformation',
                                       config=self.config,
                                       aws_access_key_id=self.access_key,
                                       aws_secret_access_key=self.secret_key)
        return self.client

    def output(self):
        execute = self.cf_client().describe_stacks(StackName=self.stack_name)

        if "Outputs" not in execute["Stacks"][0]:
            return {}

        data = {}

        for kv in execute["Stacks"][0]["Outputs"]:
            data[kv['OutputKey']] = kv["OutputValue"]

        return data

    @json_fn()
    def output_json(self):
        return self.output()

    def status(self):
        execute = self.cf_client().describe_stacks(StackName=self.stack_name)

        if "StackStatus" in execute["Stacks"][0]:
            return execute["Stacks"][0]["StackStatus"]

        return None

    def pending(self):
        status = self.status()

        if re.search(r'.*IN_PROGRESS$', status) is None:
            return None

        return status

    def create_stack(self, template, project=None):

        args = {
            'StackName': self.stack_name,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': template.json()
        }

        if self.roleARN:
            args['RoleARN'] = self.roleARN

        if project:
            args['Tags'] = [{'Key': 'project', 'Value': project}]

        return self.cf_client().create_stack(**args)

    def wait_for_complete(self, quiet=True):
        while True:
            pending = self.pending()

            if pending is None:
                break

            if not quiet:
                print(self.stack_name + " status: " + pending)

            sleep(1)


def cloud_command(args, template, executor, create_wrapper):
    command = args[1]

    if command == "print":
        template.pp()
        return

    if command == "json":
        print(template.json())
        return

    if command == "create":
        create_wrapper()
        return

    if command == "status":
        pprint(executor.status())
        return
        
    if command == "output":
        pprint(executor.output())
        return

    if command == "write":
        file_path = args[2]

        file = open(file_path, 'w')

        file.write(executor.output_json() + "\n")
        file.close()

        return


    print("unkown command: %s" % command)











