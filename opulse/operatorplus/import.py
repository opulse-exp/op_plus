# import ctypes
# import glob
# import os
# from concurrent.futures import ProcessPoolExecutor
# from tqdm import tqdm  # 导入 tqdm 库

# def load_library(so_file):
#     try:
#         # 加载共享库并返回库对象
#         lib = ctypes.CDLL(so_file)
#         print(f"加载成功: {so_file}")
#         return lib  # 返回加载的库对象
#     except Exception as e:
#         print(f"加载库 {so_file} 出错: {e}")
#         return None  # 如果加载失败，返回 None

# def load_libraries_parallel():
#     so_dir = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs'
#     so_files = glob.glob(os.path.join(so_dir, '*.so'))

#     # 使用 tqdm 包装 so_files 以显示进度条
#     with ProcessPoolExecutor() as executor:
#         # tqdm() 会将进度条添加到 executor.map 中
#         libs = list(tqdm(executor.map(load_library, so_files), total=len(so_files), desc="加载共享库"))
#     return libs

# # 使用加载的库并返回指定的函数对象
# def use_libraries(libraries, func_name):
#     for lib in libraries:
#         if lib:
#             try:
#                 # 使用 getattr 动态访问库中的函数
#                 func = getattr(lib, func_name, None)
                
#                 if func:
#                     # 如果找到该函数，返回函数对象
#                     print(f"函数 {func_name} 已找到，返回函数对象")
#                     return func  # 返回函数对象
#                 else:
#                     print(f"该库没有名为 {func_name} 的函数")
#             except Exception as e:
#                 print(f"调用库函数出错: {e}")
#     return None  # 如果没有找到函数，则返回 None

# # # 加载库并调用函数
# # libs = load_libraries_parallel()
# # op_func = use_libraries(libs, "op_W4YGzv6Whe")

# # # 确保找到函数后才调用它
# # if op_func:
# #     print(op_func(1, 2))  # 调用函数并打印结果
# # else:
# #     print("没有找到指定的函数")

# lib = ctypes.cdll.LoadLibrary('/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs/module_W4YGzv6Whe.cpython-310-x86_64-linux-gnu.so')
# func = getattr(lib, 'op_W4YGzv6Whe', None)

# if func:
#     result = func(1, 2)
#     print(result)
# else:
#     print("函数未找到")

import importlib.util
import sys
import os

# 给定 .so 文件的路径
so_file = f"module_W4YGzv6Whe.cpython-310-x86_64-linux-gnu.so"
full_path = os.path.join("/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs", so_file)

# 动态加载模块
spec = importlib.util.spec_from_file_location('module_W4YGzv6Whe', full_path)
module = importlib.util.module_from_spec(spec)
sys.modules['module_W4YGzv6Whe'] = module
spec.loader.exec_module(module)

# 现在可以使用 `module` 中定义的内容
print(module.op_W4YGzv6Whe(1,2))
