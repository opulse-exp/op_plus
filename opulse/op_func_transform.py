##写一个从计算函数反向转回定义的函数
from lark import Lark
import argparse
from operatorplus import *
from expression.expression_generator import ExpressionGenerator
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
import ast
from config import LogConfig, ParamConfig
from typing import Dict, Any
import random
from config.constants import thres
import os
import hashlib
from collections import defaultdict
import json
import re
import random
import logging
from typing import List

global logger

def get_unicode_symbols() -> List[str]:
    unicode_ranges = [
        (0x2200, 0x22FF),  # Mathematical Operators
        (0x2A00, 0x2AFF),  # Supplemental Mathematical Operators
        (0x2190, 0x21FF),  # Arrows
    ]

    symbols = []

    for start, end in unicode_ranges:
        for codepoint in range(start, end + 1):
            char = chr(codepoint)
            symbols.append(char)

    return symbols

def random_operator(existing_symbols: List[str], valid_symbols: List[str], operator_symbol_min_len: int, operator_symbol_max_len: int) -> str:
    # Loop until a unique operator is generated
    while True:
        # Randomly choose a length for the operator within the specified range
        length = random.randint(operator_symbol_min_len, operator_symbol_max_len)

        # Generate the new symbol by randomly picking characters from valid symbols
        new_symbol = "".join(random.choice(valid_symbols) for _ in range(length))

        # Check if the generated symbol is unique (not in existing_symbols)
        if new_symbol not in existing_symbols:
            return new_symbol

def update_symbols_in_jsonl(input_jsonl_file: str, output_jsonl_file: str, valid_symbols: List[str], 
                            operator_symbol_min_len: int, operator_symbol_max_len: int):
    existing_symbols = set()  # A set to store existing symbols
    symbol_to_id = {}  # Dictionary to store (symbol, n_ary, unary_position) to (func_id, id)
    # duplicates = []  # To store duplicate records for logging purposes
    updated_data = []  # List to store the updated data

    try:
        # Open the input and output files
        with open(input_jsonl_file, 'r', encoding='utf-8') as infile, open(output_jsonl_file, 'w', encoding='utf-8') as outfile:
            print(f"Reading from {input_jsonl_file} and writing to {output_jsonl_file}")
            
            for line_number, line in enumerate(infile, start=1):
                try:
                    data = json.loads(line)  # Parse each line of JSON data
                    symbol = data.get('symbol')
                    n_ary = data.get('n_ary')
                    unary_position = data.get('unary_position')
                    func_id = data.get('func_id')
                    id_value = data.get('id')  # Get the id field value

                    # Create a unique key based on symbol, n_ary, and unary_position
                    key = (symbol, n_ary, unary_position)
                    existing_symbols.add(symbol)
                    if key in symbol_to_id:
                        # If the key already exists, log duplicates and modify the symbol
                        # duplicates.append((symbol, n_ary, unary_position, func_id, id_value, symbol_to_id[key][0], symbol_to_id[key][1]))
                        # Generate a new symbol for the duplicate
                        new_symbol = random_operator(existing_symbols, valid_symbols, operator_symbol_min_len, operator_symbol_max_len)
                        data['symbol'] = new_symbol  # Update the symbol field
                        print(f"Line {line_number}: Duplicate detected. Old symbol: {symbol}, new symbol generated: {new_symbol}")
                        key = (new_symbol, n_ary, unary_position)
                        # Add the symbol to the set of existing symbols
                        existing_symbols.add(data['symbol'])
                        
                    symbol_to_id[key] = (func_id, id_value)


                    updated_data.append(data)  # Add updated data to list

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON at line {line_number}: {e}")
                except Exception as e:
                    print(f"Error processing line {line_number}: {e}")
            
            # Write the updated data to the output file
            for entry in updated_data:
                json.dump(entry, outfile, ensure_ascii=False)
                outfile.write("\n")  # Write each JSON object on a new line
            
            # # Optionally log duplicates (can be removed or logged to a file)
            # if duplicates:
            #     print(f"Found {len(duplicates)} duplicates:")
            #     for duplicate in duplicates:
            #         print(duplicate)

    except FileNotFoundError:
        print(f"File not found: {input_jsonl_file}")
    except Exception as e:
        print(f"Error while reading the file: {e}")

