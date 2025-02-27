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
from operatorplus.compiler import CythonCompiler
import orjson

# Global variables for worker processes
expression_generator_global = None
logger_global = None



def worker_init(config_path: str, operators_path: str, cython_cache_dir: str):
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
    compiler = CythonCompiler(cython_cache_dir)

    # Initialize Operator Manager
    op_manager = OperatorManager(operators_path, config, log_config,compiler=compiler)

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
    properties = expression_generator_global.create_expression("number")

    end_time_expr = time.time()
    time_taken = end_time_expr - start_time_expr
    # logger_global.info(f"Expression generated in {time_taken:.2f} seconds.")
    # Optionally, collect any logging messages or data if needed
    return properties, time_taken

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
    cython_cache_dir: str,
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
        initargs=(config_path, operators_path, cython_cache_dir),
    ) as executor, open(file_path, "w", encoding="utf-8") as f:
        # Submit all tasks to the executor
        futures = [executor.submit(worker_generate_expression) for _ in range(num)]

        # Iterate over completed futures as they finish
        for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                properties, time_taken = future.result()
                # properties, time_taken = future.result()
                properties['id'] = idx  # 分配唯一 ID
                results.append(orjson.dumps(properties))

                if len(results) >= batch_size or idx == num:
                    batch_write_to_file(results, f)
                    results.clear()
                    logging.info(f"Batch write completed up to expression {idx}")
            # except concurrent.futures.TimeoutError:
            #     logging.info(f"Task {idx} timed out and will be resubmitted.")
            #     # Resubmit the failed task
            #     new_future = executor.submit(worker_generate_expression)
            #     futures.append(new_future)  # Append it so we can wait for its completion too
            #     completed_futures = concurrent.futures.as_completed(futures)  # Update generator
            except Exception as e:
                print(f"Error in task {idx}:\n{traceback.format_exc()}")
                logging.error(f"Error generating expression {idx}: {e}")
                

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
    # global config
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
if __name__ == "__main__":
    # Initialize logging for the main process
    initialize_logging()
    logger = logging.getLogger()

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
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')

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
    print(f"Path to the Cython cache directory: {args.cython_cache_dir}")
    print("==================================================")



    # Generate the expressions using multiprocessing
    generate_expressions_multiprocess(
        config_path=args.config,
        operators_path=args.operators_path,
        num=args.num,
        max_workers=args.workers,
        file_path=args.generated_expression_path,
        dependency_path=args.generated_opexpr_dependency_path,
        cython_cache_dir=args.cython_cache_dir,
    )

    # Handle dependency dumping if necessary
    # This part depends on how dump_op2expr is implemented and whether it needs to be called in the main process
    # If dump_op2expr needs access to the expression generator, consider refactoring it to aggregate data from workers

    logger.debug("Expression generation process completed.")
