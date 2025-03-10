import concurrent.futures
import time
from typing import Dict, Any, List, Tuple
import os
import argparse
import logging
import traceback
from operatorplus import *
from generate_operator_type import initialize_globals, generate_operator_type

from operatorplus.operator_manager import OperatorManager
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson
import random
# Global variables for worker processes
globals_dict = None

def worker_generate_operator(operator_type, order):
    """
    Worker function to generate a single expression.
    Returns the generated properties and the time taken.
    """
    start_time_expr = time.time()
    # Generate expression
    operator = generate_operator_type(globals_dict, operator_type, order)
    end_time_expr = time.time()
    time_taken = end_time_expr - start_time_expr
    return operator, time_taken

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')

def generate_operators_multiprocess(
    config_path: str,
    initial_operators_path: str,
    cython_cache_dir: str,
    initial_idx: int,
    tasks: List[Tuple[str, int]],  # 每个任务格式：(operator_type, order)
    max_workers: int,
    file_path: str,
):
    """
    Generates expressions using multiple processes and writes them to a file.
    """
    start_time = time.time()

    results = []
    batch_size = 1
    print(globals_dict["op_manager"].operators)
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=max_workers,
    ) as executor, open(file_path, "a", encoding="utf-8") as f:  
        futures = [executor.submit(worker_generate_operator, op_type, order) for (op_type, order) in tasks]
        for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                operator, time_taken = future.result()
                operator.id = initial_idx + idx  
                globals_dict["op_manager"].add_operator(operator) 
                results.append(orjson.dumps(operator.to_dict()))
                if len(results) >= batch_size or idx == len(tasks):
                    batch_write_to_file(results, f)
                    results.clear()
                    logging.info(f"Batch write completed up to operator {idx}")
                    print(f"Batch Generate expressions cost {time_taken:.2f}s")
            except Exception as e:
                print(f"Error in task {idx}:\n{traceback.format_exc()}")
                logging.error(f"Error generating operator {idx}: {e}")    
    end_time = time.time()
    logging.info(f"Generated {len(tasks)} operators. Total time: {end_time - start_time:.2f}s")
    
def generate_randop(
    config_path: str,
    initial_operators_path: str,
    cython_cache_dir: str,
    initial_idx: int,
    num: int,
    max_workers: int,
    file_path: str,
    order: int
):
    simple_num = int(num * 0.2)
    branch_num = int(num * 0.2)
    random_num = num - simple_num - branch_num

    tasks = []
    tasks.extend([('simple_definition', order)] * simple_num)
    tasks.extend([('branch_definition', order)] * branch_num)
    tasks.extend([(random.choice(['simple_definition', 'branch_definition']), order) for _ in range(random_num)])

    generate_operators_multiprocess(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        initial_idx = initial_idx,
        tasks=tasks,
        max_workers=max_workers,
        file_path=file_path
    )

def generate_raise_order_operators(
    config_path: str,
    initial_operators_path: str,
    cython_cache_dir: str,
    initial_idx: int,
    num: int,
    max_workers: int,
    file_path: str,
    order: int
):
    tasks = [('recursive_definition', order)] * num
    
    generate_operators_multiprocess(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        initial_idx = initial_idx,
        tasks=tasks,
        max_workers=max_workers,
        file_path=file_path
    )


def is_file_empty(file_path):
    return os.stat(file_path).st_size == 0


def calculate_layers_with_increase(total_elements, num_layers, ratio, raise_increase_at_order=3, increase_count=3):
    """
    Calculate the number of elements at each level using a proportionally decreasing method, and generate the number of items based on the order.

    :param total_elements: Total number of elements
    :param num_layers: Number of layers
    :param ratio: Decrease ratio for each layer relative to the previous one (e.g., 0.8 means each layer is 80% of the previous layer)
    :param raise_increase_at_order: The order from which the number of items starts to increase
    :param increase_count: The number of items to increase from the 3rd order onward
    :return: The number of elements at each layer
    """
    x = total_elements / sum([ratio**i for i in range(num_layers)])
    layers = [int(x * ratio**i) for i in range(num_layers)]
    
    total_calculated = sum(layers)
    
    if total_calculated < total_elements:
        remaining = total_elements - total_calculated
        layers[-1] += remaining
    return layers

