import concurrent.futures
import time
from typing import Dict, Any, List, Tuple
import os
import argparse
import logging
import traceback
from operatorplus import *
from generate_operator_type import initialize_globals, initialize_globals_continue, generate_operator_type

from load_operators import load_operators

from operatorplus.operator_manager import OperatorManager
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson
import random
# Global variables for worker processes
globals_dict = None
# def worker_init(config_path: str, initial_operators_path: str, cython_cache_dir: str, file_path: str):
#     """
#     Initializer for each worker process. Sets up global variables for expression generation.
#     """
#     global globals_dict

#     globals_dict = initialize_globals(config_path=config_path, initial_operators_path=initial_operators_path, cython_cache_dir=cython_cache_dir)

#     # #先把这里存进去
#     # globals_dict["op_manager"].save_operators_to_jsonl(file_path)
#     # globals_dict["logger"].debug("Worker process initialized successfully.")
#     # with open(file_path, "r", encoding="utf-8") as f:
#     #     lines_count = sum(1 for _ in f)  # 计算文件的行数
#     # global initial_idx
#     # initial_idx = lines_count  # 假设 global 变量存储行数

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
    # logger_global.info(f"Expression generated in {time_taken:.2f} seconds.")
    # Optionally, collect any logging messages or data if needed
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
    ) as executor, open(file_path, "a", encoding="utf-8") as f:  # 追加模式
        
        futures = [executor.submit(worker_generate_operator, op_type, order) for (op_type, order) in tasks]

        for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                operator, time_taken = future.result()
                operator.id = initial_idx + idx  # 确保唯一ID
               
                globals_dict["op_manager"].add_operator(operator) #这时候再加入manager
                results.append(orjson.dumps(operator.to_dict()))

                if len(results) >= batch_size or idx == len(tasks):
                    batch_write_to_file(results, f)
                    results.clear()
                    logging.info(f"Batch write completed up to operator {idx}")
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

    # 构建任务列表
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
    计算每一层的元素数目，使用比例递减的方法，并根据阶数递增生成条数。
    
    :param total_elements: 总元素数目
    :param num_layers: 层数
    :param ratio: 每层相对于上一层的递减比例 (例如，0.8 表示每层是上一层的 80%)
    :param raise_increase_at_order: 从第几阶开始增加生成条数
    :param increase_count: 从第3阶开始，增加多少条内容
    :return: 每一层的元素数量
    """
    # 计算每一层的元素数目
    x = total_elements / sum([ratio**i for i in range(num_layers)])
    layers = [int(x * ratio**i) for i in range(num_layers)]
    
    # 计算实际的总和
    total_calculated = sum(layers)
    
    # 如果总和不足，补充到目标总数
    if total_calculated < total_elements:
        # 计算剩余的元素数目
        remaining = total_elements - total_calculated
        # 将剩余元素添加到最后一层
        layers[-1] += remaining
    

    return layers

def get_initial_idx(file_path):
    """
    获取文件中的初始ID，文件为空时返回 0。
    
    :param file_path: 要读取的文件路径
    :return: 文件中的行数，作为初始ID
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            initial_idx = sum(1 for _ in f)
        return initial_idx
    except FileNotFoundError:
        # 如果文件不存在，返回 0
        print(f"File {file_path} not found. Returning initial index 0.")
        return 0
    except Exception as e:
        # 处理其他可能的异常
        print(f"Error occurred while reading the file {file_path}: {e}")
        return 0


