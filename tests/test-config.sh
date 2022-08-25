#! /bin/bash

ROLE="arn:aws:iam::324189914596:role/devCFconfigBuildRole"
PROFILE=dev
ENVIRONMENT=dev

exec ./package.sh python -m makeconfig $ROLE $PROFILE $ENVIRONMENT tests/cloud-config.json $@