#! /bin/bash

ROLE="arn:aws:iam::324189914596:role/devCFconfigBuildRole"
PROFILE=dev
ENVIRONMENT=dev

CONFIG=tests/cloud-config.json
makedeploy $ROLE $PROFILE $ENVIRONMENT src/cfconfig/CloudFormation cloud_user $CONFIG
