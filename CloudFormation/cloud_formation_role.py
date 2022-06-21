# Copyright Michael Mattie (2022) - michael.mattie.employers@gmail.com

from json_decorator.json import json_fn
from cf_config.cloud_formation import CloudFormationTemplate, CloudFormationExecute

from pprint import pprint

class CFBuilderRole(CloudFormationTemplate):
    policy_name = 'CloudFormationBuild'
    
    assume_policy_version = "2012-10-17"
    cf_policy_version = "2012-10-17"

    assume_whitelist = "*"
    
    cf_whitelist = ["cloudformation:*"]
    cf_resources = "*"

    IAM_role = "CFconfigBuildRole"

    def __init__(self, *args, cf_resources=None, assume_whitelist=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if cf_resources:
            self.cf_resources = cf_resources

        if assume_whitelist:
            self.assume_whitelist = assume_whitelist

    def build_role_resource(self):
        return {
            "AssumeRolePolicyDocument": self.build_role_policy(),
            "Policies": [ self.build_cf_policy() ],
            "RoleName": self.IAM_role
        }
        

    def build_role_policy(self):
        return {
            "Version": self.assume_policy_version,
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": [ "sts:AssumeRole" ]
                }
            ]
        }

    def build_cf_policy(self):
        return {
            "PolicyName": "cf_build_policy",
            "PolicyDocument": {
                "Version": self.cf_policy_version,
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": self.cf_whitelist,
                        "Resource": self.cf_resources
                    }
                ]
            }
        }

    def construct(self):
        self.build_template([
                                self.build_resource(self.IAM_role,
                                                    "AWS::IAM::Role",
                                                    self.build_role_resource())
                            ],
                            [
                                self.build_output("BuildSystemRoleName", 
                                                  self.IAM_role),
                                self.build_output("BuildSystemRoleARN",
                                                  {"Fn::GetAtt" : [self.IAM_role, "Arn"] })
                            ])

if __name__ == '__main__':

    cloud = CloudFormationExecute('build-system')

    # create = cloud.create_stack(CFBuilderRole(), project='learn')

    # cloud.wait_for_complete(quiet=False)

    #print("stack output is: " + pprint(cloud.stack_output()))

    #CFBuilderRole().pp()

    print(CFBuilderRole().json())