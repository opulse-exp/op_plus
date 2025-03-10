from multiprocessing import Pool, Manager, Queue
import time
import orjson
import os
import argparse
from operatorplus import *
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig

global logger

def extract_func_ids(operators_path):
    func_ids = []
    with open(operators_path, "rb") as f:
        for line in f:
            try:
                data = orjson.loads(line.strip())
                if "func_id" in data and data["is_base"] is None:
                    func_ids.append(data["func_id"])
            except orjson.JSONDecodeError as e:
                print(f"Error decoding JSON on line: {line.decode('utf-8', errors='ignore')}. Error: {e}")

    return func_ids

def initialize(config_path: str, operators_path: str, cython_cache_dir: str):
    config = ParamConfig(config_path)
    log = LogConfig(config.get_logging_config())
    global logger
    logger = log.get_logger()

    compiler = CythonCompiler(cython_cache_dir)
    op_manager = OperatorManager(operators_path, config, log, cython_cache_dir, compiler, True)
    
    expression_generator = ExpressionGenerator(
        config, log, cython_cache_dir, operator_manager=op_manager
    )
    
    return {
        "config": config,
        "log": log,
        "logger": logger,
        "op_manager": op_manager,
        "exp_generator": expression_generator
    }

def init_worker(global_dict):
    global exp_generator_global
    exp_generator_global = global_dict["exp_generator"]  

def worker_generate_expression(result_queue):
    start_time = time.time()
    properties = exp_generator_global.create_expression("number")
    end_time = time.time()
    result_queue.put((properties, end_time - start_time))  # 通过队列传递结果
    
def read_existing_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for line in f)
    except FileNotFoundError:
        return 0

def batch_write_to_file(batch, f):
    for item in batch:
        f.write(item.decode('utf-8') + '\n')

def generate_expressions_multiprocess_base_depth(
    file_path: str,
    cython_cache_dir: str,
    global_dict: dict,
    num: int,
    max_workers: int,
    base: int,
    depth: int,
):
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        
    existing_lines = read_existing_lines(file_path)
    if existing_lines >= num:
        print(f"{file_path} has generated enough expressions, skipping.")
        return
    
    remaining = num - existing_lines
    print(f"Need to generate {remaining} more expressions...")

    global_dict['config'].config["random_base"]["base"] = base
    global_dict['config'].config["result_base"]["base"] = base
    global_dict['config'].config["longer_result_compute"]["base"] = base
    global_dict['config'].config["expr_max_depth"] = depth
    
    global_dict['exp_generator'] = ExpressionGenerator(
        global_dict['config'], global_dict['log'], cython_cache_dir, operator_manager=global_dict['op_manager']
    )

    with open(file_path, "a", encoding="utf-8") as f:
        with Manager() as manager:
            result_queue = manager.Queue()
            
            start_time = time.time()
            with Pool(processes=max_workers, initializer=init_worker, initargs=(global_dict,)) as pool:
                # Corrected starmap call with proper arguments
                pool.starmap(worker_generate_expression, [(result_queue,) for _ in range(remaining)])

            batch_size = 1000
            batch = []
            idx = existing_lines + 1

            while not result_queue.empty():
                properties, time_taken = result_queue.get()
                try:
                    properties['id'] = idx
                    batch.append(orjson.dumps(properties))
                    
                    if len(batch) >= batch_size or idx == num:
                        batch_write_to_file(batch, f)
                        batch.clear()
                        print(f"Batch write completed up to expression {idx}")
                        print(f"Batch Generate expressions cost {time_taken:.2f}s")
                    
                    idx += 1
                except Exception as e:
                    print(f"Error generating expression {idx}: {e}")

            end_time = time.time()
            print(f"Generated {num} expressions in {end_time - start_time:.2f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate expressions using multiprocessing.")
    parser.add_argument(
        "--config",
        type=str,
        default="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/exp_configs/generate_expression_depth2.yaml",
        help="Path to the config file",
    )
    parser.add_argument('--cython-cache-dir', type=str, default="./compiled_funcs", help='Path to the Cython cache directory')
    
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
        "--num", type=int, default=1, help="Number of expressions to generate"
    )
    parser.add_argument(
        "--workers", type=int, default=8, help="Number of worker processes"
    )
    parser.add_argument(
        "--base", type=int, default=10, help="Numerical base for expression generation"
    )
    parser.add_argument(
        "--depth", type=int, default=2, help="Depth of expressions to generate"
    )
    
    args = parser.parse_args()

    global_dict = initialize(args.config, args.operators_path, args.cython_cache_dir)

    print("==================================================")
    print("Starting expression generation process...")
    print(f"Config Path: {args.config}")
    print(f"Operators Path: {args.operators_path}")
    print(f"Output Path: {args.generated_expression_path}")
    print(f"Number of Expressions: {args.num}")
    print(f"Number of Workers: {args.workers}")
    print(f"Base: {args.base}")
    print(f"Depth: {args.depth}")
    print("==================================================")

    generate_expressions_multiprocess_base_depth(
        file_path=os.path.join(args.generated_expression_path,f"base{args.base}_depth{args.depth}.jsonl"),
        cython_cache_dir = args.cython_cache_dir,
        global_dict = global_dict,
        num=args.num,
        max_workers=args.workers,
        base=args.base,
        depth=args.depth,
    )
    print(f"Expression generation for base {args.base}, depth {args.depth} completed.")
