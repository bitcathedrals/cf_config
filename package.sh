#! /bin/bash

PACKAGE_PYTHON_VERSION="3.10:latest"

PUBLISH_SERVER=localhost
PUBLISH_USER=packages

VIRTUAL_PREFIX="config"

REGION='us-west-2'
VERSION=0.6.3

case $1 in

#
# tooling
#

    "install-tools")
        brew update

        brew install pyenv
        brew install pyenv-virtualenv
    ;;
    "update-tools")
        brew update

        brew upgrade pyenv
        brew upgrade pyenv-virtualenv
    ;;

#
# virtual environments
#
    "virtual-install")
        pyenv install --skip-existing "$PACKAGE_PYTHON_VERSION"

        LATEST=$(pyenv versions | grep -E '^ *\d+\.\d+\.\d+$' | sed 's/ *//g')

        echo "installing $LATEST to $VIRTUAL_PREFIX"

        pyenv virtualenv "$LATEST" "${VIRTUAL_PREFIX}_release"
        pyenv virtualenv "$LATEST" "${VIRTUAL_PREFIX}_dev"
    ;;
    "virtual-destroy")
        pyenv virtualenv-delete "${VIRTUAL_PREFIX}_release"
        pyenv virtualenv-delete "${VIRTUAL_PREFIX}_dev"
    ;;

    "virtual-list")
        pyenv virtualenvs
    ;;

#
# all environments
#
    "versions")
        pyenv version
        pyenv exec python --version
        pipenv graph
    ;;
    "test")
        PYTHONPATH="$PYTHONPATH:src" pyenv exec python -m pytest tests
    ;;
    "python")
        shift
        PYTHONPATH="$PYTHONPATH:src:CloudFormation:" pyenv exec python $@
    ;;
    "run")
        shift
        PYTHONPATH="$PYTHONPATH:src" pyenv exec $@ 
    ;;
    "aws")
        shift
        pyenv exec python -m awscli $@
    ;;
    "cf")
        shift

        export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s" \
                    $(aws sts assume-role \
                    --role-arn arn:aws:iam::324189914596:role/devCFconfigBuildRole \
                    --role-session-name DevCloudFormationSession \
                    --profile dev \
                    --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
                    --output text))

        pyenv exec python -m awscli --region $REGION $@
    ;;
    "validate")
        pyenv exec python -m awscli cloudformation validate-template --template-body file://$2 --profile $AWS_PROFILE
   ;;

    "cli-delete")
        echo "attempting to delete stack: $2"
        PYTHONPATH="$PYTHONPATH:src" pyenv exec python -m awscli cloudformation delete-stack --stack-name $2
    ;;
    "cli-describe")
        echo "attempting to describe stack: $2"
        PYTHONPATH="$PYTHONPATH:src" pyenv exec python -m awscli cloudformation describe-stacks --stack-name $2
    ;;

    "build")
        pyenv exec python -m build
    ;;

#
# dev environment
#
    "pull")
        pyenv exec python -m pipenv install --skip-lock
        pyenv exec python -m pyenv rehash
    ;;
    "all")
        pyenv exec python -m pip install -U pip
        pyenv exec python -m pip install -U pipenv
        pyenv exec python -m pipenv install --dev --skip-lock
        pyenv rehash
    ;;
    "push")

    "list")
        pyenv exec python -m pipenv graph
    ;;
#
# release environment
#
    "release-m1")
        pyenv exec python -m pyenv -m pip -U pip
        pyenv exec python -m pyenv install -U pipenv
        pyenv exec python -m pipenv install --ignore-pipfile
        pyenv rehash

        test -d releases || mkdir releases
        pyenv exec python -m pipenv lock
        mv Pipfile.lock releases/Pipfile.lock-$VERSION

        git push --all
        git push --tags

        pyenv exec python -m build

        DIST_PATH="/Users/michaelmattie/coding/python-packages/"
        PKG_PATH="$DIST_PATH/simple/cfconfig"
        BEAST="michaelmattie@beast.local"

        ssh $BEAST "test -d $PKG_PATH || mkdir $PKG_PATH"
        scp dist/* "$BEAST:$PKG_PATH/"
        ssh $BEAST "cd $DISTPATH && ./upload-new-packages.sh"
        ssh $BEAST "cd $DISTPATH && mv simple/cfconfig/* remote/cfconfig/ && ./update-packages.sh"
    ;;
    *)
        echo "unknown command."
    ;;
esac
