# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com
from abc import ABC, abstractmethod
import os
import boto3

from json_decorator.json import json_fn

from json import dumps

class CloudFormationTemplate(ABC):
    built = None

    def build_output(self, output, key, value):
        return {
           output: {
                    "Export": {
                        "Name": key 
                    },
                    "Value": value
                }
        }

    def build_resource(self, name, config):
        return {
            name: { **config }
        }

    def build_template(self, resources, outputs):
        self.built = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {},
            "Outputs": {}
        }

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


class CloudFormationExecute:
    environment = None
    stack_name = None

    roleARN = None

    access_key = None 
    secret_key = None 

    def __init__(self, stack_name, ARN=None):
            self.stack_name = stack_name
            self.roleARN = ARN

            self.access_key = os.environ['CF_ACCESS_KEY']
            self.secret_key = os.environ['CF_SECRET_KEY']


    def create_stack(self, template, project=None):
        output = None

        client = boto3.client('cloudformation',
                              aws_access_key_id=self.access_key,
                              aws_secret_access_key=self.secret_key)

        args = {
            'StackName': self.stack_name,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'TemplateBody': template.json()
        }

        if self.roleARN:
            args['RoleARN'] = self.roleARN

        if project:
            args['Tags'] = [{'Key': 'project', 'Value': project}]

        output = client.create_stack(**args)

        if isinstance(output, dict):
            return output

        return None





