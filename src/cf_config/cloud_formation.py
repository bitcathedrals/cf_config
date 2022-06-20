# copyright (2022) Micheal Mattie  - michael.mattie.employers@gmail.com

import os
import boto3

from json import dumps

class CloudFormation:
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
            'TemplateBody': template
        }

        if self.roleARN:
            args['RoleARN'] = self.roleARN

        if project:
            args['tags'] = [{'project': project}]

        output = client.create_stack(**args)

        if isinstance(output, dict):
            return output

        return None