def read_jsonl_file(jsonl_file_path):
    """
    读取 JSONL 文件并返回全部数据，使用 func_id 作为键。
    :param jsonl_file_path: JSONL 文件的路径
    :return: 以 func_id 为键，解析后的 JSON 数据为值的字典
    """
    data_dict = {}  # 用于存储以 func_id 为键的解析后 JSON 数据
    try:
        with open(jsonl_file_path, 'r', encoding='utf-8') as file:
            print(f"正在读取文件: {jsonl_file_path}")
            for line_number, line in enumerate(file, start=1):
                try:
                    # 解析每一行的 JSON 数据
                    data = json.loads(line)
                    # 获取 func_id 作为键
                    func_id = data.get('func_id')  # 假设 func_id 存在于 JSON 中
                    if func_id:
                        data_dict[func_id] = data  # 使用 func_id 作为键，存储数据
                    else:
                        print(f"警告: 在第 {line_number} 行未找到 func_id")
                except json.JSONDecodeError as e:
                    print(f"解析错误在第 {line_number} 行: {e}")
    except FileNotFoundError:
        print(f"文件未找到: {jsonl_file_path}")
    except Exception as e:
        print(f"读取文件时发生错误: {e}")
    
    return data_dict  # 返回以 func_id 为键的数据字典


def reverse_transform(config_path, initial_operators_path, cython_cache_dir, all_data, output_jsonl_path):
    processed_data = []  

    config = ParamConfig(config_path)
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    global logger
    logger = log.get_logger()
    
    parser = OperatorDefinitionParser(config, log)
    compiler = CythonCompiler(cython_cache_dir)
    op_manager = OperatorManager(initial_operators_path, config, log, compiler, False)
    transformer = OperatorTransformer(config, log, op_manager)
    # Traverse all data entries
    for func_id, entry in all_data.items():  # 使用 .items() 来遍历字典的键值对
    # 
    # entry = all_data["WvpRrkIbtT"]
        definition_type = entry.get('definition_type')
        op_compute_func = entry.get('op_compute_func')

        # Check if definition_type is either 'branch' or 'simple'
        if definition_type in ["branch_definition", "simple_definition"]:
            # Perform the operations for these types
            print(f"Processing entry with definition_type: {definition_type}")
            definition = parse_code(all_data, op_compute_func)
            definition_2 = parse_code_2(all_data, op_compute_func)
            def_tree = parser.parse_definition(definition)
            def_tree_2 = parser.parse_definition(definition_2)
            if def_tree is not None or def_tree_2 is not None:
                parse_op_compute_func, parse_op_count_func = transformer.generate_function(entry.get('func_id'), entry.get('n_ary'), def_tree)
                if parse_op_compute_func == op_compute_func:
                    entry["definition"]=definition
                    print(f"{entry.get('func_id')}已经被成功地替换")
                else:
                    parse_op_compute_func, parse_op_count_func = transformer.generate_function(entry.get('func_id'), entry.get('n_ary'), def_tree_2)
                    if parse_op_compute_func == op_compute_func:
                        entry["definition"]=definition_2
                        print(f"{entry.get('func_id')}已经被成功地替换")
                    else:
                        raise ValueError(f"Error: {entry.get('func_id')} could not be processed correctly.")
            # Here you can replace the print statement with your actual processing logic
            # Example operation: you can modify or append values to the entry
            # entry['new_field'] = 'processed_value'  # Just an example of modification
            # lhs=
            else:
                raise ValueError(f"Error: {entry.get('func_id')} could not be processed correctly.")
        processed_data.append(entry)
    
    
     # Write the processed data to a JSONL file
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for entry in processed_data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')  # Write a newline after each JSON object
    
    print(f"Processed data has been written to {output_jsonl_path}")
    
    return processed_data
    
    
    
    
    


