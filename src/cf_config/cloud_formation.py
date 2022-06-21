# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com
from abc import ABC, abstractmethod
import os
import boto3
from collections import OrderedDict
import re
from pprint import pprint
from time import sleep

from json_decorator.json import json_fn

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


class CloudFormationExecute:
    environment = None
    stack_name = None

    roleARN = None

    access_key = None 
    secret_key = None

    client = None

    def __init__(self, stack_name, ARN=None):
            self.stack_name = stack_name
            self.roleARN = ARN

            self.access_key = os.environ['CF_ACCESS_KEY']
            self.secret_key = os.environ['CF_SECRET_KEY']


    def cf_client(self):
        if self.client is None:
            self.client = boto3.client('cloudformation',
                                       aws_access_key_id=self.access_key,
                                       aws_secret_access_key=self.secret_key)
        return self.client

    def stack_output(self):
        execute = self.cf_client().describe_stacks(StackName=self.stack_name)

        if "Outputs" not in execute["Stacks"][0]:
            return {}

        data = {}

        for kv in execute["Outputs"]:
            data[kv['OutputKey']] = kv["OutputValue"]

        return data

    def status(self):
        execute = self.cf_client().describe_stacks(StackName=self.stack_name)

        print(pprint(execute))

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









