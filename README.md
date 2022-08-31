# CFconfig

cfconfig is a paradigm combining deployment with configuration.

The problem that cfconfig solves is that deployment and configuration
are two sides of the same coin. Critical configuration parameters such as ARN's of resources are not known until Cloud Formation stacks are created or updated.

This has often lead to poor practices such as hand tweaking poorly coded config classes after deploying. 

This is extremely error prone and causes hard to detect errors where the application seems to work initially but has subtle bugs that arise later due to using old versions of resources.

## The cfconfig approach

cfconfig changes this by providing an API for Object Oriented construction of templates and stacks. Using this API it is easy to build secure stacks, with the help of policy and resource construction using python instead of JSON or YAML to define resources.

Configuration is baked into Python code by generating python modules with the outputs of the stacks written as module constants.

Eventually there will be support for accessing parameter store values through the module constant
Concept as well.

## Examples

I learn best by example so here are some examples.

Here is a template to create users with privileges for CloudFormation so you don't have to use and share root credentials: [cloud_user.py](src/cfconfig/CloudFormation/cloud_user.py)

## Setting up the environment

First you have to setup the development environment using my tool pythonsh:

```bash
./py.sh virtual-install
switch_dev
./py.sh update-all 
./py.sh paths
```

## Deploying

```bash
makedeploy <ROLE> <PROFILE> <ENVIRONMENT> <DIR> <MODULE> <COMMAND>
```

- ROLE = ARN of a role to access CloudFormation
- PROFILE - AWS credentials profile that also includes region
- ENVIRONMENT - the environment, such as "env", "test", or "production"
- DIR - "directory containing the template module
- MODULE - name of the template module
- COMMAND - one of the make deploy commands listed below

### A CFconfig module

A CFconfig module is a module that uses cloud_formation to create templates and deploy
Them.

It is expected to have two functions:
- template(AWSContext): = a function that returns a template object using the AWSContext parameter and the CloudFormationTemplate Abstract Base Class.
- deploy(context, stack_name, template): = a function to create the deploy object. 

An example below, first an example of template:

```python
def template(context):
    return CFBuildSystem(context)
```

And second an example of deploy:

```python
def deploy(context, stack_name, template):
    return CloudFormationExecute(
        context,
        stack_name,
        template,
        System=SYSTEM_NAME,
        Component=COMPONENT_NAME
    )
```

CFconfig can't simply do the deploy function for
you since you need to pass your tags to the constructor so the stack is tagged correctly.

Here System and Component are tags.

### makedeploy commands

Makedeploy has several flags for working with modules and deploying them:

```bash
-> template-json: print the json of the template
-> template-python: print the python of the template
-> build: deploy the template
-> status: print the status of the deploy
-> output-json: print the outputs of the stack in JSON
-> output-python: print the output of the stack in Python
-> events: print the event history of the stack up to --limit=N entries
```

The commands are pretty self explanatory. The most important ones are build which does a CloudFormation create or update depending on wether the stack exists or not, status which prints the last event, events to see the events, and output-json to get the stack outputs in JSON format.

### makeconfig

makeconfig is a little simpler in that it uses
A config to specify some of the values. You need a JSON file like below 

To generate a configuration module you create a [cloud-config.json](tests/cloud-config.json)
file listing the environment, the stacks to include, and the parameters to
generate.

```json
{
    "dev": {
        "stacks": ["test-stack"],
        "ignore": ["BuildUserAccessSecret", "BuildUserAccessId"],

        "AppName": "test-stack"
    }
}
```

The first key is the environment. Within an environment is a list of stacks to generate the config from, a ignore list to mask sensitive keys,
and any static configuration values as key/value pairs. 

Invoking it is pretty simple:

```bash
makeconfig <ROLE> <PROFILE> <ENVIRONMENT> <CONFIG.json>

--ouptut=FILE (optional)
```

By default it prints the config but if you want to specify an output file you can with --output=<FILE>.

