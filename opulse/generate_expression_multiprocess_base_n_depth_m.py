# import concurrent.futures
# import json
# import time
# from typing import Dict, Any, cast
# import argparse
# import logging
# import traceback

# from operatorplus.operator_manager import OperatorManager
# from expression import ExpressionGenerator
# from config import LogConfig, ParamConfig
# from operatorplus.compiler import CythonCompiler
# import orjson

# # Global variables for worker processes
# expression_generator_global = None
# logger_global = None

# def worker_init(config_path: str, operators_path: str, cython_cache_dir: str, base: int, depth: int):
#     """
#     Initializer for each worker process. Sets up global variables for expression generation.
#     """
#     global expression_generator_global
#     global logger_global

#     # Load configuration
#     config = ParamConfig(config_path)
#     logging_config = config.get_logging_config()
#     log_config = LogConfig(logging_config)
#     logger = log_config.get_logger()
#     logger_global = logger
#     compiler = CythonCompiler(cython_cache_dir)

#     # set base and depth
#     config.config["random_base"]["base"]=base
#     config.config["result_base"]["base"]=base
#     config.config["longer_result_compute"]["base"]=base
#     config.config["expr_max_depth"]=depth

#     # Initialize Operator Manager
#     op_manager = OperatorManager(operators_path, config, log_config, compiler)

#     # Initialize Expression Generator
#     expression_generator_global = ExpressionGenerator(
#         param_config=config, logger=log_config, operator_manager=op_manager
#     )
#     # expression_generator_global.set_random_base(random_flag=False, target_base=10)

#     logger.debug("Worker process initialized successfully.")

# def worker_generate_expression():
#     """
#     Worker function to generate a single expression.
#     Returns the generated properties and the time taken.
#     """
#     global expression_generator_global
#     global logger_global

#     start_time_expr = time.time()

#     # Generate expression
#     properties = expression_generator_global.create_expression("number")

#     end_time_expr = time.time()
#     time_taken = end_time_expr - start_time_expr
#     # logger_global.info(f"Expression generated in {time_taken:.2f} seconds.")
#     # Optionally, collect any logging messages or data if needed
#     return properties, time_taken

# def batch_write_to_file(batch, f):
#     """write a batchc of items to a file"""
#     for item in batch:
#         f.write(item.decode('utf-8') + '\n')

# def generate_expressions_multiprocess(
#     config_path: str,
#     operators_path: str,
#     num: int,
#     max_workers: int,
#     file_path: str,
#     dependency_path: str,
#     cython_cache_dir: str,
#     base: int,
#     depth: int,
# ):
#     """
#     Generates expressions using multiple processes and writes them to a file.
#     """
#     start_time = time.time()

#     # Initialize the operator manager and expression generator in the main process if needed
#     # (Here, it's handled within worker processes)
#     results = []
#     batch_size = 1000
#     with concurrent.futures.ProcessPoolExecutor(
#         max_workers=max_workers,
#         initializer=worker_init,
#         initargs=(config_path, operators_path, cython_cache_dir, base, depth),
#     ) as executor, open(file_path, "w", encoding="utf-8") as f:
#         # Submit all tasks to the executor
#         futures = [executor.submit(worker_generate_expression) for _ in range(num)]

#         # Iterate over completed futures as they finish
#         for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
#             try:
#                 properties, time_taken = future.result()
#                 # properties, time_taken = future.result()
#                 properties['id'] = idx  # 分配唯一 ID
#                 results.append(orjson.dumps(properties))

#                 if len(results) >= batch_size or idx == num:
#                     batch_write_to_file(results, f)
#                     results.clear()
#                     logging.info(f"Batch write completed up to expression {idx}")
#             # except concurrent.futures.TimeoutError:
#             #     logging.info(f"Task {idx} timed out and will be resubmitted.")
#             #     # Resubmit the failed task
#             #     new_future = executor.submit(worker_generate_expression)
#             #     futures.append(new_future)  # Append it so we can wait for its completion too
#             #     completed_futures = concurrent.futures.as_completed(futures)  # Update generator
#             except Exception as e:
#                 print(f"Error in task {idx}:\n{traceback.format_exc()}")
#                 logging.error(f"Error generating expression {idx}: {e}")
                

