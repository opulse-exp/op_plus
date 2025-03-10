#!/bin/bash

export PYTHONPATH=$(pwd)
# Set paths for the config, initial operators file, and output files
export CONFIG_PATH="config/exp_configs/generate_expression_depth2.yaml"
export OPERATORS_PATH="/map-vepfs/kaijing/op_plus/opulse/data/operator/operator_100.jsonl" 
export GENERATED_EXPRESSION_PATH="data/exps/combination_100"
export CYTHON_CACHE_DIR="./compiled_funcs"

export NUM=100000
export WORKERS=8


python generate_expression_multiprocess_base_n_depth_m_q.py \
    --config "$CONFIG_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --operators-path "$OPERATORS_PATH" \
    --generated-expression-path "$GENERATED_EXPRESSION_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --num "$NUM" \
    --workers "$WORKERS" 



