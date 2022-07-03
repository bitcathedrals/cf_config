# Copyright Michael Mattie (2022) - michael.mattie.employers@gmail.com

from json_decorator.json import json_fn
from cf_config.cloud_formation import CloudFormationTemplate, CloudFormationExecute, cloud_command
from cf_config.cloud_formation import USER_TYPE, GROUP_TYPE, ROLE_TYPE, PARAMETER_ACCCOUNT

import sys

STACK_NAME = 'build-system'
SYSTEM_NAME = 'build-system'
COMPONENT_NAME = 'build-permissions'

USER_NAME = 'DeployUser'
GROUP_NAME = 'DeployGroup'

class CFBuildSystem(CloudFormationTemplate):
    ROLE_ACTION = "sts:AssumeRole"
    INLINE_POLICY_VERSION = "2012-10-17"

    ROLE_POLICY_NAME = 'CFRolePolicy'
    GROUP_POLICY_NAME= 'CFGroupPolicy'
    USER_POLICY_NAME = 'CFUserPolicy'

    assume_whitelist = "*"
    assume_operations = "cloudformation:*"
    assume_resources = "*"

    IAM_ROLE = "CFconfigBuildRole"
    IAM_GROUP = "CFconfigBuildGroup"
    IAM_USER = "CFconfigBuildUser"

    def __init__(self, *args, assume_resources=None, assume_whitelist=None):
        super().__init__(
            System=SYSTEM_NAME,
            Component=COMPONENT_NAME
        )
        
        if assume_resources:
            self.assume_resources = assume_resources

        if assume_whitelist:
            self.assume_whitelist = assume_whitelist

    def build_role_assume_policy(self):
        return {
            "Version": self.INLINE_POLICY_VERSION,
            "Statement": self.build_statement(
                self.ROLE_ACTION,
                Principal={
                    "AWS": { 
                        "Value" : self.build_reference(PARAMETER_ACCCOUNT) 
                    }
                }
            )
        }

    def build_role_policy(self):
        return self.build_policy(
            self.ROLE_POLICY_NAME,
            self.build_statement(
                self.assume_operations,
                self.assume_resources,
            )
        )


    def build_group_policy(self):
        return self.build_policy(
            self.GROUP_POLICY_NAME,
            self.build_statement(
                self.ROLE_ACTION,
                self.build_attribute(self.IAM_ROLE),
                deny_other=True
            )
        )

    def construct(self):
        self.build_template(
            [
                self.build_resource(
                    self.IAM_ROLE,
                    ROLE_TYPE,
                    self.build_role_policy(),
                    RoleName=self.IAM_ROLE,
                    AssumeRolePolicyDocument=self.build_role_assume_policy()
                ),
                                                    

                self.build_resource(
                    self.IAM_GROUP,
                    GROUP_TYPE,
                    self.build_group_policy()
                ),


                self.build_resource(
                    self.IAM_USER,
                    USER_TYPE,
                    [],
                    UserName=USER_NAME,
                    Groups=[ self.IAM_GROUP ]
                )

            ],

            [],

            [
                self.build_output(
                    "BuildSystemGroupName",
                    GROUP_NAME
                ),

                self.build_output(
                    "BuildSystemGroupARN",
                    self.build_attribute(self.IAM_GROUP)
                ),

                self.build_output(
                    "BuildSystemUserName",
                    USER_NAME
                ),

                self.build_output(
                    "BuildSystemUserARN",
                    self.build_attribute(self.IAM_USER)
                ),

                self.build_output(
                    "BuildSystemRoleName", 
                    self.IAM_ROLE
                ),
                    
                self.build_output(
                    "BuildSystemRoleARN",
                    self.build_attribute(self.IAM_ROLE)
                )
            ],
        )

if __name__ == '__main__':

    cloud = CloudFormationExecute(
        STACK_NAME,
        template=CFBuildSystem(),
        System=SYSTEM_NAME,
        Component=COMPONENT_NAME
    )

    if cloud_command(sys.argv, cloud):
        cloud.wait_for_complete(quiet=False)
