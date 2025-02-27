#!/bin/bash


CONFIG_PATH="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/generate_operator.yaml"
OPERATOR_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100/5_order/5_order_raise.jsonl"
OUTPUT_FILE="/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/data/operator_100/5_order/5_order_raise_final.jsonl"



OPERATOR_IDS=(103 101 100 98 96 95 94)

OPERATOR_IDS_ARG=$(IFS=' ' ; echo "${OPERATOR_IDS[*]}")


python delete_operators.py \
  --config "$CONFIG_PATH" \
  --operator-file "$OPERATOR_FILE" \
  --operator-ids $OPERATOR_IDS_ARG \
  --output-operator-file "$OUTPUT_FILE"

