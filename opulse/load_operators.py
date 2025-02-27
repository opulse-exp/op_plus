from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
import os
from operatorplus import *

# 外部处理函数
def load_operator_line(line, line_count, compiler, cython_cache_dir, logger, load_compile, operators):
    try:
        # Process each line to create an operator
        operator = OperatorInfo.from_json(line)
        
        so_file = f"module_{operator.func_id}.cpython-310-x86_64-linux-gnu.so"
        full_path = os.path.join(cython_cache_dir, so_file)
        
        # Check if module exists, and import if necessary
        if os.path.exists(full_path):
            operator.module = compiler.import_module_from_path(f"module_{operator.func_id}")
        else:
            if load_compile:
                func_code_str = f"thres = {2**31 - 1}\n\n"
                func_code_str += f"# Operator Func ID: {operator.func_id} - op_compute_func\n"
                func_code_str += f"{operator.op_compute_func}\n\n"
                func_code_str += f"# Operator Func ID: {operator.func_id} - op_count_func\n"
                func_code_str += f"{operator.op_count_func}\n\n"
                compiler.compile_function(func_code_str, operator.func_id, deps=None)
        
        # Update shared data structures
        operators[operator.func_id] = operator
        
        return operator, line_count

    except Exception as e:
        logger.warning(f"Failed to parse operator from line {line_count}: {e}")
        return None, line_count


# 外部函数：加载操作符
def load_operators(operator_file, param_config, logger, cython_cache_dir, compiler, load_compile=True, max_workers=4):
    """
    Loads operator definitions from a JSONL file using multiple processes.
    This function is now external to the OperatorManager class.

    Args:
        operator_file (str): The path to the operator configuration file (JSONL).
        param_config (ParamConfig): Configuration object for parameters.
        logger (LogConfig): Logger object for logging messages.
        cython_cache_dir (str): The directory where compiled modules are cached.
        compiler (CythonCompiler): Compiler object used for compiling functions.
        load_compile (bool, optional): Whether to compile the function. Defaults to True.
        max_workers (int, optional): Maximum number of worker processes to use. If None, defaults to the number of CPUs.

    Returns:
        tuple: A tuple containing three dictionaries:
            - operators (dict): Mapping of operator func_id to OperatorInfo.
            - symbol_to_operators (dict): Mapping of operator symbols to lists of OperatorInfo.
            - base_operators (dict): Mapping of base operators to lists of OperatorInfo.
    """
    logger.info(f"Loading operators from configuration file: {operator_file}")

    with open(operator_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Using Manager to create shared data structures
    with Manager() as manager:
        operators = manager.dict()  # Shared dictionary for operators

        # Using ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for line_count, line in enumerate(lines, start=1):
                if line.strip():  # Only process non-empty lines
                    futures.append(executor.submit(load_operator_line, line, line_count, compiler, cython_cache_dir, logger, load_compile, operators))

            for future in as_completed(futures):
                operator, line_count = future.result()
                if operator:
                    logger.debug(f"Loaded operator {operator.func_id} ({operator.symbol}) from line {line_count}.")

        # After processing, we assign the shared data back to a regular dictionary
        operators = dict(operators)

    logger.info(f"Successfully loaded {len(operators)} operators from the configuration file.")

    return operators