def parse_code(all_data, source_code):
    """
    解析 Python 代码并生成抽象语法树，遍历树的节点并返回最后一个字符串。

    参数:
        source_code (str): 要解析的 Python 代码字符串。

    返回:
        str: 生成的字符串表达式。
    """
    # 使用 ast.parse 解析代码并生成抽象语法树
    tree = ast.parse(source_code)

    # 打印 AST 树的结构
    print(ast.dump(tree, indent=4))

    def visit_node(node):
        """
        访问 AST 中的每个节点并打印其详细信息。
        """
        if isinstance(node, ast.FunctionDef):
            print(f"Function: {node.name}")
            print(f"Arguments: {[arg.arg for arg in node.args.args]}")
            func_name = node.name
            match = re.search(r'op_(\w+)', func_name)
            func_id = match.group(1)
            params = [arg.arg for arg in node.args.args]
            params_length = len(params)
            operator = all_data[func_id]
            symbol = operator["symbol"]
            n_ary = operator["n_ary"]
            unary_position = operator["unary_position"]

            if n_ary == 2:
                lhs = f"a{symbol}b"
            elif n_ary == 1 and unary_position == "prefix":
                lhs = f"{symbol}a"
            elif n_ary == 1 and unary_position == "postfix":
                lhs = f"a{symbol}"
            else:
                print(f"Warning: {func_id} not found in all_data.")
 
            rhs = visit_node(node.body[0]) 
            return f"{lhs} = {{ {rhs} }}"

        elif isinstance(node, ast.If):
            print("If Statement:")
            print("Test Expression:")
            condition = visit_node(node.test)  # 递归访问条件部分
            print("Body:")
            result_string = visit_node(node.body[0])
            print("Else Body:")
            if isinstance(node.orelse[0], ast.If):
                elif_string = visit_node(node.orelse)
                return f"{result_string} , if {condition} ; {elif_string}"
            else:
                else_string = visit_node(node.orelse[0])
                return f"{result_string} , if {condition} ; {else_string} , else"

        elif isinstance(node, ast.Return):
            print("Return Statement:")
            return f"{visit_node(node.value)}"  # 递归访问返回值
        elif isinstance(node, ast.BoolOp):  # 处理布尔运算符（and/or）
            print(f"Boolean Operation: {type(node.op)}")
            # left_value = f"{visit_node(node.values[0])}"
            # operator = "and" if isinstance(node.op, ast.And) else "or"
            # right_value = f"{visit_node(node.values[1])}"
            
            # 递归处理每个条件并生成表达式
            left_value = visit_node(node.values[0])
            operator = "and" if isinstance(node.op, ast.And) else "or"
            
            # 遍历剩余的条件，逐个添加连接符
            for right_value in node.values[1:]:
                right_value_expr = visit_node(right_value)
                left_value = f"{left_value} {operator} {right_value_expr}"  # 使用括号避免优先级问题
    
            return f"({left_value})"
                
        elif isinstance(node, ast.Compare):
            print("Compare Expression:")
            left_value = visit_node(node.left)  # 递归访问比较的左操作数
            
            operator_mapping = {
                ast.Lt: "<",
                ast.Gt: ">",
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.LtE: "<=",
                ast.GtE: ">="
            }
            
            #我们这里的node.ops和node.comparators应该都是只有一个
            for op in node.ops:
                # 获取操作符的符号
                operator = operator_mapping.get(type(op), str(op))  # 默认使用操作符类的字符串表示

            for comparator in node.comparators:
                right_value = visit_node(comparator)  # 递归访问比较的右操作数
            return f"{left_value}{operator}{right_value}"
            
        #如果是一个函数调用
        elif isinstance(node, ast.Call):
            print(f"Function Call: {node.func.id if isinstance(node.func, ast.Name) else 'Unknown'}")
            args_values = []  # 用于存储每个参数的值
            for arg in node.args:
                arg_value = visit_node(arg)  # 递归访问并获取参数值
                args_values.append(arg_value)
            # 在此你可以根据需要将参数值与函数调用一起处理
            # print(f"Arguments: {args_values}")
            match = re.search(r'op_(\w+)', node.func.id)
            func_id = match.group(1)
            operator = all_data[func_id]
            symbol = operator["symbol"]
            n_ary = operator["n_ary"]
            unary_position = operator["unary_position"]
            if n_ary == 2:
                return f"({args_values[0]}{symbol}{args_values[1]})"
            elif n_ary == 1 and unary_position == "prefix":
                return f"({symbol}{args_values[0]})"
            elif n_ary == 1 and unary_position == "postfix":
                return f"({args_values[0]}{symbol})"
        
        #最小的单位就是常量或者是name(字母a或者b)，都是输入的内容
        elif isinstance(node, ast.Constant):
            print(f"Constant: {node.value}")
            return node.value
        elif isinstance(node, ast.Name):
            print(f"Name: {node.id}")
            return node.id
        else:
            print(f"Other node type: {type(node)}")
    definition = visit_node(tree.body[0])
    return definition

