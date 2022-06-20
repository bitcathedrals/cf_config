# Copyright Michael Mattie (2022) - michael.mattie.employers@gmail.com

from json_decorator.json import json_fn
from cf_config.cloud_formation import CloudFormationTemplate, CloudFormationExecute

from json import dumps

class CFBuilderRole(CloudFormationTemplate):
    policy_name = 'CloudFormationBuild'
    policy_version = "2012-10-17"
    resource = None
    IAM_role = "CFconfigBuildRole"

    def __init__(self, *args, resource="*", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.resource = resource

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

    def construct(self):
        self.build_template([
                                self.build_resource(self.IAM_role,
                                                    self.IAM())
                            ],
                            [
                                self.build_output(self.IAM_role, 
                                                  "CFconfig:%s" % self.IAM_role,
                                                  self.IAM_role)
                            ])

if __name__ == '__main__':

    cloud = CloudFormationExecute('build-system')

    output = cloud.create_stack(CFBuilderRole(), project='learn')

    print("got this: " + dumps(output))

