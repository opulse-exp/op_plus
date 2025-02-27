from lark import Lark
import argparse
import os
from operatorplus import *
from expression.expression_generator import ExpressionGenerator
from hypothesis import given, settings, HealthCheck
import hypothesis.strategies as st
import ast
from config import LogConfig, ParamConfig
from typing import Dict, Any
import random
import numba
from config.constants import thres
import sys
import os
import importlib
import time
import hashlib

# # 将.so文件所在目录添加到sys.path
# so_file_path = "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/operatorplus/"
# sys.path.append(so_file_path)
# import op_func

global config
global logger
global compute_func, count_func

# def build_extension():
#     # 执行 python setup.py build_ext --inplace 命令并等待完成
#     # 文件路径，可以根据实际情况修改
#     os.system('python operatorplus/setup.py clean --all')
#     os.system('rm -rf build/')
#     result = os.system('python operatorplus/setup.py build_ext --inplace')
#     if result == 0:
#         print("Build completed successfully.")
#         # 删除缓存
#         sys.modules.pop('operatorplus.op_func', None)
        
#         time.sleep(2)  
#         importlib.reload(op_func)
#     else:
#         print(f"Build failed with status code {result}.")
        
def check_syntax(code: str) -> bool:
    logger.debug(f"Checking syntax for code: {code}")
    try:
        ast.parse(code)
        logger.info("Syntax is valid.")
        return True  
    except SyntaxError as e:
        logger.error(f"Syntax error: {e}")
        return False

def is_binary_operator(function):
    """
    判断一个函数是否是二元运算符。
    """
    # 获取函数的 AST（抽象语法树）
    tree = ast.parse(function)
    
    # 找到所有的函数定义
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 获取函数签名的参数
            arg_names = [arg.arg for arg in node.args.args]
            if len(arg_names) != 2:
                return False  # 如果参数不是两个，直接返回 False
            
            # 检查函数体是否使用了两个参数
            used_args = set()
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Name) and sub_node.id in arg_names:
                    used_args.add(sub_node.id)
            
            # 如果两个参数都被使用，则认为是二元运算
            return len(used_args) == 2
    return False


def is_unary_operator(function):
    """
    判断一个函数是否是一个一元运算符。
    """
    # 获取函数的 AST（抽象语法树）
    tree = ast.parse(function)
    
    # 找到所有的函数定义
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 获取函数签名的参数
            arg_names = [arg.arg for arg in node.args.args]
            if len(arg_names) != 1:
                return False  # 如果参数不是一个，直接返回 False
            
            # 检查函数体是否使用了这个唯一的参数
            used_args = set()
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Name) and sub_node.id in arg_names:
                    used_args.add(sub_node.id)
            
            # 如果唯一的参数被使用，则认为是有效的一元运算符
            return len(used_args) == 1
    
    return False

def check_single_function_call_with_same_args(function_code: str) -> bool:
    """
    Check if a function only calls a single other function, and if the parameter count of both
    functions is the same, return False. Otherwise, return True.

    Args:
        function_code (str): The source code of the function to check.

    Returns:
        bool: Returns False if the function calls a single function with the same number of arguments.
              Returns True otherwise.
    """
    try:
        tree = ast.parse(function_code)
    except SyntaxError:
        raise ValueError("Invalid Python code.")
    
    if len(function_code.strip().splitlines()) == 2:
        # This dictionary will store function names and their argument counts
        function_args = {}
        called_functions = set()  # Track called functions and their argument counts
        num_calls = 0  # Count total function calls in the function
        fun_name = None
        # First pass: Collect function argument counts
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_args[node.name] = len(node.args.args)  # Number of arguments for each function
                fun_name = node.name
        # Second pass: Analyze function calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                num_calls += 1
                if isinstance(node.func, ast.Name):  # Ensure the called function is a named function
                    called_function = node.func.id
                    called_functions.add((called_function, len(node.args)))  # Add function name and arg count

        # If there is exactly one function call
        if num_calls == 1 and len(called_functions) == 1:
            # Extract the called function's name and arg count
            called_function, called_arg_count = next(iter(called_functions))
            if function_args.get(fun_name) == called_arg_count:
                return False
    return True