##或者不加括号的
def parse_code_2(all_data, source_code):
    """
    解析 Python 代码并生成抽象语法树，遍历树的节点并返回最后一个字符串。

    参数:
        source_code (str): 要解析的 Python 代码字符串。

    返回:
        str: 生成的字符串表达式。
    """
    # 使用 ast.parse 解析代码并生成抽象语法树
    tree = ast.parse(source_code)

    # 打印 AST 树的结构
    print(ast.dump(tree, indent=4))

    def visit_node(node):
        """
        访问 AST 中的每个节点并打印其详细信息。
        """
        if isinstance(node, ast.FunctionDef):
            print(f"Function: {node.name}")
            print(f"Arguments: {[arg.arg for arg in node.args.args]}")
            func_name = node.name
            match = re.search(r'op_(\w+)', func_name)
            func_id = match.group(1)
            params = [arg.arg for arg in node.args.args]
            params_length = len(params)
            operator = all_data[func_id]
            symbol = operator["symbol"]
            n_ary = operator["n_ary"]
            unary_position = operator["unary_position"]

            if n_ary == 2:
                lhs = f"a{symbol}b"
            elif n_ary == 1 and unary_position == "prefix":
                lhs = f"{symbol}a"
            elif n_ary == 1 and unary_position == "postfix":
                lhs = f"a{symbol}"
            else:
                print(f"Warning: {func_id} not found in all_data.")
 
            rhs = visit_node(node.body[0]) 
            return f"{lhs} = {{ {rhs} }}"

        elif isinstance(node, ast.If):
            print("If Statement:")
            print("Test Expression:")
            condition = visit_node(node.test)  # 递归访问条件部分
            print("Body:")
            result_string = visit_node(node.body[0])
            print("Else Body:")
            if isinstance(node.orelse[0], ast.If):
                elif_string = visit_node(node.orelse)
                return f"{result_string} , if {condition} ; {elif_string}"
            else:
                else_string = visit_node(node.orelse[0])
                return f"{result_string} , if {condition} ; {else_string} , else"

        elif isinstance(node, ast.Return):
            print("Return Statement:")
            return f"{visit_node(node.value)}"  # 递归访问返回值
        elif isinstance(node, ast.BoolOp):  # 处理布尔运算符（and/or）
            print(f"Boolean Operation: {type(node.op)}")
            # left_value = f"{visit_node(node.values[0])}"
            # operator = "and" if isinstance(node.op, ast.And) else "or"
            # right_value = f"{visit_node(node.values[1])}"
            
            # 递归处理每个条件并生成表达式
            left_value = visit_node(node.values[0])
            operator = "and" if isinstance(node.op, ast.And) else "or"
            
            # 遍历剩余的条件，逐个添加连接符
            for right_value in node.values[1:]:
                right_value_expr = visit_node(right_value)
                left_value = f"{left_value} {operator} {right_value_expr}"  # 使用括号避免优先级问题
    
            return f"{left_value}"
        
                
        elif isinstance(node, ast.Compare):
            print("Compare Expression:")
            left_value = visit_node(node.left)  # 递归访问比较的左操作数
            
            operator_mapping = {
                ast.Lt: "<",
                ast.Gt: ">",
                ast.Eq: "==",
                ast.NotEq: "!=",
                ast.LtE: "<=",
                ast.GtE: ">="
            }
            
            #我们这里的node.ops和node.comparators应该都是只有一个
            for op in node.ops:
                # 获取操作符的符号
                operator = operator_mapping.get(type(op), str(op))  # 默认使用操作符类的字符串表示

            for comparator in node.comparators:
                right_value = visit_node(comparator)  # 递归访问比较的右操作数
            return f"{left_value}{operator}{right_value}"
            
        #如果是一个函数调用
        elif isinstance(node, ast.Call):
            print(f"Function Call: {node.func.id if isinstance(node.func, ast.Name) else 'Unknown'}")
            args_values = []  # 用于存储每个参数的值
            for arg in node.args:
                arg_value = visit_node(arg)  # 递归访问并获取参数值
                args_values.append(arg_value)
            # 在此你可以根据需要将参数值与函数调用一起处理
            # print(f"Arguments: {args_values}")
            match = re.search(r'op_(\w+)', node.func.id)
            func_id = match.group(1)
            operator = all_data[func_id]
            symbol = operator["symbol"]
            n_ary = operator["n_ary"]
            unary_position = operator["unary_position"]
            if n_ary == 2:
                return f"({args_values[0]}{symbol}{args_values[1]})"
            elif n_ary == 1 and unary_position == "prefix":
                return f"({symbol}{args_values[0]})"
            elif n_ary == 1 and unary_position == "postfix":
                return f"({args_values[0]}{symbol})"
        
        #最小的单位就是常量或者是name(字母a或者b)，都是输入的内容
        elif isinstance(node, ast.Constant):
            print(f"Constant: {node.value}")
            return node.value
        elif isinstance(node, ast.Name):
            print(f"Name: {node.id}")
            return node.id
        else:
            print(f"Other node type: {type(node)}")
    definition = visit_node(tree.body[0])
    return definition

