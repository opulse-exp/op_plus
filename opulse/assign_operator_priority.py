import argparse
import logging
from operatorplus import *
from expression.expression_generator import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')
        
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate and assign priorities to operators.")
    
    parser.add_argument('--config', type=str, required=True, help="Path to the config file")
    parser.add_argument('--operator-file', type=str, required=True, help="Path to the operator input JSONL file")
    parser.add_argument('--output-operator-file', type=str, required=True, help="Path to save the generated operators")
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')
    
    args = parser.parse_args()
    
    # Load config
    config = ParamConfig(args.config)
    
    # Setup logging
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    
    # Initialize OperatorManager
    compiler = CythonCompiler(args.cython_cache_dir)
    op_manager = OperatorManager(args.operator_file, config, log, compiler, load_compile=False)
    
    # Initialize OperatorPriorityManager and assign priorities
    op_priority_manager = OperatorPriorityManager(log, op_manager)
    op_priority_manager.assign_priorities()

    
    results = []
    for func_id, operator in op_manager.operators.items():
        results.append(orjson.dumps(operator.to_dict()))
    
    with open(args.output_operator_file, "a", encoding="utf-8") as f: 
        batch_write_to_file(results, f)

    # # Save the operators to the specified output file
    # op_manager.save_operators_to_jsonl(args.output_operator_file)
