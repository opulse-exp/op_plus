import json

# 输入 JSONL 文件路径和输出文件路径
input_file = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol.jsonl'  # JSONL 输入文件
output_file = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operatorplus/operator_func.py'   # 生成的 Python 文件

# 打开输入 JSONL 文件并读取内容
with open(input_file, 'r', encoding='utf-8') as f:
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # 逐行读取 JSONL 文件
        for line in f:
            # 解析每一行的 JSON 数据
            data = json.loads(line.strip())
            
            # 获取 func_id
            func_id = data.get("func_id")
            
            if func_id:
                # 写入导入语句
                out_f.write(f"from module_{func_id} import *\n")

print(f"生成的文件已保存为: {output_file}")
# import json
# import os

# # 输入 JSONL 文件路径和输出文件路径
# input_file = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol.jsonl'  # JSONL 输入文件
# setup_file = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operatorplus/setup.py'  # 生成的 setup.py 文件

# # 读取 JSONL 文件
# with open(input_file, 'r', encoding='utf-8') as f:
#     # 读取所有 func_id 并生成对应的 .pyx 文件路径
#     pyx_modules = []
#     for line in f:
#         data = json.loads(line.strip())
#         func_id = data.get("func_id")
#         if func_id:
#             pyx_modules.append(f'/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs/module_{func_id}.pyx')

# # 生成 setup.py 文件内容
# setup_content = '''
# from setuptools import setup
# from Cython.Build import cythonize
# import sys

# sys.path.append('/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs')

# setup(
#     ext_modules=cythonize(
#         [
# '''

# # 将每个模块路径添加到 setup.py 中
# for module in pyx_modules:
#     setup_content += f'        "{module}",\n'

# # 完成 setup.py 内容
# setup_content += '''    ]),
#     compiler_directives={'language_level': "3"},
#     nthreads=20  
# )
# '''

# # 将生成的 setup.py 写入文件
# with open(setup_file, 'w', encoding='utf-8') as setup_f:
#     setup_f.write(setup_content)

# print(f"生成的 setup.py 文件已保存为: {setup_file}")
