import concurrent.futures
import time
import json
import argparse

from operatorplus import *
from expression import ExpressionGenerator
from config import LogConfig, ParamConfig
import orjson

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
    op_manager = OperatorManager(operators_path, config, log, compiler, False)

    expression_generator = ExpressionGenerator(
        config, log, operator_manager=op_manager
    )

    return {
        "config": config,
        "logger": logger,
        "op_manager": op_manager,
        "exp_generator": expression_generator
    }


   
def worker_generate_expression():

    # 生成表达式
    start_time = time.time()
    properties = globals_dict["exp_generator"].create_expression("number")
    end_time = time.time()

    return properties, end_time - start_time

def batch_write_to_file(batch, f):
    """write a batchc of items to a file"""
    for item in batch:
        f.write(item.decode('utf-8') + '\n')


def generate_expressions_multiprocess(
    file_path: str,
    num: int,
    max_workers: int
):
    """
    使用多进程生成表达式，并将结果写入文件。
    """
    start_time = time.time()

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
        default="data/exps/expr_test.jsonl",
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
    global globals_dict
    globals_dict = initialize(args.config, args.operators_path, args.cython_cache_dir)

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
    generate_expressions_multiprocess(
        file_path=args.generated_expression_path,
        num=args.num,
        max_workers=args.workers
    )

    print("Expression generation completed.")
    
