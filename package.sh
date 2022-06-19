#! /bin/bash

PACKAGE_PYTHON_VERSION="3.10:latest"

PUBLISH_SERVER=localhost
PUBLISH_USER=packages

VIRTUAL_PREFIX="config"

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

    "run")
        shift
        PYTHONPATH="$PYTHONPATH:src" pyenv exec $@ 
    ;;
    "repl")
        PYTHONPATH="$PYTHONPATH:src" pyenv exec ptpython
    ;;
#
#   build
#
    "build")
        pyenv exec python -m build
    ;;

#
# dev environment
#
    "pull")
        pipenv install --skip-lock
        pyenv rehash
    ;;
    "all")
        python -m pip install -U pip
        python -m pip install -U pipenv
        pipenv install --dev --skip-lock
        pyenv rehash
    ;;
    "push")
        scp -o "StrictHostKeyChecking=no" dist/*-0.0.* "${PUBLISH_USER}@${PUBLISH_SERVER}:~/packages/dev/"
    ;;
#
# release environment
#
    "freeze")
        pipenv lock
    ;;
    "requirements")
        pipenv run python -m pip freeze
    ;;
    "release")
        pyenv exec python -m pip -U pip
        python -m pip install -U pipenv
        pipenv install --ignore-pipfile
        pyenv rehash
    ;;

#
# publish
#

    "publish")
        scp -o "StrictHostKeyChecking=no" dist/*-[0-9]*.[1-9]*.* "${PUBLISH_USER}@${PUBLISH_SERVER}:~/packages/release/"
    ;;
    *)
        echo "unknown command."
    ;;
esac
