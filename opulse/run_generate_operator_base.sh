#!/bin/bash
export PYTHONPATH=$(pwd)

# 定义变量
CONFIG_PATH="config/generate_operator.yaml"
INITIAL_OPERATORS_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/final_symbol_final.jsonl"
GENERATED_OPERATORS_PATH_1="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/operator_100000_1.jsonl"
GENERATED_OPERATORS_PATH_2="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test_2/operator_100000_with_base.jsonl"
CYTHON_CACHE_DIR="./compiled_funcs"

# 运行 Python 脚本并传递命令行参数
##TODO:赋优先级
python assign_operator_priority.py \
  --config "$CONFIG_PATH" \
  --operator-file "$INITIAL_OPERATORS_PATH" \
  --output-operator-file "$GENERATED_OPERATORS_PATH_1" \
  --cython-cache-dir "$CYTHON_CACHE_DIR" 

##TODO:生成base运算符
python generate_base_operator.py \
  --config "$CONFIG_PATH" \
  --max_base 16 \
  --operator-file "$GENERATED_OPERATORS_PATH_1" \
  --output-file "$GENERATED_OPERATORS_PATH_2" \
  --cython-cache-dir "$CYTHON_CACHE_DIR" 