def check_duplicate_returns_in_branches(function_code: str) -> bool:
    """
    Check if there are duplicate return statements in different branches (if/elif/else)
    of the same function.
    
    Args:
        function_code (str): The source code of the function to check.
    
    Returns:
        bool: Returns False if any branch has duplicate return statements, True otherwise.
    """
    try:
        tree = ast.parse(function_code)
    except SyntaxError:
        raise ValueError("Invalid Python code.")
    
    # Check each function in the abstract syntax tree
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return_statements = []
            # Check each node in the function body
            for body_node in node.body:
                if isinstance(body_node, ast.If):
                    # Check return statements in if, elif and else branches
                    for sub_node in ast.walk(body_node):
                        if isinstance(sub_node, ast.Return):
                            return_statements.append(ast.dump(sub_node))
                elif isinstance(body_node, ast.Return):
                    return_statements.append(ast.dump(body_node))

            # If there are duplicate return statements, return False
            if len(return_statements) != len(set(return_statements)):
                return False
    return True

def get_operator_compute_funcs(globals_dict):
    """
    获取当前 op_manager 中所有操作符的计算函数。
    """
    operator_compute_funcs = []
    all_operators = globals_dict["op_manager"].operators
    for operator_id, operator_info in all_operators.items():
        operator_compute_funcs.append(operator_info.op_compute_func)
    return operator_compute_funcs[:-1]

def extract_function_body(func):
    """
    提取函数体的代码内容，去掉函数的定义部分（即去掉 def 行）。
    """
    try:
        # 使用 ast.parse 解析函数定义
        tree = ast.parse(func)
        # 获取函数体部分（去掉 'def' 语句），即函数体的语句列表
        body = tree.body[0].body  # 获取函数体的节点列表

        # 将函数体的 AST 转换回代码字符串
        func_body_code = ast.unparse(body)  # 从 AST 节点列表生成代码
        return func_body_code
    except Exception as e:
        return None  # 解析失败返回 None

def compare_function_bodies(func1, func2):
    """
    比较两个函数的计算函数是否相同。通过解析 AST 来检测语法结构的相似性。
    """
    body1 = extract_function_body(func1)
    body2 = extract_function_body(func2)

    # 如果无法提取函数体，返回 False
    if body1 is None or body2 is None:
        return False

    # 比较函数体的 AST 结构
    return body1 == body2

def get_function_hash(func):
    """通过哈希计算函数体"""
    body = extract_function_body(func)
    if body is None:
        return None
    return hashlib.sha256(body.encode('utf-8')).hexdigest()

def check_function_similarity(new_func, existing_funcs):
    """
    检查当前新生成的操作符计算函数是否与已有操作符的计算函数同义。
    """
    new_func_hash = get_function_hash(new_func)
    if new_func_hash is None:
        return False

    # 遍历已有的哈希值，如果存在相同的哈希值，则进一步比较
    for existing_func in existing_funcs:
        existing_func_hash = get_function_hash(existing_func)
        if existing_func_hash == new_func_hash:
            # 如果哈希值相同，进一步比较函数体
            if compare_function_bodies(new_func, existing_func):
                return True
    return False


@given(st.integers(min_value=-thres, max_value=thres))
@settings(max_examples=5)
def test_unary_op_compute_func(a: int):
    logger.debug(f"Running test_unary_op_compute_func with a: {a}")
    try:
        result = compute_func(a)
        # logger.debug(f"Result of compute_func: {result}")
        assert isinstance(result, (int, float)), f"Expected result to be either an integer or a float, but got {type(result)}"
        # logger.info(f"test_unary_op_compute_func passed for a: {a}")
    except Exception as e:
        logger.error(f"Error in test_unary_op_compute_func with a: {a} - {e}")
        raise

@given(st.integers(min_value=-thres, max_value=thres))
@settings(max_examples=5)
def test_unary_op_count_func(a: int):
    logger.debug(f"Running test_unary_op_count_func with a: {a}")
    try:
        result = count_func(a)
        # logger.debug(f"Result of count_func: {result}")
        assert isinstance(result, (int, float)), f"Expected result to be either an integer or a float, but got {type(result)}"
        # logger.info(f"test_unary_op_count_func passed for a: {a}")
    except Exception as e:
        logger.error(f"Error in test_unary_op_count_func with a: {a} - {e}")
        raise

