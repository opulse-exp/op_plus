import os
import shutil
import json

# 输入 JSONL 文件路径和输出文件路径
input_file = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol.jsonl'  # JSONL 输入文件
cython_cache_dir = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operator_funcs_so'  # 存放 .so 文件的目录
target_dir = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operator_compiled_funcs_so/build/lib.linux-x86_64-cpython-310'  # 新的目标目录

# 确保目标目录存在
os.makedirs(target_dir, exist_ok=True)

# 打开输入 JSONL 文件并读取内容
with open(input_file, 'r', encoding='utf-8') as f:
    # 逐行读取 JSONL 文件
    for line in f:
        # 解析每一行的 JSON 数据
        data = json.loads(line.strip())
        
        # 获取 func_id
        func_id = data.get("func_id")
        
        if func_id:
            
            # 根据 func_id 构建对应的 .so 文件名
            so_file = f"module_{func_id}.cpython-310-x86_64-linux-gnu.so"
            
            # 获取 .so 文件的完整路径
            so_file_path = os.path.join(cython_cache_dir, so_file)
            
            # 如果 .so 文件存在，复制到目标目录
            if os.path.exists(so_file_path):
                target_so_path = os.path.join(target_dir, so_file)
                shutil.copy(so_file_path, target_so_path)
                print(f"复制文件 {so_file} 到 {target_so_path}")
            else:
                print(f"警告: 找不到文件 {so_file_path}")
