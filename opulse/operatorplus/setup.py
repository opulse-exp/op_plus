from setuptools import setup
from Cython.Build import cythonize
import sys

sys.path.append('/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs')

setup(
    ext_modules=cythonize(
        "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operatorplus/operator_func.pyx", 
        compiler_directives={'language_level': "3"}
    )
)
