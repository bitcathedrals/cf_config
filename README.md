# CFconfig

CFconfig is a paradigm of combining deployment with configuration.

The problem that cf-config solves is that deployment and configuration
are two sides of the same coin. Critical configuration parameters such
as ARN's of resouces are not known until stacks are created or updated.

This has often lead to poor practices such as hand tweaking poorly coded
config classes. This is extremely error prone and causes hard to detect
errors where the application seems to work initialy but has suble bugs
the arise later due to using old versions of resources.

## The cf_config approach

cf_config changes this by providing an API for Object Oriented construction
of templates and stacks. Using this API it is easy to build secure stacks.

Configuration is baked into the application by generating python configuration
modules with the outputs of the stacks written as module constants.

This makes configuration systematic and easy. also Parameter Store is supported
through the constant interface dynamically retrieving and caching secrets.

## Examples

I learn best by example so here are some examples.

Here is a template to create users with privelages for cloudformation
without having access to root credentials: [deploy.py](CloudFormation/deploy.py)

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

You need a configuration in the directory where you want to generate the
config and a python driver to generate the config. An example of a driver
is [test_config.py](tests/test_config.py)

Once you have a driver or have integrated the modulue into your source
tree and build system you can generate config files after deployment
and bake them into an app, or package them with you app.