#     # After generating all expressions, handle dependency dumping if necessary
#     # Since expression_generator_global is not accessible here, you might need to handle this differently
#     # For example, if dump_op2expr needs to be called, consider aggregating necessary data
#     # Alternatively, you can have a separate step for dependency handling

#     end_time = time.time()
#     # print(f"Generating {num} expressions. Time taken: {end_time - start_time:.2f} seconds.")
#     logging.info(f"Generating {num} expressions. Time taken: {end_time - start_time:.2f} seconds.")

# def initialize_logging():
#     """
#     Initializes the logging configuration for the main process.
#     """
#     logging.basicConfig(
#         level=logging.DEBUG,
#         format='%(asctime)s [%(levelname)s] %(message)s',
#         handlers=[
#             logging.StreamHandler()
#         ]
#     )

# if __name__ == "__main__":
#     # Initialize logging for the main process
#     initialize_logging()
#     logger = logging.getLogger()

#     # Parse command-line arguments
#     parser = argparse.ArgumentParser(
#         description="Initialize and run the operator manager with custom configuration paths."
#     )
#     parser.add_argument(
#         "--config",
#         type=str,
#         default="config/generate_expression.yaml",
#         help="Path to the config file",
#     )
#     parser.add_argument(
#         "--operators-path",
#         type=str,
#         default="data/operator_100/operator_100_with_base.jsonl",
#         help="Path to the initial operator JSONL file",
#     )
#     parser.add_argument(
#         "--generated-expression-path",
#         type=str,
#         default="data/expression/generated_expression.jsonl",
#         help="Path where the final results should be saved",
#     )
#     parser.add_argument(
#         "--generated-opexpr-dependency-path",
#         type=str,
#         default="data/dependency/op_expression.jsonl",
#         help="Path where the final dependency results should be saved",
#     )
#     parser.add_argument(
#         "--num", type=int, default=10000, help="Number of expressions to generate"
#     )
#     parser.add_argument(
#         "--workers", type=int, default=4, help="Number of worker processes to generate"
#     )
#     parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')

#     # Parse arguments
#     args = parser.parse_args()

#     # Print debugging information
#     print("==================================================")
#     print("Starting the expression generation process...")
#     print(f"Config Path: {args.config}")
#     print(f"Initial Operators Path: {args.operators_path}")
#     print(f"Generated Expression Path: {args.generated_expression_path}")
#     print(f"Number of Expressions to Generate: {args.num}")
#     print(f"Number of Worker Processes: {args.workers}")
#     print(f"Path to the Cython cache directory: {args.cython_cache_dir}")
#     print("==================================================")

#     depth_list = [2,4,6,8,10]
#     for base in range(2,17):
#         for depth in depth_list:
#             # Generate the expressions using multiprocessing
#             generate_expressions_multiprocess(
#                 config_path=args.config,
#                 operators_path=args.operators_path,
#                 num=args.num,
#                 max_workers=args.workers,
#                 file_path=f"data/exps/all_depth_base/expressions_base{base}_depth{depth}.jsonl",
#                 dependency_path=args.generated_opexpr_dependency_path,
#                 cython_cache_dir=args.cython_cache_dir,
#                 base=base,
#                 depth=depth,
#             )

#     # Handle dependency dumping if necessary
#     # This part depends on how dump_op2expr is implemented and whether it needs to be called in the main process
#     # If dump_op2expr needs access to the expression generator, consider refactoring it to aggregate data from workers

#     logger.debug("Expression generation process completed.")


import concurrent.futures
import time
import json
import argparse

from operatorplus import *
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson
import os

# 全局变量，用于在子进程中引用共享对象
global_dict = None


def initialize(config_path: str, operators_path: str, cython_cache_dir: str):
    """
    初始化共享对象，包括配置、日志、以及 OperatorManager。
    使用 multiprocessing.Manager 创建共享字典。
    """
    config = ParamConfig(config_path)
    log = LogConfig(config.get_logging_config())
    logger = log.get_logger()

    # 创建 OperatorManager
    compiler = CythonCompiler(cython_cache_dir)
    op_manager = OperatorManager(operators_path, config, log, cython_cache_dir, compiler, True)

    expression_generator = ExpressionGenerator(
        config, log, cython_cache_dir, operator_manager=op_manager
    )

    return {
        "config": config,
        'log': log,
        "logger": logger,
        "op_manager": op_manager,
        "exp_generator": expression_generator
    }


   