def generate_total_process(config_path, initial_operators_path, cython_cache_dir, num, max_workers, file_path, raise_increase_at_order=3, increase_count=3, ratio=0.6):
    """
    综合生成流程，首先计算每个 order 下的元素数目，再从第3阶开始添加递增条数。
    """

    start_time = time.time()
    global globals_dict
    globals_dict = initialize_globals(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        max_workers=max_workers
    )
    # 判断文件是否为空
    if is_file_empty(file_path):
        results = []
        for func_id, operator in globals_dict["op_manager"].operators.items():
            results.append(orjson.dumps(operator.to_dict()))
        
        with open(file_path, "a", encoding="utf-8") as f: 
            batch_write_to_file(results, f)
        
        globals_dict["logger"].debug("Initial operators saved by main process.")

    # 获取初始ID

    initial_idx = get_initial_idx(file_path)
        
    total_elements = num
    num_layers = 5  # 假设有5个阶层
    layers = calculate_layers_with_increase(total_elements, num_layers, ratio, raise_increase_at_order, increase_count)
    
    for i in range(min(5, len(layers))):
        layers[i] = max(layers[i] - 3, 0)  # 确保不会减为负数

    print(f"计算后的每层内容数: {layers}")
    
    order = 1  # 初始阶数

    # 遍历每个阶层，根据计算的层数分配任务
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
    """
    综合生成流程，首先计算每个 order 下的元素数目，再从第3阶开始添加递增条数。
    """

    start_time = time.time()
    global globals_dict
    

    
    globals_dict = initialize_globals_continue(
        config_path=config_path,
        initial_operators_path=initial_operators_path,
        cython_cache_dir=cython_cache_dir,
        max_workers=max_workers
    )
    # 判断文件是否为空
    if is_file_empty(file_path):
        results = []
        for func_id, operator in globals_dict["op_manager"].operators.items():
            results.append(orjson.dumps(operator.to_dict()))
        
        with open(file_path, "a", encoding="utf-8") as f: 
            batch_write_to_file(results, f)
        
        globals_dict["logger"].debug("Initial operators saved by main process.")

    # 获取初始ID

    initial_idx = get_initial_idx(file_path)
    
    # 初始化字典来记录每个order的次数
    order_count = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # 遍历 binary_ops 列表，统计每个 order 的次数
    for func_id, operator in globals_dict["op_manager"].operators.items():
        if operator.n_order in order_count:
            order_count[operator.n_order] += 1

    # 打印结果
    print(f"Order counts: {order_count}")

        
    total_elements = num
    num_layers = 5  # 假设有5个阶层
    layers = calculate_layers_with_increase(total_elements, num_layers, ratio, raise_increase_at_order, increase_count)
    
    for i in range(min(5, len(layers))):
        layers[i] = max(layers[i] - order_count[i+1], 0)  # 确保不会减为负数

    print(f"计算后的每层内容数: {layers}")
    
    order = 1  # 初始阶数

    # 遍历每个阶层，根据计算的层数分配任务
    for i, layer in enumerate(layers):
        # if i >= (raise_increase_at_order - 1):
        #     generate_raise_order_operators(
        #     config_path=config_path,
        #     initial_operators_path=initial_operators_path,
        #     cython_cache_dir=cython_cache_dir,
        #     initial_idx = initial_idx,
        #     num=raise_increase_at_order,
        #     max_workers=max_workers,
        #     file_path=file_path,
        #     order=order
        #     )
        #     initial_idx = get_initial_idx(file_path)
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
    parser.add_argument('--initial-operators-path', type=str, default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/initial.jsonl", help='Path to the initial operator JSONL file')
    parser.add_argument('--generated-operators-path', type=str, default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final.jsonl", help='Path where the final results should be saved')
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')
    parser.add_argument('--num', type=int, default=100000, help='Number of operators to generate')
    parser.add_argument('--max-workers', type=int, default=8, help='Maximum worker processes')
    parser.add_argument('--ratio', type=float, default=0.6, help='The ratio of each layer compared to the previous one')
    parser.add_argument('--raise-increase-at-order', type=int, default=3, help='The order at which to start increasing the number of operators')
    parser.add_argument('--increase-count', type=int, default=3, help='The number of operators to add after the raise-order')
    
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

    
    # globals_dict = initialize_globals(
    #     config_path=args.config,
    #     initial_operators_path=args.initial_operators_path,
    #     cython_cache_dir=args.cython_cache_dir
    # )
    
    # # operator = generate_operator_type(globals_dict, "recursive_definition", args.n_order)
    
    # if args.mode == 'raise':
    #     generate_raise_order_operators(
    #         config_path=args.config,
    #         initial_operators_path=args.initial_operators_path,
    #         cython_cache_dir=args.cython_cache_dir,
    #         num=args.num,
    #         max_workers=args.max_workers,
    #         file_path=args.generated_operators_path,
    #         order=args.n_order
    #     )
    # else:
    #     generate_randop(
    #         config_path=args.config,
    #         initial_operators_path=args.initial_operators_path,
    #         cython_cache_dir=args.cython_cache_dir,
    #         num=args.num,
    #         max_workers=args.max_workers,
    #         file_path=args.generated_operators_path,
    #         order=args.n_order
    #     )
    

        
     # 调用新的总流程函数
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