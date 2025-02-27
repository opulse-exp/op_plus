import argparse
from operatorplus import *
from expression.expression_generator import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')

if __name__ == "__main__":
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Generate operators based on given configuration.")
    parser.add_argument('--config', type=str, required=True, help='Path to the configuration file')
    parser.add_argument("--max_base", type=int, help="Maximum base value", default=None)
    parser.add_argument('--operator-file', type=str, required=True, help='Path to the input operator file')
    parser.add_argument('--output-file', type=str, required=True, help='Path to save the generated operators')
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')

    # Parse arguments
    args = parser.parse_args()

    # Load configuration and logging using command line arguments
    config = ParamConfig(args.config)  # Use the passed config path
    config.set('max_base', args.max_base)
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)

    # Initialize OperatorManager using the passed operator file path
    compiler = CythonCompiler(args.cython_cache_dir)
    op_manager = OperatorManager(args.operator_file, config, log, compiler, load_compile=False)

    # Initialize Generators
    condition_generator = ConditionGenerator(config, log, op_manager)
    expr_generator = ExpressionGenerator(config, log, op_manager)
    op_generator = OperatorGenerator(
        param_config=config, 
        logger=log, 
        condition_generator=condition_generator, 
        expr_generator=expr_generator,
        operator_manager=op_manager
    )

    # Generate base operators
    op_generator.generate_base_operators()

    results = []
    for func_id, operator in op_manager.operators.items():
        results.append(orjson.dumps(operator.to_dict()))
    
    with open(args.output_file, "a", encoding="utf-8") as f: 
        batch_write_to_file(results, f)
