#!/bin/bash


CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/generate_operator.yaml"
OPERATOR_FILE_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base.jsonl"
OUTPUT_OPERATOR_FILE_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator/generated_operators_base_2.jsonl"


python assign_operator_priority.py \
  --config "$CONFIG_PATH" \
  --operator-file "$OPERATOR_FILE_PATH" \
  --output-operator-file "$OUTPUT_OPERATOR_FILE_PATH"
