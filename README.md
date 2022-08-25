# CFconfig

cfconfig is a paradigm of combining deployment with configuration.

The problem that cf-config solves is that deployment and configuration
are two sides of the same coin. Critical configuration parameters such
as ARN's of resouces are not known until stacks are created or updated.

This has often lead to poor practices such as hand tweaking poorly coded
config classes. This is extremely error prone and causes hard to detect
errors where the application seems to work initialy but has suble bugs
the arise later due to using old versions of resources.

## The cfconfig approach

cfconfig changes this by providing an API for Object Oriented construction
of templates and stacks. Using this API it is easy to build secure stacks.

Configuration is baked into the application by generating python configuration
modules with the outputs of the stacks written as module constants.

This makes configuration systematic and easy. also Parameter Store is supported
through the constant interface dynamically retrieving and caching secrets.

## Examples

I learn best by example so here are some examples.

Here is a template to create users with privelages for cloudformation
without having access to root credentials: [deploy.py](CloudFormation/cloud_user.py)

First you have to setup the development environment

```bash
./package.sh virtual-insall
./package.sh all 
./package.sh paths

pyenv activate config_dev
```

To generate a configuration module you create a [cloud-config.json](tests/cloud-config.json)
file listing the environment, the stacks to include, and the parameters to
generate.

An example of a cloud-config.json file is:

```json
{
    "env": "dev",
    "stacks": ["test-stack"],
    "ignore": ["BuildUserAccessSecret", "BuildUserAccessId"],
    "AppName": "test"
}
```

Initially to create the unprivelaged user you will need root credentials. You would invoke
it something like this:

```bash
ROLE=""
PROFILE=root
ENVIRONMENT=dev

CONFIG=tests/cloud-config.json
exec ./package.sh python -m makedeploy $ROLE $PROFILE $ENVIRONMENT CloudFormation cloud_user $CONFIG build
```

at that point you can invoke the CloudFormation operations as a unprivelaged user in the dev ennvironment
by using the newly created role and credentials:

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

by adding adding a --output=<module.py> to the invocation of makeconfig it will write a python module
with all the keys as constants.

The practice is to have a module for each environment like: config-dev.py, config-test.py, config-prod.py
and symlink config.py -> config-dev.py for each environment.

This is the basic usage. the makedeploy script has a number of commands:

template-json

print the generated template in JSON format
    
template-python

print the generated template as a python data structure

build

create or update a stack using the template.

status

return the status or last event of the stack

output-json

print the output from the stack as JSON

output-python

print the output from the stack as python.

events

print all the events from the stack


## Template Construction

TODO