def parse_function(function_node):
    """
    解析函数节点并生成所需的字符串。
    """
    # 获取函数参数
    param_a = function_node.args.args[0].arg  # 'a'
    param_b = function_node.args.args[1].arg  # 'b'

    # 获取函数体的if-else部分
    if_node = function_node.body[0]
    if_test = if_node.test
    if_body = if_node.body[0].value
    else_body = if_node.orelse[0].value

    # 提取比较符号和数值
    comparison_operator = if_test.ops[0]  # 比较符号
    comparison_value = if_test.comparators[0].value  # 575

    # 提取运算符
    op_a = extract_operator(if_body)
    op_b = extract_operator(else_body)

    # 构造字符串输出
    expression = f"{param_a}⨁⊸⫻ = {{ ({op_a}) , if {param_a} {comparison_operator} {comparison_value} ; {param_a}, else }}"

    return expression

###!1. 更新symbol
# Example usage
# input_jsonl_path = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final.jsonl'
# output_jsonl_path = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol.jsonl'
# valid_symbols = get_unicode_symbols()
# operator_symbol_min_len = 1
# operator_symbol_max_len = 3

# update_symbols_in_jsonl(input_jsonl_path, output_jsonl_path, valid_symbols, operator_symbol_min_len, operator_symbol_max_len)


###!2.根据更新以后的symbol来更新定义
input_jsonl_path = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol.jsonl'
all_data = read_jsonl_file(input_jsonl_path)
output_jsonl_path = '/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol_final.jsonl'
config_path = "config/generate_operator.yaml"
cython_cache_dir = "./compiled_funcs"
reverse_transform(config_path, input_jsonl_path, cython_cache_dir, all_data, output_jsonl_path)