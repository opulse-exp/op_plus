#!/bin/bash

export PYTHONPATH=$(pwd)

CONFIG_PATH="config/generate_operator.yaml"
INITIAL_OPERATORS_PATH="data/initial.jsonl"
GENERATED_OPERATORS_PATH="data/final.jsonl"
CYTHON_CACHE_DIR="./compiled_funcs"
NUM_OPERATORS=5
MAX_WORKERS=1
RATIO=0.6
RAISE_INCREASE_AT_ORDER=3
INCREASE_COUNT=3
CONTINUE_MODE=False

python generate_operator_multiprocess.py \
    --config "$CONFIG_PATH" \
    --initial-operators-path "$INITIAL_OPERATORS_PATH" \
    --generated-operators-path "$GENERATED_OPERATORS_PATH" \
    --cython-cache-dir "$CYTHON_CACHE_DIR" \
    --num "$NUM_OPERATORS" \
    --max-workers "$MAX_WORKERS" \
    --ratio "$RATIO" \
    --raise-increase-at-order "$RAISE_INCREASE_AT_ORDER" \
    --increase-count "$INCREASE_COUNT" \
    --continue-mode "$CONTINUE_MODE"