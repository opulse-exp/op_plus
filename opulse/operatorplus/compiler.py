import os
import sys
import pyximport
from Cython.Build import cythonize
from pathlib import Path
import importlib
import sys
from typing import Optional
from types import ModuleType

class CythonCompiler:
    def __init__(self, compile_dir: str = './compiled_funcs'):
        """
        Initializes the Cython compiler, sets the compilation directory, and ensures it exists.

        Parameters:
            compile_dir (str): Directory to store compiled modules, default is './compiled_funcs'.

        Raises:
            OSError: If the directory cannot be created due to permission issues or other errors.
        """
        self.compile_dir = Path(compile_dir)
        if not self.compile_dir.exists():
            self.compile_dir.mkdir()
        
        sys.setdlopenflags(os.RTLD_NOW | os.RTLD_GLOBAL)

    def compile_function(self, func_code: str, func_name: str, deps: list = None) -> None:
        """
        Dynamically compiles a Cython function and generates a module.

        Parameters:
            func_code (str): The new function code provided as a string.
            func_name (str): The function name, used to generate the module name and file name.
            deps (List[str]): List of dependent modules, default is None (no dependencies).

        Raises:
            Exception: If there is an error during the compilation process.
        """
        module_name = f"module_{func_name}"
        if self.import_module(module_name) == None:
            
            if deps is None:
                deps = []

        
            pyx_file_path = self.compile_dir / f"{module_name}.pyx"

            with open(pyx_file_path, "w") as f:
                for dep in deps:
                    f.write(f"from {dep} import *\n")
                f.write(func_code)
            try:
                # os.system(f"cythonize -a -i -j 8 -3 {pyx_file_path}")
                os.system(f"cythonize -i -j 8 -3 {pyx_file_path}")
                # cythonize([str(pyx_file_path)], build_dir=str(self.compile_dir))
                print(f"Successfully compiled {module_name}")
            except Exception as e:
                print(f"Error compiling {module_name}: {e}")

            
    def import_module(self, module_name) -> Optional[ModuleType]:
        """
        Attempts to import the specified module from the compilation directory.

        Parameters:
            module_name (str): The name of the module.

        Returns:
            Optional[ModuleType]: Returns the imported module object on success; returns `None` on failure.

        Raises:
            ImportError: If the module cannot be imported due to missing dependencies or other issues.
        """
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
    
    def import_module_from_path(self, module_name) -> ModuleType:
        """
        Dynamically loads a module via its `.so` file path.

        Parameters:
            module_name (str): The name of the module.

        Returns:
            ModuleType: Returns the loaded module object on success.

        Raises:
            FileNotFoundError: If the `.so` file does not exist in the specified directory.
            ImportError: If the module cannot be loaded due to invalid file format or other issues.
        """

        compiled_dir = str(Path(self.compile_dir).resolve())
        so_file = f"{module_name}.cpython-310-x86_64-linux-gnu.so"
        full_path = os.path.join(compiled_dir, so_file)

        spec = importlib.util.spec_from_file_location(module_name, full_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = ModuleType
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
#     print("Simple function compiled and imported successfully.")


# test_compile_simple_function()
