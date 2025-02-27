import argparse
from operatorplus.operator_manager import OperatorManager
from expression import ExpressionGenerator
from operatorplus.operator_priority_manager import OperatorPriorityManager
from config import LogConfig, ParamConfig
from typing import Dict, Any
import time
import json
from typing import cast
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

def run_with_timeout(func, args=(), kwargs={}, timeout=10):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        result = func(*args, **kwargs)
    except TimeoutException:
        print(f"Function {func.__name__} timed out after {timeout} seconds")
        result = None
    finally:
        signal.alarm(0)
    return result

def initialize_globals(config_path: str, operators_path: str):
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
    config = ParamConfig(config_path)
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    logger = log.get_logger()
    # Initialize Operator Manager
    op_manager = OperatorManager(operators_path, config, log)
    # if len(op_manager.operators)!=0 :
    #     logger.info("Operator priority is None, assign priority")
    #     op_priority_manager=OperatorPriorityManager(logger=log,operator_manager=op_manager)
    #     op_priority_manager.assign_priorities()
    # Initialize Generators
    expression_generator = ExpressionGenerator(
        param_config=config, logger=log, operator_manager=op_manager
    )
    # Debug logging
    logger.debug("Global variables initialized successfully.")

    return {
        "config": config,
        "log": log,
        "logger": logger,
        "op_manager": op_manager,
        "expression_generator": expression_generator,
    }


def generate_randexpr(
    globals_dict: Dict[str, Any], file_path: str, dependency_path: str, num: int
):
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

    start_time = time.time()
    with open(file_path, "w", encoding="utf-8") as f:
        globals_dict["expression_generator"] = cast(
            ExpressionGenerator, globals_dict["expression_generator"]
        )
        globals_dict["expression_generator"].set_random_base(
            random_flag=False, target_base=10
        )
        for i in range(num):
            start_time_expr = time.time()
            properties = globals_dict["expression_generator"].create_expression(
                "number"
            )
            json.dump(properties, f, ensure_ascii=False)
            f.write("\n")
            end_time_expr = time.time()
            globals_dict["logger"].debug(
                f"Generating expression: using {end_time_expr - start_time_expr}s",
            )
    globals_dict["expression_generator"].dump_op2expr(dependency_path)
    end_time = time.time()

    globals_dict["logger"].debug(
        f"Generating {num} expressions. Time taken: {end_time - start_time} seconds."
    )


if __name__ == "__main__":
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
        help="Path where the final results should be saved",
    )
    parser.add_argument(
        "--num", type=int, default=1000, help="Number of expressions to generate"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of thread to generate"
    )

    # Parse arguments
    args = parser.parse_args()

    # Print debugging information
    print("==================================================")
    print("Starting the expression generation process...")
    print(f"Config Path: {args.config}")
    print(f"Initial Expression Path: {args.operators_path}")
    print(f"Generated Expression Path: {args.generated_expression_path}")
    print(f"Number of Expression to Generate: {args.num}")

    # Initialize global objects
    globals_dict = initialize_globals(
        config_path=args.config, operators_path=args.operators_path
    )

    # Generate the operators
    generate_randexpr(
        globals_dict,
        args.generated_expression_path,
        args.generated_opexpr_dependency_path,
        args.num,
    )
