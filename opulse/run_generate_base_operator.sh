#!/bin/bash


CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/generate_operator.yaml"
OPERATOR_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators.jsonl"
OUTPUT_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base.jsonl"

python generate_base_operator.py --config "$CONFIG_PATH" --operator-file "$OPERATOR_FILE" --output-file "$OUTPUT_FILE"