@given(st.integers(min_value=-thres, max_value=thres), st.integers(min_value=-thres, max_value=thres))
@settings(max_examples=5)
def test_binary_op_compute_func(a: int, b: int):
    logger.debug(f"Running test_binary_op_compute_func with a: {a}, b: {b}")
    try:
        result = compute_func(a, b)
        logger.debug(f"Running test_binary_op_compute_func with a: {a}, b: {b}, result: {result}")
        # logger.debug(f"Result of compute_func: {result}")
        assert isinstance(result, (int, float)), f"Expected result to be either an integer or a float, but got {type(result)}"
        # logger.info(f"test_binary_op_compute_func passed for a: {a}, b: {b}")
    except Exception as e:
        logger.error(f"Error in test_binary_op_compute_func with a: {a}, b: {b} - {e}")
        raise

@given(st.integers(min_value=-thres, max_value=thres), st.integers(min_value=-thres, max_value=thres))
@settings(max_examples=5)
def test_binary_op_count_func(a: int, b: int):
    logger.debug(f"Running test_binary_op_count_func with a: {a}, b: {b}")
    try:
        result = count_func(a, b)
        logger.debug(f"Running test_binary_op_count_func with a: {a}, b: {b}, result: {result}")
        # logger.debug(f"Result of count_func: {result}")
        assert isinstance(result, (int, float)), f"Expected result to be either an integer or a float, but got {type(result)}"
        # logger.info(f"test_binary_op_count_func passed for a: {a}, b: {b}")
    except Exception as e:
        logger.error(f"Error in test_binary_op_count_func with a: {a}, b: {b} - {e}")
        raise

def test_syntax_validity(op_compute_func: str, op_count_func: str) -> bool:
    logger.debug(f"Testing syntax validity for op_compute_func: {op_compute_func} and op_count_func: {op_count_func}")
    if check_syntax(op_compute_func) and check_syntax(op_count_func):
        logger.info("Both operator functions have valid syntax.")
        return True
    else:
        logger.error("One or both operator functions have syntax errors.")
        return False

def test_unary_op_executability():
    logger.debug("Running test_unary_op_executability")
    try:
        test_unary_op_compute_func()  # Just run the test, if no exception occurs, it passes
        test_unary_op_count_func()
        logger.info("Unary operator functions are executable.")
        return True
    except Exception as e:
        logger.error(f"Error in test_unary_op_executability: {e}")
        return False

def test_binary_op_executability():
    logger.debug("Running test_binary_op_executability")
    try:
        test_binary_op_compute_func() 
        test_binary_op_count_func()
        logger.info("Binary operator functions are executable.")
        return True
    except Exception as e:
        logger.error(f"Error in test_binary_op_executability: {e}")
        return False


# st_integers_range = st.integers(min_value=-1000, max_value=1000)

# # The idempotency verification (for unary operators)
# @given(st.integers())
# @settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
# def test_unary_idempotency(a: int):
#     try:
#         assert compute_func(compute_func(a)) == compute_func(a)
#     except Exception as e:
#         print(f"Error in {e}")
#         raise

# def valid_unary_idempotency():
#     try:
#         test_unary_idempotency() 
#         return True
#     except Exception as e:
#         print(e)
#         pass
    
# # Check commutativity: a op b == b op a
# @given(st.integers(), st.integers())
# @settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
# def test_binary_commutativity(a: int, b:int):
#     try:
#         assert compute_func(a,b) == compute_func(b,a)
#     except Exception as e:
#         print(f"Error in {e}")
#         return False

# def valid_binary_commutativity():
#     try:
#         test_binary_commutativity() 
#         return True
#     except Exception as e:
#         print(e)
#         return False
    
# # Check associativity: (a op b) op c == a op (b op c)
# @given(st.integers(), st.integers(), st.integers())
# @settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
# def test_binary_associativity(a: int, b: int, c: int):
#     try:
#         lhs = compute_func(compute_func(a, b), c)
#         rhs = compute_func(a, compute_func(b, c))
#         assert lhs == rhs
#     except Exception as e:
#         print(f"Error in {e}")
#         raise

