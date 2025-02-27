import argparse
from operatorplus.operator_manager import OperatorManager
from config import LogConfig, ParamConfig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete multiple operators from a list and save the updated operator file.")
    parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    parser.add_argument('--operator-file', type=str, required=True, help='Path to the operator JSONL file')
    parser.add_argument('--operator-ids', type=int, nargs='+', required=True, help='List of operator IDs to delete')
    parser.add_argument('--output-operator-file', type=str, required=True, help='Path to save the updated operator JSONL file')
    args = parser.parse_args()
    config = ParamConfig(args.config)
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    operator_manager = OperatorManager(args.operator_file, config, log)

    for operator_id in args.operator_ids:
        operator_manager.delete_one_operator(operator_id)

    operator_manager.save_operators_to_jsonl(args.output_operator_file)
