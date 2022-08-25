#! /bin/bash

ROLE="arn:aws:iam::324189914596:role/devCFconfigBuildRole"
PROFILE=dev
ENVIRONMENT=dev

CONFIG=tests/cloud-config.json
exec ./package.sh python -m makedeploy $ROLE $PROFILE $ENVIRONMENT CloudFormation cloud_user $CONFIG $@