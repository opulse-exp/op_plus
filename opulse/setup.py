from setuptools import setup, Extension
from Cython.Build import cythonize
import glob

# 查找所有的 .pyx 文件
# 查找指定目录下的所有 .pyx 文件
pyx_files = glob.glob("./operator_funcs_pyxs/*.pyx")


# 创建 Extension 对象，指定单个模块名，所有 .pyx 文件作为源文件
extensions = [
    Extension(
        name="operator_plus_funcs",  # 你希望生成的 .so 文件名
        sources=pyx_files  # 所有 .pyx 文件作为源文件
    )
]

# 设置编译选项
setup(
    ext_modules=cythonize(extensions, compiler_directives={'language_level': "3"}),
    script_args=["build_ext", "--inplace", "--parallel", "16"]  # 指定并行编译4个任务
)
