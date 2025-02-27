import concurrent.futures
import json
import time
from typing import Dict, Any, cast
import argparse
import logging
import traceback

from operatorplus.operator_manager import OperatorManager
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson
import os
# Global variables for worker processes
expression_generator_global = None
logger_global = None

def worker_init(config_path: str, operators_path: str):
    """
    Initializer for each worker process. Sets up global variables for expression generation.
    """
    global expression_generator_global
    global logger_global

    # Load configuration
    config = ParamConfig(config_path)
    logging_config = config.get_logging_config()
    log_config = LogConfig(logging_config)
    logger = log_config.get_logger()
    logger_global = logger

    # Initialize Operator Manager
    op_manager = OperatorManager(operators_path, config, log_config)

    # Initialize Expression Generator
    expression_generator_global = ExpressionGenerator(
        param_config=config, logger=log_config, operator_manager=op_manager
    )
    # expression_generator_global.set_random_base(random_flag=False, target_base=10)

    logger.debug("Worker process initialized successfully.")

def worker_generate_expression():
    """
    Worker function to generate a single expression.
    Returns the generated properties and the time taken.
    """
    global expression_generator_global
    global logger_global

    start_time_expr = time.time()

    # Generate expression
    properties_list = expression_generator_global.create_single_operator_expression(1)

    end_time_expr = time.time()
    time_taken = end_time_expr - start_time_expr
    # logger_global.info(f"Expression generated in {time_taken:.2f} seconds.")
    # Optionally, collect any logging messages or data if needed
    return properties_list, time_taken

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')

def generate_expressions_multiprocess(
    config_path: str,
    operators_path: str,
    num: int,
    max_workers: int,
    file_path: str,
    dependency_path: str,
):
    """
    Generates expressions using multiple processes and writes them to a file.
    """
    start_time = time.time()

    # Initialize the operator manager and expression generator in the main process if needed
    # (Here, it's handled within worker processes)
    results = []
    batch_size = 1000
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=max_workers,
        initializer=worker_init,
        initargs=(config_path, operators_path),
    ) as executor, open(file_path, "w", encoding="utf-8") as f:
        # Submit all tasks to the executor
        futures = [executor.submit(worker_generate_expression) for _ in range(num)]

        # Iterate over completed futures as they finish
        expr_idx=0
        for batch_idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                properties_list, time_taken = future.result()
                # properties, time_taken = future.result()
                for properties in properties_list:
                    properties['id'] = expr_idx  # 分配唯一 ID
                    expr_idx += 1
                    results.append(orjson.dumps(properties))

                if len(results) >= batch_size or batch_idx == num:
                    batch_write_to_file(results, f)
                    results.clear()
                    logging.info(f"Batch write completed up to expression {expr_idx}")
            # except concurrent.futures.TimeoutError:
            #     logging.info(f"Task {idx} timed out and will be resubmitted.")
            #     # Resubmit the failed task
            #     new_future = executor.submit(worker_generate_expression)
            #     futures.append(new_future)  # Append it so we can wait for its completion too
            #     completed_futures = concurrent.futures.as_completed(futures)  # Update generator
            except Exception as e:
                print(f"Error in task {batch_idx}:\n{traceback.format_exc()}")
                logging.error(f"Error generating expression {batch_idx}: {e}")
                

    # After generating all expressions, handle dependency dumping if necessary
    # Since expression_generator_global is not accessible here, you might need to handle this differently
    # For example, if dump_op2expr needs to be called, consider aggregating necessary data
    # Alternatively, you can have a separate step for dependency handling

    end_time = time.time()
    # print(f"Generating {num} expressions. Time taken: {end_time - start_time:.2f} seconds.")
    logging.info(f"Generating {num} expressions. Time taken: {end_time - start_time:.2f} seconds.")

def initialize_logging():
    """
    Initializes the logging configuration for the main process.
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    # Initialize logging for the main process
    # initialize_logging()
    # logger = logging.getLogger()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Initialize and run the operator manager with custom configuration paths."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/generate_expression.yaml",
        help="Path to the config file",
    )
    parser.add_argument(
        "--operators-path",
        type=str,
        default="data/operator_100/operator_100_with_base.jsonl",
        help="Path to the initial operator JSONL file",
    )
    parser.add_argument(
        "--generated-expression-path",
        type=str,
        default="data/expression/generated_expression.jsonl",
        help="Path where the final results should be saved",
    )
    parser.add_argument(
        "--generated-opexpr-dependency-path",
        type=str,
        default="data/dependency/op_expression.jsonl",
        help="Path where the final dependency results should be saved",
    )
    parser.add_argument(
        "--num", type=int, default=10000, help="Number of expressions to generate"
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker processes to generate"
    )

    # Parse arguments
    args = parser.parse_args()

    # Print debugging information
    print("==================================================")
    print("Starting the expression generation process...")
    print(f"Config Path: {args.config}")
    print(f"Initial Operators Path: {args.operators_path}")
    print(f"Generated Expression Path: {args.generated_expression_path}")
    print(f"Number of Expressions to Generate: {args.num}")
    print(f"Number of Worker Processes: {args.workers}")
    print("==================================================")



    # Generate the expressions using multiprocessing
    generate_expressions_multiprocess(
        config_path=args.config,
        operators_path=args.operators_path,
        num=args.num,
        max_workers=args.workers,
        file_path=args.generated_expression_path,
        dependency_path=args.generated_opexpr_dependency_path,
    )

    # Handle dependency dumping if necessary
    # This part depends on how dump_op2expr is implemented and whether it needs to be called in the main process
    # If dump_op2expr needs access to the expression generator, consider refactoring it to aggregate data from workers

    # logger.debug("Expression generation process completed.")