If you build cloud_user.py with this you will have a user and credentials that is restricted to accessing CloudFormation.

Output of running tests/test-config.sh will look something like this after you edit it to have the
correct ARN for the role:

```bash
[static]: adding key -> AppName
[test-stack]: ignoring key -> BuildUserAccessSecret
[test-stack]: ignoring key -> BuildUserAccessId
[test-stack]: adding key -> BuildSystemGroupName
[test-stack]: adding key -> BuildSystemGroupARN
[test-stack]: adding key -> BuildSystemRoleName
[test-stack]: adding key -> BuildSystemUserName
[test-stack]: adding key -> BuildSystemUserARN
[test-stack]: adding key -> BuildSystemRoleARN
APPNAME="test-stack"
BUILDSYSTEMGROUPARN="arn:aws:iam::324189914596:group/devConfigDeployGroup"
BUILDSYSTEMGROUPNAME="devConfigDeployGroup"
BUILDSYSTEMROLEARN="arn:aws:iam::324189914596:role/devCFconfigBuildRole"
BUILDSYSTEMROLENAME="devCFconfigBuildRole"
BUILDSYSTEMUSERARN="arn:aws:iam::324189914596:user/devConfigDeployUser"
BUILDSYSTEMUSERNAME="devConfigDeployUser"
```

### Practices

Each template should have a configuration per environment such as
- example-dev.py
- example-test.py
- example-prod.py

When run for each environment I suggest symlinking a single name to the config: example-config.py -> example-dev.py

## Template Construction with CloudFormationTemplate

CloudFormation templates are constructed with the CloudFormationTemplate abstract base class

```python
from cfconfig import CloudFormationTemplate
```

```python
def build_output(self, key, value):
```

build an CF output, key and value

```python
def build_attribute(self, name, env=None, attribute="Arn"):
```

build a CF attribute out of a logical resource name. attribute defaults to Arn

```python
def build_reference(self, name, env=None):
```

Build a CF reference out of a logical resource name

```python
def build_resource(self, name, resource_type, *policies, path=None, depends=None, **properties):
```

Build a resource with (name), resource type:

```python
USER_TYPE = "AWS::IAM::User"
GROUP_TYPE = "AWS::IAM::Group"
ROLE_TYPE = "AWS::IAM::Role"
ACCESS_TYPE = "AWS::IAM::AccessKey"
```

You can optionally specify a path, other resources it depends on. Policies is a list of inline policies constructed with the policy methods.

Properties are specified as keyword arguments to the method.

```python
def build_statement(self, actions, resources=[], permission="Allow", deny_other=False, **extra_args):
```

Statements are policy statements constructed with actions which is a single action, or multiple actions in an array. Resources is an array of the resources affected by this policy. Permission defaults to allow. deny_other automatically creates a inverse DENY policy for security best practices.

Extra args can be given such as principal.

```python
def build_policy(self, name, *statements):
```

Build policy takes an array of policy statements and constructs a resource inline policy.

```python
def build_template(self, resources, policies, outputs):
```

Build template takes resources, policies, and outputs
And constructs a CloudFormation template.

```python
@abstractmethod
def construct():
    pass
```

The abstract method you have to override is "construct". It takes no arguments and here you should build the template.

```python
def construct(self):
    self.build_template(
        [
            self.build_resource(
                self.IAM_ROLE,
                ROLE_TYPE,
                self.build_role_policy(),
                RoleName=self.iam_role,
                AssumeRolePolicyDocument=self.build_role_assume_policy()
            )
        ],

        [],

        [
            self.build_output(
                "BuildSystemGroupName",
                self.group_name
            )
		]
	)
```

## CloudFormationTemplate hooks

```python
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
```

Along with the template you need to define two hooks
- template = return the constructed template
- deploy = return an execute object

The CloudFormationExecute object is created with the AWScontext named tuple which takes (role, profile, and environment), the stack name, and the template, and any remaining keyword arguments are tags for the stack.




