# Copyright Michael Mattie (2022) - codermattie@runbox.com

from cfconfig.cloud_formation import CloudFormationTemplate, CloudFormationExecute, AWScontext
from cfconfig.cloud_formation import USER_TYPE, GROUP_TYPE, ROLE_TYPE, ACCESS_TYPE, PARAMETER_ACCCOUNT

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

    def __init__(self, context, assume_resources=None, assume_whitelist=None):
        super().__init__(
            context,
            System=SYSTEM_NAME,
            Component=COMPONENT_NAME
        )
        
        self.environment = context.environment

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

def template(context):
    return CFBuildSystem(context)

def deploy(context, stack_name, template):

    return CloudFormationExecute(
        context,
        stack_name,
        template,
        System=SYSTEM_NAME,
        Component=COMPONENT_NAME
    )