#!/bin/bash

echo "setuptools_scm[toml]>=8.0" >> requirements-build.in
echo "flit_core<4,>=3.8" >> requirements-build.in
echo "setuptools<79.0.0,>=78.1.1" >> requirements-build.in
echo "hatchling<2,>=1.6.0" >> requirements-build.in
echo "calver>=2022.6.26" >> requirements-build.in
echo "urllib3<3.0.0,>=2.5.0" >> requirements-build.in
echo "hatch-vcs<0.6.0,>=0.4.0" >> requirements-build.in
echo "pbr>=1.8" >> requirements-build.in
echo "Cython>=3.0.8" >> requirements-build.in
echo "hatch-fancy-pypi-readme>=24.1.0" >> requirements-build.in
echo "mypy<=1.15.0,>=1.4.1" >> requirements-build.in
echo "types-psutil>=6.0.0.20240621" >> requirements-build.in
