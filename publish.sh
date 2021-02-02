#!/usr/bin/env bash

#build
python setup.py sdist bdist_wheel

#upload
twine upload --repository pypi dist/*