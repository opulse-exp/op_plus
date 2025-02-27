#!/bin/bash
export PYTHONPATH=$(pwd)
# Set paths for the config, initial operators file, and output files
CONFIG_PATH="config/exp_configs/generate_expression_depth1.yaml"
OPERATORS_PATH="data/operator/operator_100.jsonl"
GENERATED_EXPRESSION_PATH="data/exps/single_op"
GENERATED_OPEXPRESS_DEPENDENCY_PATH="data/exps/depth_2/op_expr.jsonl"
CYTHON_CACHE_DIR="./operator_funcs_so"
# Number of expressions and threads to use (can be adjusted as needed)
NUM=10
WORKERS=2

# Run the Python script to generate expressions
python generate_expression_singleop_base_n_multiprocess.py \
    --config "$CONFIG_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --operators-path "$OPERATORS_PATH" \
    --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
    --generated-opexpr-dependency-path "$GENERATED_OPEXPRESS_DEPENDENCY_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --num "$NUM" \
    --workers "$WORKERS"




