# Copyright Michael Mattie (2022) - michael.mattie.employers@gmail.com

from cfconfig.cloud_formation import CloudFormationTemplate, CloudFormationExecute, cloud_command, BUILD_PROFILE
from cfconfig.cloud_formation import USER_TYPE, GROUP_TYPE, ROLE_TYPE, ACCESS_TYPE, PARAMETER_ACCCOUNT

import sys
import argparse
from pprint import pprint

from functools import cached_property

STACK_NAME = 'config-build-system'

SYSTEM_NAME = 'config-build'
COMPONENT_NAME = 'config-deploy'

USER_NAME = 'ConfigDeployUser'
GROUP_NAME = 'ConfigDeployGroup'

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
    IAM_CREDENTIALS = "CFconfigBuilderCredentails"

    IAM_ACCESS_ID = "CFconfigBuildAccessId"
    IAM_ACCESS_KEY = "CFconfigBuildAccessKey"

    environment = None

    def __init__(self, environment, assume_resources=None, assume_whitelist=None):
        super().__init__(
            environment,
            System=SYSTEM_NAME,
            Component=COMPONENT_NAME
        )
        
        self.environment = environment

        if assume_resources:
            self.assume_resources = assume_resources

        if assume_whitelist:
            self.assume_whitelist = assume_whitelist


    @cached_property
    def iam_role(self):
        return self.environment + self.IAM_ROLE

    @cached_property
    def group_name(self):
        return self.environment + GROUP_NAME

    @cached_property
    def user_name(self):
        return self.environment + USER_NAME

    def build_role_assume_policy(self):
        return {
            "Version": self.INLINE_POLICY_VERSION,
            "Statement": self.build_statement(
                self.ROLE_ACTION,
                Principal={
                    "AWS": self.build_reference(PARAMETER_ACCCOUNT)
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
                self.build_attribute(self.iam_role),
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
                    RoleName=self.iam_role,
                    AssumeRolePolicyDocument=self.build_role_assume_policy()
                ),
                                                    
                self.build_resource(
                    self.IAM_GROUP,
                    GROUP_TYPE,
                    self.build_group_policy(),
                    GroupName=self.group_name,
                    depends=self.environment + self.IAM_ROLE
                ),

                self.build_resource(
                    self.IAM_USER,
                    USER_TYPE,
                    UserName=self.user_name,
                    Groups=[ self.group_name ],
                    depends=self.environment + self.IAM_GROUP
                ),

                self.build_resource(
                    self.IAM_CREDENTIALS,
                    ACCESS_TYPE,
                    UserName=self.build_reference(self.environment + self.IAM_USER),
                    depends=self.environment + self.IAM_USER
                )
            ],

            [],

            [
                self.build_output(
                    "BuildSystemGroupName",
                    self.group_name
                ),

                self.build_output(
                    "BuildSystemGroupARN",
                    self.build_attribute(self.IAM_GROUP, env=self.environment)
                ),

                self.build_output(
                    "BuildSystemUserName",
                    self.user_name
                ),

                self.build_output(
                    "BuildSystemUserARN",
                    self.build_attribute(self.IAM_USER, env=self.environment)
                ),

                self.build_output(
                    "BuildSystemRoleName", 
                    self.iam_role
                ),
                    
                self.build_output(
                    "BuildSystemRoleARN",
                    self.build_attribute(self.IAM_ROLE, env=self.environment)
                ),

                self.build_output(
                    "BuildUserAccessId",
                    self.build_reference(self.IAM_CREDENTIALS, env=self.environment)
                ),

                self.build_output(
                    "BuildUserAccessSecret",
                    self.build_attribute(self.IAM_CREDENTIALS, env=self.environment, attribute="SecretAccessKey")
                )    
            ],
        )

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Construct a build role and user for using CloudFormation as a non-privelaged user.')

    parser.add_argument(  
                          'command',
                            type=str,
                            default='status',
                            help="specify the command to run"
                        )

    parser.add_argument(
                          'environment',
                          type=str,
                          default='dev',
                          help="specify the environment to target"
    )
    
    parser.add_argument(
                            '-profile',
                            type=str,
                            dest='profile',
                            nargs="?",
                            default=BUILD_PROFILE,
                            help='the AWS CLI profile to use for building'
                        )

    parser.add_argument(
                            '-count', 
                            type=int,
                            dest='count',
                            nargs="?",
                            default=10,
                            help='count of entries to return from stack inspection operations'
                        )

    parser.add_argument(
                            '-path',
                            type=str,
                            dest='config_file',
                            nargs="?",
                            help='the file path to merge the new output values to'
                        )

    parser.add_argument(
                            '-debug', 
                            dest='debug', 
                            default=False, 
                            action='store_true'
                        )

    args = parser.parse_args()

    cloud = CloudFormationExecute(
        STACK_NAME,
        CFBuildSystem(args.environment),
        args.environment,
        profile=args.profile,
        System=SYSTEM_NAME,
        Component=COMPONENT_NAME
    )

    if cloud_command(args, cloud):
        cloud.wait_for_complete(quiet=False)
