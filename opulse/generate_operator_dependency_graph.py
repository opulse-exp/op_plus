from lark import Lark
from operatorplus import *
from expression.expression_generator import ExpressionGenerator
from typing import Dict, List, Optional, Any, Tuple
from config import LogConfig, ParamConfig

if __name__ == "__main__":
    config = ParamConfig(
        "config/generate_operator.yaml"
    )
    logging_config = config.get_logging_config()
    log = LogConfig(logging_config)
    op_manager = OperatorManager(
        "data/operator/operator_100.jsonl",
        config,
        log,
    )
    operator_dependency_graph = OperatorDependencyGraph(log, op_manager)
    graph, topo_sorted = operator_dependency_graph.build_dependency_graph()
    operator_dependency_graph.visualize_dependency_graph()
    operator_dependency_graph.write_dependency_to_jsonl()
