#!/bin/bash
export PYTHONPATH=$(pwd)
# Set paths for the config, initial operators file, and output files
CONFIG_PATH="config/exp_configs/generate_expression_depth2.yaml"
OPERATORS_PATH="data/operator/operator_100.jsonl"
GENERATED_EXPRESSION_PATH="data/exps/combination"
GENERATED_OPEXPRESS_DEPENDENCY_PATH="data/exps/depth_2/op_expr.jsonl"
CYTHON_CACHE_DIR="./operator_funcs_so"

NUM=5
WORKERS=2

# Run the Python script to generate expressions
python generate_expression_multiprocess_base_n_depth_m.py \
    --config "$CONFIG_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --operators-path "$OPERATORS_PATH" \
    --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
    --generated-opexpr-dependency-path "$GENERATED_OPEXPRESS_DEPENDENCY_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --num "$NUM" \
    --workers "$WORKERS"


# CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/exp_configs/generate_expression_depth10.yaml"
# OPERATORS_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100/operator_100_with_base.jsonl"
# GENERATED_EXPRESSION_PATH="data/exps/depth_10/expressions.jsonl"
# GENERATED_OPEXPRESS_DEPENDENCY_PATH="data/exps/depth_10/op_expr.jsonl"
# export CYTHON_CACHE_DIR="opulse/_cyphon_cache"
# # Number of expressions and threads to use (can be adjusted as needed)
# NUM=100000
# WORKERS=256

# # Run the Python script to generate expressions
# python generate_expression_multiprocess.py \
#     --config "$CONFIG_PATH" \
#     --operators-path "$OPERATORS_PATH" \
#     --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
#     --generated-opexpr-dependency-path "$GENERATED_OPEXPRESS_DEPENDENCY_PATH" \
#     --num "$NUM" \
#     --workers "$WORKERS"