# def valid_binary_associativity():
#     try:
#         test_binary_associativity() 
#         return True
#     except Exception as e:
#         print(e)
#         return False
    
# # Check absorption law: a op (a op b) == a
# @given(st.integers(), st.integers())
# @settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
# def test_binary_absorption(a: int, b: int):
#     try:
#         assert compute_func(a, compute_func(a, b)) == a
#     except Exception as e:
#         print(f"Error in {e}")
#         pass

# def valid_binary_absorption():
#     try:
#         test_binary_absorption() 
#         return True
#     except Exception as e:
#         print(e)
#         return False
    
# # Check idempotency: a op a == a
# @given(st.integers())
# @settings(max_examples=500, deadline=None, suppress_health_check=[HealthCheck.too_slow])
# def test_binary_idempotency(a: int):
#     try:
#         assert compute_func(a, a) == a
#     except Exception as e:
#         print(f"Error in {e}")
#         pass

# def valid_binary_idempotency():
#     try:
#         test_binary_idempotency() 
#         return True
#     except Exception as e:
#         print(e)
#         return False
    
# def validate_unary_property():
#     """
#     Validates all properties and returns a dictionary containing the validation results of all properties
#     """
#     validation_results = {
#         "idempotency": valid_unary_idempotency(),
#     }
#     return validation_results

# def validate_binary_property():
#     """
#     Validates all properties and returns a dictionary containing the validation results of all properties
#     """
#     validation_results = {
#         "commutativity": valid_binary_commutativity(),
#         "associativity": valid_binary_associativity(),
#         "absorption": valid_binary_absorption(),
#         "idempotency": valid_binary_idempotency(),
#     }
#     return validation_results


def initialize_globals(config_path: str, initial_operators_path: str, cython_cache_dir: str):
    """
    Initializes global variables including configuration loading, 
    creation of the operator manager, and related generators.
    
    This function loads the configuration, sets up logging, initializes
    the operator manager, and generates the required generators for 
    handling operators, conditions, and expressions.
    
    Args:
        config_path (str): Path to the configuration file.
        initial_operators_path (str): Path to the initial operator definitions.
    
    Returns:
        dict: A dictionary containing the initialized objects for configuration, logging, 
              operator manager, condition generator, expression generator, operator generator, 
              parser, transformer, and operator priority manager.
    """
    # Load configuration
    global config
    config = ParamConfig(config_path)
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    global logger
    logger = log.get_logger()
    # Initialize Operator Manager
    compiler = CythonCompiler(cython_cache_dir)
    op_manager = OperatorManager(initial_operators_path, config, log, compiler)
    # Initialize Generators
    condition_generator = ConditionGenerator(config, log, op_manager)
    expr_generator = ExpressionGenerator(config, log, op_manager)
    expr_parser = Simple_Expr_Parser(config, log)
    expr_transformer = Simple_Expr_Transformer(config, log, op_manager)
    
    op_generator = OperatorGenerator(
        param_config=config, 
        logger=log, 
        condition_generator=condition_generator, 
        expr_generator=expr_generator,
        operator_manager=op_manager
    )
    
    # Parsers and transformers
    parser = OperatorDefinitionParser(config, log)
    transformer = OperatorTransformer(config, log, op_manager)
    op_priority_manager = OperatorPriorityManager(log, op_manager)

    # Debug logging
    logger.debug("Global variables initialized successfully.")
    
    return {
        'config': config,
        'log': log,
        'logger': logger,
        'op_manager': op_manager,
        'condition_generator': condition_generator,
        'expr_generator': expr_generator,
        'op_generator': op_generator,
        'parser': parser,
        'transformer': transformer,
        'op_priority_manager': op_priority_manager,
        'compiler':compiler
    }

