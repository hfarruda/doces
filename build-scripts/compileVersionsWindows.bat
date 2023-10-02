
conda create -n buildpy35 -c default -c anaconda -c msys2 python=3.5 numpy libpython m2w64-toolchain
conda activate buildpy35
python setup.py bdist_wheel

conda create -n buildpy36 -c default -c anaconda -c msys2 python=3.6 numpy libpython m2w64-toolchain
conda activate buildpy36
python setup.py bdist_wheel

conda create -n buildpy37 -c default -c anaconda -c msys2 python=3.7 numpy libpython m2w64-toolchain
conda activate buildpy37
python setup.py bdist_wheel

conda create -n buildpy38 -c default -c anaconda -c msys2 python=3.8 numpy libpython m2w64-toolchain
conda activate buildpy38
python setup.py bdist_wheel
