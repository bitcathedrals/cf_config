# CFconfig

CFconfig is a paradigm of combining deployment with configuration.

Other than the static configuration values, and secrets, the configuration
keys are often derived from CloudFormation deploys which produce the ARN's
and other key outputs.

CFconfig facilates not only making outputs available between stacks but
also makes configuration values available to the application code
in a easy to use interface of dynamically loading modules with constants
set to the configuration values.