def generate_operator_type(globals_dict, file_path, operator_type, num, order):
    """
    Generate a specified type of operators and handle their creation, parsing, 
    transformation, and execution validation.

    This function:
    - Generates operators of the specified type.
    - Attempts to parse the operator definitions.
    - Transforms the parsed definition into executable functions.
    - Validates the syntax and executability of the generated operators.
    - Handles dependencies, calculates operator order, and saves valid operators.

    :param globals_dict: A dictionary containing all global objects including the operator manager and generators.
    :param operator_type: The type of operator to generate (e.g., 'simple_definition', 'recursive_definition').
    :param num: The number of operators to generate.
    """
    generated_count = 0
    while generated_count < num:
        # Create a new operator based on the specified type
        operator_data = globals_dict["op_generator"].create_operator_info(choice=operator_type, order=order)
        # new_operator = globals_dict["op_manager"].add_operator(operator_data) #不需要再添加进去了
        new_operator = OperatorInfo(**operator_data)
        # Update operator state to ensure it's not temporary
        new_operator.is_temporary = False
        globals_dict["logger"].debug(f"Operator Definition: {new_operator.definition}")

        if operator_type != "recursive_definition":
            try:
                # Attempt to parse the operator definition into a tree
                def_tree = globals_dict["parser"].parse_definition(new_operator.definition)
                globals_dict["logger"].debug(f"Parsed definition: {def_tree}")
            except Exception as e:
                globals_dict["logger"].error(f"Error parsing definition: {e}")
                # globals_dict["op_manager"].remove_operator(new_operator.id)
                continue

            if def_tree is not None:
                try:
                    # Transform the parsed definition into compute and count functions
                    new_operator.op_compute_func, new_operator.op_count_func = globals_dict["transformer"].generate_function(new_operator.func_id, new_operator.n_ary, def_tree)
                    new_operator.is_temporary = True
                except Exception as e:
                    globals_dict["logger"].error(f"Error transforming the parsed definition: {e}")
                    # globals_dict["op_manager"].remove_operator(new_operator.id)
                    continue

        # # Get the available functions from the operator manager
        # available_funcs = globals_dict["op_manager"].get_available_funcs()

        # Update global variables to ensure the correct compute and count functions are set
        global compute_func, count_func
        
        ##先提取它的依赖，为编译这个函数提供方便
        globals_dict["op_manager"].extract_op_dependencies(new_operator)
        
        dependencies = getattr(new_operator, 'dependencies', [])
        deps = [f"module_{dep}" for dep in dependencies]
        func_code_str = f"thres = {2**31 - 1}\n\n"#添加thres变量的值和限制
        func_code_str += f"# Operator Func ID: {new_operator.func_id} - op_compute_func\n"
        func_code_str += f"{new_operator.op_compute_func}\n\n"
        func_code_str += f"# Operator Func ID: {new_operator.func_id} - op_count_func\n"
        func_code_str += f"{new_operator.op_count_func}\n\n"
        globals_dict["compiler"].compile_function(func_code_str, new_operator.func_id, deps = deps) 
        op_module = globals_dict["compiler"].import_module(f"module_{new_operator.func_id}")
        # ##!编译这个计算函数和计数函数
        # globals_dict["compiler"].
        # globals_dict["op_manager"].save_op_funcs_to_file()

        compute_func = getattr(op_module, f"op_{new_operator.func_id}", None)
        count_func = getattr(op_module, f"op_count_{new_operator.func_id}", None)

        # # 动态获取计算函数和计数函数
        # compute_func = getattr(op_func, f"op_{new_operator.id}")
        # count_func = getattr(op_func, f"op_count_{new_operator.id}")
        
        if compute_func is None and count_func is None:
            globals_dict["logger"].debug("Compile func failed.")
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue  # 如果发现相似函数，跳过当前操作符
        
        # First, check the syntax validity of the compute and count functions
        if test_syntax_validity(new_operator.op_compute_func, new_operator.op_count_func) == False:
            globals_dict["logger"].debug("Code for operators has syntax errors")
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue
        if new_operator.n_ary == 1:
            if is_unary_operator(new_operator.op_compute_func)==False:
                globals_dict["logger"].debug("is_unary_operator_check is False")
                # globals_dict["op_manager"].remove_operator(new_operator.id)
                continue
        elif new_operator.n_ary == 2:
            if is_binary_operator(new_operator.op_compute_func)==False:
                globals_dict["logger"].debug("is_binary_operator_check is False")
                # globals_dict["op_manager"].remove_operator(new_operator.id)
                continue
        
        if check_single_function_call_with_same_args(new_operator.op_compute_func) ==False:
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue
        
        if check_single_function_call_with_same_args(new_operator.op_compute_func) ==False:
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue
        
        if check_duplicate_returns_in_branches(new_operator.op_compute_func) ==False:
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue
        
        # 获取当前 op_manager 中所有操作符的计算函数
        existing_funcs = get_operator_compute_funcs(globals_dict)

        # 检查新操作符的计算函数是否与现有操作符计算函数同义
        if check_function_similarity(new_operator.op_compute_func, existing_funcs):
            globals_dict["logger"].debug("Found a similar function in existing operators")
            # globals_dict["op_manager"].remove_operator(new_operator.id)
            continue  # 如果发现相似函数，跳过当前操作符
        
        
        # Validate whether the operator is executable based on its arity (1 or 2)
        if new_operator.n_ary == 1:
            # #先调用一次让numba进行临时编译
            # # try:
            # print(compute_func(0))
            # print(count_func(0))
            # except Exception as e:
            #     globals_dict["op_manager"].remove_operator(new_operator.id)
            #     continue
            is_executable = test_unary_op_executability()
        elif new_operator.n_ary == 2:
            # #先调用一次让numba进行临时编译

            # print(compute_func(0,0))
            # print(count_func(0,0))

            is_executable = test_binary_op_executability()

        
        # Process successful operators
        if is_executable:
            new_operator.is_temporary = False
            # # Record the operator's dependencies
            # globals_dict["op_manager"].extract_op_dependencies(new_operator.id)
            # Calculate the operator's order (priority)
            globals_dict["op_manager"].calculate_order(new_operator.func_id)
            #判断是否等于order
            if new_operator.n_order != order:
                globals_dict["logger"].debug("n_order is not equal to needed order.")
                # globals_dict["op_manager"].remove_operator(new_operator.id)
                continue  # 如果发现相似函数，跳过当前操作符
            
            # globals_dict["op_manager"].add_available_funcs(new_operator)
            
            # Validate the operator's properties
            #TODO: will be optimised to use the z3 library to find unsatisfiable a and b
            # if new_operator.n_ary == 1:
            #     new_operator.properties = validate_unary_property()
            # elif new_operator.n_ary == 2:
            #     new_operator.properties = validate_binary_property()
            
            globals_dict["logger"].debug(f"Operator {new_operator.id} is executable.")
            # globals_dict["op_manager"].save_operator_to_temp(new_operator)
            # globals_dict["logger"].debug(f"Operator {new_operator.id} has been successfully written to the temp file.")
            generated_count += 1
            new_operator = globals_dict["op_manager"].add_operator(operator_data) #这时候再加入manager
            # globals_dict["op_manager"].save_operators_to_jsonl(file_path)#这时候再根据文件的大小更新id并进行写入
        # else:
        #     globals_dict["op_manager"].remove_operator(new_operator.id)

