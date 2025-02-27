#!/bin/bash

export PYTHONPATH=$(pwd)
#!/bin/bash

# 定义变量
CONFIG_PATH="config/generate_operator.yaml"
INITIAL_OPERATORS_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test/initial.jsonl"
GENERATED_OPERATORS_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100000_test/final.jsonl"
CYTHON_CACHE_DIR="./compiled_funcs"
NUM_OPERATORS=100000
MAX_WORKERS=24
RATIO=0.6
RAISE_INCREASE_AT_ORDER=3
INCREASE_COUNT=3

# 运行 Python 脚本并传递命令行参数
python generate_operator_multiprocess.py \
    --config "$CONFIG_PATH" \
    --initial-operators-path "$INITIAL_OPERATORS_PATH" \
    --generated-operators-path "$GENERATED_OPERATORS_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --num "$NUM_OPERATORS" \
    --max-workers "$MAX_WORKERS" \
    --ratio "$RATIO" \
    --raise-increase-at-order "$RAISE_INCREASE_AT_ORDER" \
    --increase-count "$INCREASE_COUNT"


# # !获取函数文件
# input_file="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/1_order/1_order_final.jsonl"
# op_compute_file="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/1_order/op_compute_fun.py"
# op_count_file="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/1_order/op_count_fun.py"
# python get_operator_func.py "$input_file" "$op_compute_file" "$op_count_file"

# CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/generate_operator.yaml"
# OPERATOR_FILE_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base.jsonl"
# OUTPUT_OPERATOR_FILE_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base_2.jsonl"

##TODO:赋优先级
# python assign_operator_priority.py \
#   --config "$CONFIG_PATH" \
#   --operator-file "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/5_order/5_order_final.jsonl" \
#   --output-operator-file "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/operator_500_no_base.jsonl"

##TODO:生成base运算符
# CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/generate_operator.yaml"
# OPERATOR_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators.jsonl"
# OUTPUT_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base.jsonl"

# python generate_base_operator.py \
#   --config "$CONFIG_PATH" \
#   --operator-file "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/operator_500_no_base.jsonl" \
#   --output-file "/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_500/operator_500_with_base.jsonl"