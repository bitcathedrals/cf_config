# Copyright Michael Mattie (2022) - michael.mattie.employers@gmail.com

from json_decorator.json import json_fn
from cf_config.cloud_formation import CloudFormation

from json import dumps

class CFBuilderRole:
    policy_name = 'CloudFormationBuild'
    policy_version = "2012-10-17"
    resource = None

    def __init__(self, resource="*"):
        self.resource = resource

    @json_fn()
    def template(self):
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "buildIAM": { **self.IAM() }
            }
        }

    def IAM(self):
        return {
            "Type": "AWS::IAM::Policy",
            "Properties": {
                "PolicyName": self.policy_name,
                "PolicyDocument": self.policy()
            }
        }

    def policy(self):
        return {
            "Version": self.policy_version,
            "Statement": [
                self.allow_all()
            ]
        }

    def allow_all(self):
        return {
            "Effect": "Allow",
            "Action": ["cloudformation:*"],
            "Resource": self.resource
        }

if __name__ == '__main__':

    cloud = CloudFormation('build-system')

    output = cloud.create_stack(CFBuilderRole().template())

    print("got this: " + dumps(output))

