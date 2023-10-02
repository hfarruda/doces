#!/usr/bin/env bash

eval "$(conda shell.bash hook)"

conda create -y -n buildpy35 python=3.5 numpy
conda activate buildpy35
python setup.py sdist bdist_wheel

conda create -y -n buildpy36 python=3.6 numpy
conda activate buildpy36
python setup.py sdist bdist_wheel

conda create -y -n buildpy37 python=3.7 numpy
conda activate buildpy37
python setup.py sdist bdist_wheel

conda create -y -n buildpy38 python=3.8 numpy
conda activate buildpy38
python setup.py sdist bdist_wheel