def generate_randop(globals_dict: Dict[str, Any], file_path: str, num: int, order: int):
    """
    Generates random operators based on different types of definitions 
    and assigns priorities. The function will generate operators of 
    various types (simple, recursive, and branch) and then assign 
    binding, priority, and generate compute and count functions.

    The function follows these steps:
    1. Generates operators of different types (simple, recursive, 
       branch).
    2. Assigns binding and priority to the operators.
    3. Generates compute and count code for each operator.
    4. Saves the operators to a temporary file and assigns them to 
       the operator manager.

    Args:
        globals_dict (Dict[str, Any]): The global dictionary containing 
            configurations and relevant objects for operator generation.
        file_path (str): Path to the file where generated operators 
            will be saved.
        num (int): The total number of operators to generate.
    """
    
    # Get the number of base operators
    # base_operators_num = globals_dict["config"].get("max_base")
    # num = num - base_operators_num
    # Calculate the number of operators for each type of definition
    simple_definition_num = int(num * 0.2)  # Number of simple definitions
    # recursive_definition_num = int(num * 0.2)  # Number of recursive definitions
    branch_definition_num = int(num * 0.2)  # Number of branch definitions

    random_definition_num = num - simple_definition_num - branch_definition_num 
    
    # Generate simple definitions
    globals_dict["logger"].debug(f"Generating {simple_definition_num} simple definitions.")
    generate_operator_type(globals_dict, file_path, 'simple_definition', simple_definition_num, order)
    
    # Generate branch definitions
    globals_dict["logger"].debug(f"Generating {branch_definition_num} branch definitions.")
    generate_operator_type(globals_dict, file_path, 'branch_definition', branch_definition_num, order)
    
    # Generate recursive definitions
    #TODO:Problems with large numerical values
    # globals_dict["logger"].debug(f"Generating {recursive_definition_num} recursive definitions.")
    # generate_operator_type(globals_dict, 'recursive_definition', recursive_definition_num)

    # Generate random operators (simple, recursive, or branch)
    
    ###!修改了条件表达式的生成分支让它的分支变得更多了，一开始是3
    globals_dict["op_generator"].max_if_branches = 2
    globals_dict["op_generator"].expr_max_depth = 2
    remaining_operators = random_definition_num
    while remaining_operators > 0:
        # operator_type = random.choice(['simple_definition', 'branch_definition', 'recursive_definition'])
        operator_type = random.choice(['simple_definition', 'branch_definition'])
        globals_dict["logger"].debug(f"Generating 1 random operator of type {operator_type}.")
        generate_operator_type(globals_dict, file_path, operator_type, 1, order)
        remaining_operators -= 1

    # Assign priorities to all operators
    # globals_dict["logger"].debug("Assigning priorities to operators.")
    # globals_dict['op_priority_manager'].assign_priorities()

    # # Generate and add base operators to the operator manager
    # globals_dict["logger"].debug("Generating and adding base operators to the manager.")
    # globals_dict["op_generator"].generate_base_operators()

    # Rename temporary operators and save them to the specified file
    globals_dict["logger"].debug(f"Renaming temporary operators and saving to {file_path}.")
    # globals_dict["op_manager"].rename_temp_to_jsonl(file_path)
    globals_dict["op_manager"].save_operators_to_jsonl(file_path)


