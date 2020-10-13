#!/bin/bash

pip install .
pip install .[test]
ACG_CONFIG=./cdappconfig.json pytest