def worker_generate_expression():

    # 生成表达式
    start_time = time.time()
    properties = global_dict["exp_generator"].create_expression("number")
    end_time = time.time()

    return properties, end_time - start_time

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')


def generate_expressions_multiprocess_base_depth(
    file_path: str,
    cython_cache_dir: str,
    num: int,
    max_workers: int,
    base: int,
    depth: int,
):
    """
    使用多进程生成表达式，并将结果写入文件。
    """
    start_time = time.time()
    global global_dict
    # select target base
    global_dict['config'].config["random_base"]["base"]=base
    global_dict['config'].config["result_base"]["base"]=base
    global_dict['config'].config["longer_result_compute"]["base"]=base
    global_dict['config'].config["expr_max_depth"]=depth

    global_dict['exp_generator']=ExpressionGenerator(
        global_dict['config'], global_dict['log'],  cython_cache_dir, operator_manager= global_dict['op_manager']
    )

    # 打开目标文件
    with open(file_path, "w", encoding="utf-8") as f, concurrent.futures.ProcessPoolExecutor(
        max_workers=max_workers,
    ) as executor:
        # 提交任务到进程池
        futures = [executor.submit(worker_generate_expression) for _ in range(num)]
        
        results = []
        batch_size = 1000
        # 处理任务结果
        for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                properties, time_taken = future.result()  # 获取子进程返回结果
                properties['id'] = idx  # 为每个表达式分配唯一 ID
                results.append(orjson.dumps(properties))

                if len(results) >= batch_size or idx == num:
                    batch_write_to_file(results, f)
                    results.clear()
                    print(f"Batch write completed up to expression {idx}")
            except Exception as e:
                print(f"Error generating expression {idx}: {e}")

    end_time = time.time()
    print(f"Generated {num} expressions in {end_time - start_time:.2f}s")


if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="Generate expressions using multiprocessing.")
    parser.add_argument(
        "--config",
        type=str,
        default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/exp_configs/generate_expression_depth2.yaml",
        help="Path to the config file",
    )
    parser.add_argument('--cython-cache-dir', type=str, default="./operator_funcs_so", help='Path to the Cython cache directory')
    
    parser.add_argument(
        "--operators-path",
        type=str,
        default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100_test/final_base.jsonl",
        help="Path to the initial operator JSONL file",
    )
    parser.add_argument(
        "--generated-expression-path",
        type=str,
        default="data/exps/combination",
        help="Path where the final results should be saved",
    )
    parser.add_argument(
        "--generated-opexpr-dependency-path",
        type=str,
        default="data/exps/depth_2/op_expr.jsonl",
        help="Path where the final results should be saved",
    )
    parser.add_argument(
        "--num", type=int, default=100, help="Number of expressions to generate"
    )
    parser.add_argument(
        "--workers", type=int, default=8, help="Number of worker processes"
    )

    args = parser.parse_args()

    # 初始化共享对象
    global_dict = initialize(args.config, args.operators_path, args.cython_cache_dir)

    # 打印信息
    print("==================================================")
    print("Starting expression generation process...")
    print(f"Config Path: {args.config}")
    print(f"Operators Path: {args.operators_path}")
    print(f"Output Path: {args.generated_expression_path}")
    print(f"Number of Expressions: {args.num}")
    print(f"Number of Workers: {args.workers}")
    print("==================================================")

    # 使用多进程生成表达式
    depth_list = [2,4,6,8,10]
    for base in range(2,17):
        for depth in depth_list:
            generate_expressions_multiprocess_base_depth(
                file_path=os.path.join(args.generated_expression_path,f"base{base}_depth{depth}.jsonl"),
                cython_cache_dir = args.cython_cache_dir,
                num=args.num,
                max_workers=args.workers,
                base=base,
                depth=depth,
            )

    print("Expression generation completed.")