def get_initial_idx(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            initial_idx = sum(1 for _ in f)
        return initial_idx
    except FileNotFoundError:
        print(f"File {file_path} not found. Returning initial index 0.")
        return 0
    except Exception as e:
        print(f"Error occurred while reading the file {file_path}: {e}")
        return 0


def generate_total_process(config_path, initial_operators_path, cython_cache_dir, num, max_workers, file_path, raise_increase_at_order=3, increase_count=3, ratio=0.6):
    start_time = time.time()
    global globals_dict
    globals_dict = initialize_globals(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        max_workers=max_workers
    )
    if is_file_empty(file_path):
        results = []
        for func_id, operator in globals_dict["op_manager"].operators.items():
            results.append(orjson.dumps(operator.to_dict()))
        
        with open(file_path, "a", encoding="utf-8") as f: 
            batch_write_to_file(results, f)
        
        globals_dict["logger"].debug("Initial operators saved by main process.")

    initial_idx = get_initial_idx(file_path)
        
    total_elements = num
    num_layers = 5  
    layers = calculate_layers_with_increase(total_elements, num_layers, ratio, raise_increase_at_order, increase_count)
    
    for i in range(min(5, len(layers))):
        layers[i] = max(layers[i] - 3, 0) 
    print(f"Number of items per layer after calculation: {layers}")
    order = 1  
    for i, layer in enumerate(layers):
        if layer != 0:
            if i >= (raise_increase_at_order - 1):
                generate_raise_order_operators(
                config_path=config_path,
                initial_operators_path=initial_operators_path,
                cython_cache_dir=cython_cache_dir,
                initial_idx = initial_idx,
                num=raise_increase_at_order,
                max_workers=max_workers,
                file_path=file_path,
                order=order
                )
                initial_idx = get_initial_idx(file_path)

            generate_randop(
            config_path=config_path,
            initial_operators_path=initial_operators_path,
            cython_cache_dir=cython_cache_dir,
            initial_idx = initial_idx,
            num=layer,
            max_workers=max_workers,
            file_path=file_path,
            order=order
            )
            initial_idx = get_initial_idx(file_path)
        
        order += 1
    end_time = time.time()
    logging.info(f"Generated all operators. Total time: {end_time - start_time:.2f}s")


def generate_total_process_continue(config_path, initial_operators_path, cython_cache_dir, num, max_workers, file_path, raise_increase_at_order=3, increase_count=3, ratio=0.6):
    start_time = time.time()
    global globals_dict
    
    globals_dict = initialize_globals(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        max_workers=max_workers
    )
    if is_file_empty(file_path):
        results = []
        for func_id, operator in globals_dict["op_manager"].operators.items():
            results.append(orjson.dumps(operator.to_dict()))
        
        with open(file_path, "a", encoding="utf-8") as f: 
            batch_write_to_file(results, f)
        
        globals_dict["logger"].debug("Initial operators saved by main process.")


    initial_idx = get_initial_idx(file_path)
    
    order_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    for func_id, operator in globals_dict["op_manager"].operators.items():
        if operator.n_order in order_count:
            order_count[operator.n_order] += 1

    print(f"Order counts: {order_count}")

        
    total_elements = num
    num_layers = 5  
    layers = calculate_layers_with_increase(total_elements, num_layers, ratio, raise_increase_at_order, increase_count)
    
    for i in range(min(5, len(layers))):
        layers[i] = max(layers[i] - order_count[i+1], 0)  

    print(f"Number of items per layer after calculation: {layers}")
    
    order = 1  

    for i, layer in enumerate(layers):
        if layer != 0:
            generate_randop(
            config_path=config_path,
            initial_operators_path=initial_operators_path,
            cython_cache_dir=cython_cache_dir,
            initial_idx = initial_idx,
            num=layer,
            max_workers=max_workers,
            file_path=file_path,
            order=order
            )
            initial_idx = get_initial_idx(file_path)
        
        order += 1
    end_time = time.time()
    logging.info(f"Generated all operators. Total time: {end_time - start_time:.2f}s")
    
if __name__ == "__main__":
    # Parse command-line arguments
 # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Initialize and run the operator manager with custom configuration paths.")
    parser.add_argument('--config', type=str, default='config/generate_operator.yaml', help='Path to the config file')
    parser.add_argument('--initial-operators-path', type=str, default="data/initial.jsonl", help='Path to the initial operator JSONL file')
    parser.add_argument('--generated-operators-path', type=str, default="data/final.jsonl", help='Path where the final results should be saved')
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')
    parser.add_argument('--num', type=int, default=10, help='Number of operators to generate')
    parser.add_argument('--max-workers', type=int, default=8, help='Maximum worker processes')
    parser.add_argument('--ratio', type=float, default=0.6, help='The ratio of each layer compared to the previous one')
    parser.add_argument('--raise-increase-at-order', type=int, default=3, help='The order at which to start increasing the number of operators')
    parser.add_argument('--increase-count', type=int, default=3, help='The number of operators to add after the raise-order')
    parser.add_argument('--continue-mode', type=bool, default=False, help='Whether to continue the generation process or not')

    # Parse arguments
    args = parser.parse_args()
    
    # Print debugging information
    print("==================================================")
    print("Starting the operator generation process...")
    print(f"Config Path: {args.config}")
    print(f"Initial Operators Path: {args.initial_operators_path}")
    print(f"Generated Operators Path: {args.generated_operators_path}")
    print(f"Cython Cache Directory: {args.cython_cache_dir}")
    # print(f"Mode to Generate: {args.mode}")
    print(f"Number of Operators to Generate: {args.num}")
    # print(f"Order of Operators to Generate: {args.n_order}")
    print(f"Maximum worker processes: {args.max_workers}")

    if args.continue_mode:
        generate_total_process_continue(
            config_path=args.config,
            initial_operators_path=args.initial_operators_path,
            cython_cache_dir=args.cython_cache_dir,
            num=args.num,
            max_workers=args.max_workers,
            file_path=args.generated_operators_path,
            raise_increase_at_order=args.raise_increase_at_order,
            increase_count=args.increase_count,
            ratio=args.ratio
        )
    else:
        generate_total_process(
            config_path=args.config,
            initial_operators_path=args.initial_operators_path,
            cython_cache_dir=args.cython_cache_dir,
            num=args.num,
            max_workers=args.max_workers,
            file_path=args.generated_operators_path,
            raise_increase_at_order=args.raise_increase_at_order,
            increase_count=args.increase_count,
            ratio=args.ratio
        )
