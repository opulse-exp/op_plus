#!/bin/bash

export PYTHONPATH=$(pwd)
# Set paths for the config, initial operators file, and output files
export CONFIG_PATH="config/exp_configs/generate_expression_depth2.yaml"
export OPERATORS_PATH="/map-vepfs/kaijing/op_plus/opulse/data/operator/operator_100000.jsonl" 
export GENERATED_EXPRESSION_PATH="data/exps/singleop"
export CYTHON_CACHE_DIR="./compiled_funcs"

export NUM=10000
export WORKERS=20

python generate_expression_singleop_multiprocess_base_n.py \
    --config "$CONFIG_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --operators-path "$OPERATORS_PATH" \
    --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
    --num "$NUM" \
    --workers "$WORKERS" \
    --base 2


python generate_expression_singleop_multiprocess_base_n.py \
    --config "$CONFIG_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --operators-path "$OPERATORS_PATH" \
    --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
    --num "$NUM" \
    --workers "$WORKERS" \
    --base 3

