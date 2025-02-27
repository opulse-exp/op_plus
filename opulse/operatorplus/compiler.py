import os
import sys
import pyximport
from Cython.Build import cythonize
from pathlib import Path
import importlib
import sys

class CythonCompiler:
    def __init__(self, compile_dir: str = './compiled_funcs'):
        """
        初始化Cython编译器, 设置编译目录并确保该目录存在。

        参数:
        - compile_dir: 存储已编译模块的目录，默认为'./compiled_funcs'
        """
        self.compile_dir = Path(compile_dir)
        if not self.compile_dir.exists():
            self.compile_dir.mkdir()
        
        sys.setdlopenflags(os.RTLD_NOW | os.RTLD_GLOBAL)

    def compile_function(self, func_code: str, func_name: str, deps: list = None) -> None:
        """
        动态编译一个Cython函数并生成一个模块。
        
        参数:
        - func_code: 新的函数代码
        - func_name: 函数名称
        - deps: 依赖模块的列表, 默认None表示没有依赖
        """
         # 尝试导入模块
        # 准备模块名称和文件路径
        module_name = f"module_{func_name}"
        if self.import_module(module_name) == None:
            
            if deps is None:
                deps = []

        
            pyx_file_path = self.compile_dir / f"{module_name}.pyx"

            # 生成 .pyx 文件
            with open(pyx_file_path, "w") as f:
                # 如果有依赖模块，先写入 import 语句
                for dep in deps:
                    f.write(f"from {dep} import *\n")
                
                # 然后写入新的函数代码
                f.write(func_code)

            try:
                #4是并发编译
                # os.system(f"cythonize -a -i -j 8 -3 {pyx_file_path}")
                
                os.system(f"cythonize -i -j 8 -3 {pyx_file_path}")
                # cythonize([str(pyx_file_path)], build_dir=str(self.compile_dir))
                print(f"Successfully compiled {module_name}")
            except Exception as e:
                print(f"Error compiling {module_name}: {e}")

            
    def import_module(self, module_name):
        compiled_dir = str(Path(self.compile_dir).resolve())
        # Ensure sys.path is set up correctly
        if compiled_dir not in sys.path:
            sys.path.insert(0, compiled_dir)
        try:
            # Try importing the module
            imported_module = importlib.import_module(module_name)
            print(f"Module {module_name} imported successfully.")
            return imported_module
        except Exception as e:
            # print(f"Error importing module {module_name}: {e}")
            return None
    
    def import_module_from_path(self, module_name):
        compiled_dir = str(Path(self.compile_dir).resolve())
        so_file = f"{module_name}.cpython-310-x86_64-linux-gnu.so"
        full_path = os.path.join(compiled_dir, so_file)

        # 动态加载模块
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module#缓存模块
        spec.loader.exec_module(module)
        return module

# def test_compile_simple_function():
#     compiler = CythonCompiler()
#     func_code = """
# def add(a, b):
#     return a + b
# """
#     compiler.compile_function(func_code, "add")
#     module_add=compiler.import_module("module_add")
#     print(module_add.add(3,4))
#     # 如果没有异常输出，说明编译和导入成功
#     print("Simple function compiled and imported successfully.")


# test_compile_simple_function()
