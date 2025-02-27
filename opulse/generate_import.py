import json

def extract_func_ids(jsonl_file_path):
    """
    从 JSONL 文件中提取所有的 'func_id' 字段并生成列表。
    
    :param jsonl_file_path: JSONL 文件路径
    :return: 包含所有 func_id 的列表
    """
    func_ids = []

    # 打开 JSONL 文件
    with open(jsonl_file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                # 解析每一行的 JSON 对象
                data = json.loads(line.strip())
                
                # 检查是否存在 'func_id' 字段
                if "func_id" in data:
                    func_ids.append(data["func_id"])
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line: {line}. Error: {e}")

    return func_ids

def generate_import_statements(func_ids, output_file_path):
    """
    根据 func_id 列表生成 from xx import * 的代码，并保存到文件中。
    
    :param func_ids: 包含 func_id 的列表
    :param output_file_path: 输出文件路径
    """
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("import sys\n")
        f.write("sys.path.append('/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/compiled_funcs')\n\n")
        for func_id in func_ids:
            # 生成 from xx import * 的代码
            import_statement = f"from module_{func_id} import *\n"
            f.write(import_statement)

# 示例用法
if __name__ == "__main__":
    # 替换为您的 JSONL 文件路径
    jsonl_file_path = "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100_test/final_base.jsonl"
    
    # 提取 func_id 列表
    func_id_list = extract_func_ids(jsonl_file_path)
    generate_import_statements(func_id_list, "import_statements.txt")