def generate_raise_order_operators(globals_dict: Dict[str, Any], file_path: str, num: int, order: int):
    globals_dict["expr_generator"].max_depth = 2
    
    globals_dict["logger"].debug(f"Generating {num} recursive definitions.")
    generate_operator_type(globals_dict, file_path, 'recursive_definition', num, order)

    # Rename temporary operators and save them to the specified file
    globals_dict["logger"].debug(f"Renaming temporary operators and saving to {file_path}.")
    # globals_dict["op_manager"].rename_temp_to_jsonl(file_path)
    globals_dict["op_manager"].save_operators_to_jsonl(file_path)
    
     
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Initialize and run the operator manager with custom configuration paths.")
    parser.add_argument('--config', type=str, default='config/generate_operator.yaml', help='Path to the config file')
    parser.add_argument('--initial-operators-path', type=str, default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_test/initial.jsonl", help='Path to the initial operator JSONL file')
    parser.add_argument('--generated-operators-path', type=str, default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_test/final.jsonl", help='Path where the final results should be saved')
     # 新增 cython-cache-dir 参数
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')
    parser.add_argument('--mode', type=str, choices=['raise', 'expand'], default='expand', help="Mode for operator generation: 'raise' for exponentiation (升阶), 'expand' for expansion (扩展)")
    parser.add_argument('--num', type=int, default=5, help='Number of operators to generate')
    parser.add_argument('--n_order', type=int, default=1, help='Order of operators to generate')

    # Parse arguments
    args = parser.parse_args()
    
    # Print debugging information
    print("==================================================")
    print("Starting the operator generation process...")
    print(f"Config Path: {args.config}")
    print(f"Initial Operators Path: {args.initial_operators_path}")
    print(f"Generated Operators Path: {args.generated_operators_path}")
    print(f"Cython Cache Directory: {args.cython_cache_dir}")
    print(f"Mode to Generate: {args.mode}")
    print(f"Number of Operators to Generate: {args.num}")
    print(f"Order of Operators to Generate: {args.n_order}")

    # Initialize global objects
    globals_dict = initialize_globals(config_path=args.config, initial_operators_path=args.initial_operators_path, cython_cache_dir=args.cython_cache_dir)

    if args.mode == 'raise':
        generate_raise_order_operators(globals_dict, args.generated_operators_path, args.num, args.n_order)
    else:
        generate_randop(globals_dict, args.generated_operators_path, args.num, args.n_order)






