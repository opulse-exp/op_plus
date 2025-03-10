import random
from typing import Dict, Any, List
from expression.expression_evaluator import ExpressionEvaluator
from operatorplus.operator_manager import OperatorManager
from operatorplus.operator_info import OperatorInfo
import json
from collections import defaultdict
from expression.expression_node import (
    ExpressionNode,
    NumberNode,
    BinaryExpressionNode,
    UnaryExpressionNode,
    VariableNode,
)
import time
from expression.base_converter import BaseConverter
from config import LogConfig, ParamConfig
from expression.expression_evaluator import LongerResultInfo
from operatorplus.compiler import CythonCompiler

class ExpressionGenerator:

    def __init__(
        self,
        param_config: ParamConfig,
        logger: LogConfig,
        cython_cache_dir : str,
        operator_manager: OperatorManager,
        # variables: List[str] = None,
        # min_value: int = 0,
        # max_value: int = 100,
        # max_depth: int = 3,
        # expr_type_weights: Dict[str, float] = None,
        # atoms_type_weights: Dict[str, float] = None,
    ):
        """
        Initializes the ExpressionGenerator with configuration parameters and dependencies.

        Args:
            param_config (ParamConfig): Configuration parameters for expression generation.
            logger (LogConfig): Logging configuration to record events and errors.
            operator_manager (OperatorManager): Manager for handling operators used in expressions.
        """
        self.param_config = param_config
        self.logger = logger.get_logger()

        self.variables = self.param_config.get("expr_variables")
        self.max_value = self.param_config.get("expr_numeric_range")["max_value"]
        self.min_value = self.param_config.get("expr_numeric_range")["min_value"]

        self.max_depth = self.param_config.get("expr_max_depth")

        self.expr_type_weights = self.param_config.get("expr_type_weights")

        self.atoms_type_weights = self.param_config.get("expr_atom_type_weights")

        self.cur_expr_id = 0
        self.operator_manager = operator_manager

        unary_prefix_ops, unary_postfix_ops, self.binary_ops = (
            operator_manager.get_unary_and_binary_operators()
        )

        self.unary_postfix_ops = [
            opinfo for opinfo in unary_postfix_ops if opinfo.is_base is None
        ]
        self.unary_prefix_ops = [
            opinfo for opinfo in unary_prefix_ops if opinfo.is_base is None
        ]


        self.operators2expr: Dict[int, list[int]] = defaultdict(list)


        self.base_converter = BaseConverter(
            self.param_config.get("max_base"), self.param_config.get("custom_digits")
        )
        self.max_base = self.param_config.get("max_base")
        self.random_base_flag: bool = self.param_config.get("random_base")["flag"]
        self.current_base: int = self.param_config.get("random_base")["base"]
        # self.logger.debug(f"init: current base: {self.current_base}")
        self.result_base: int = self.param_config.get("result_base")["base"]
        self.result_base_random_flag: bool = self.param_config.get("result_base")[
            "random_flag"
        ]
        # related to longer result compute
        self.longer_result_compute_flag: bool = self.param_config.get("longer_result_compute")["flag"]
        self.longer_result_compute_base: int = self.param_config.get("longer_result_compute")["base"]

        self.expr_evaluator = ExpressionEvaluator(
            param_config,
            logger,
            cython_cache_dir,
            operator_manager,
            base_converter=self.base_converter,
        )

    def set_random_base(self, random_flag: bool, target_base: int = 10):
        self.random_base_flag = random_flag
        if random_flag == False:
            self.current_base = target_base

    def set_variables(self, new_variables: List[str]):
        """
        Updates the list of variables used in expression generation.

        Args:
            new_variables (List[str]): A list of variable names to be used in expressions.
        """
        self.variables = new_variables

    def set_max_depth(self, max_depth: int) -> None:
        """
        Sets the maximum depth for generated expression trees.

        Args:
            max_depth (int): The maximum depth of the expression tree.
        """
        self.max_depth = max_depth

    def generate_random_value(self) -> int:
        """
        Generates a random integer value within the predefined min and max range.

        Returns:
            int: A randomly generated integer value.
        """
        mid_value = random.randint(self.min_value, self.max_value)
        value = random.randint(self.min_value, mid_value)
        return value
        # return random.randint(self.min_value, self.max_value)

    def generate_random_base(self) -> int:
        """
        Generates a random base for number representation within the allowed range.

        Returns:
            int: A randomly selected base for number representation.
        """
        # self.logger.debug(f"current base: {self.current_base}")
        if self.random_base_flag:
            return random.randint(2, self.max_base)
        else:
            return self.current_base

    def generate_atoms(self, atom_choice: str) -> ExpressionNode:
        """
        Generates an atomic node based on the specified type.

        Args:
            atom_choice (str): Specifies the type of atomic element to generate. Options are 'variable', 'number', or 'variable_and_number'.

        Returns:
            ExpressionNode: An atomic node representing either a variable or a number.

        Raises:
            ValueError: If the provided atom_choice is not recognized.
        """
        atoms_node = None
        if atom_choice == "variable":
            
            atoms_node = VariableNode(random.choice(self.variables))
        elif atom_choice == "number":
            
            atoms_node = NumberNode(
                self.generate_random_value(), self.generate_random_base()
            )
        elif atom_choice == "variable_and_number":
            
            atoms_type = random.choices(
                ["variable", "number"],
                weights=[
                    self.atoms_type_weights["variable"],
                    self.atoms_type_weights["number"],
                ],
            )[0]
            if atoms_type == "variable":
                atoms_node = VariableNode(random.choice(self.variables))
            else:
                atoms_node = NumberNode(
                    self.generate_random_value(), self.generate_random_base()
                )
        else:
            raise ValueError(
                f"Unknown atom_choice value: {atom_choice}. Valid options are 'variable', 'number', or 'variable_and_number'."
            )
        if atoms_node == None:
            self.logger.error("atoms_node is None")
        return atoms_node

    def generate_expression(
        self, cur_depth, max_depth, atom_choice: str, is_op_weight: bool = False, fixed_op: OperatorInfo = None
    ) -> Dict[str, Any]:
        """
        Recursively generates a random expression tree up to a specified depth.

        Args:
            cur_depth (int): Current depth of recursion.
            max_depth (int): Maximum depth of the expression tree.
            atom_choice (str): Determines what type of atoms can be generated ('variable', 'number', 'variable_and_number').

        Returns:
            ExpressionNode: A node representing part of the expression tree.
        """
        if cur_depth >= max_depth:
            expr_node = self.generate_atoms(atom_choice)
            return expr_node

        if fixed_op is not None:
            available_type=["atoms","fixed_op"]
            expr_type=random.choices(available_type,weights=[0.5,0.5])[0]
            if expr_type=="atoms":
                expr_node = expr_node = self.generate_atoms(atom_choice)
                return expr_node
            elif expr_type=="fixed_op":
                if fixed_op.n_ary==1:
                    expr_node = UnaryExpressionNode(fixed_op)
                    expr_node.unary_expr = self.generate_expression(
                        cur_depth + 1, max_depth, atom_choice,fixed_op=fixed_op
                    )
                    expr_node.unary_expr.position = "unary"
                    return expr_node
                else:
                    expr_node = BinaryExpressionNode(fixed_op)
                    expr_node.left_expr = self.generate_expression(
                        cur_depth + 1, max_depth, atom_choice,fixed_op=fixed_op
                    )
                    expr_node.left_expr.position = "left"
                    expr_node.right_expr = self.generate_expression(
                        cur_depth + 1, max_depth, atom_choice,fixed_op=fixed_op
                    )
                    expr_node.right_expr.position = "right"
                    return expr_node

        expr_type = random.choices(
            ["binary", "unary_prefix", "unary_postfix", "atoms"],
            weights=[
                self.expr_type_weights["binary"],
                self.expr_type_weights["unary_prefix"],
                self.expr_type_weights["unary_postfix"],
                self.expr_type_weights["atoms"],
            ],
        )[0]

        if expr_type == "binary":
            
            if not self.binary_ops:
                
                return self.generate_expression(cur_depth, max_depth, atom_choice)
            binary_op_weights = [opinfo.weight for opinfo in self.binary_ops]
            if is_op_weight:
                select_op = random.choices(
                    self.binary_ops,
                    weights=binary_op_weights,
                )[0]
            else:
                equal_weight = [1] * len(self.binary_ops)
                select_op = random.choices(
                    self.binary_ops,
                    weights=equal_weight,
                )[0]

            # select_op = random.choice(self.binary_ops)
            expr_node = BinaryExpressionNode(select_op)

            # The reason for recording the position here is that when converting to an expression string, 
            # parentheses need to be added appropriately, especially considering associativity.
            # For example, in the expression tree: 1 + (2 + 3), after outputting 2 + 3, 
            # the recursive upper level needs to determine whether to add parentheses.

            expr_node.left_expr = self.generate_expression(
                cur_depth + 1, max_depth, atom_choice
            )
            expr_node.left_expr.position = "left"
            expr_node.right_expr = self.generate_expression(
                cur_depth + 1, max_depth, atom_choice
            )
            expr_node.right_expr.position = "right"
            return expr_node
        elif expr_type == "unary_prefix":
            if not self.unary_prefix_ops:
                return self.generate_expression(cur_depth, max_depth, atom_choice)
            unary_prefix_ops_weights = [
                opinfo.weight for opinfo in self.unary_prefix_ops
            ]
            if is_op_weight:
                select_op = random.choices(
                    self.unary_prefix_ops,
                    weights=unary_prefix_ops_weights,
                )[0]
            else:
                equal_weight = [1] * len(self.unary_prefix_ops)
                select_op = random.choices(
                    self.unary_prefix_ops,
                    weights=equal_weight,
                )[0]
            # select_op = random.choice(self.unary_prefix_ops)
            # if select_op.is_base:
            #     print("error")
            #     exit(1)
            expr_node = UnaryExpressionNode(select_op)
            expr_node.unary_expr = self.generate_expression(
                cur_depth + 1, max_depth, atom_choice
            )
            expr_node.unary_expr.position = "unary"
            return expr_node
        elif expr_type == "unary_postfix":
            if not self.unary_postfix_ops:
                return self.generate_expression(cur_depth, max_depth, atom_choice)
            unary_postfix_ops_weights = [
                opinfo.weight for opinfo in self.unary_postfix_ops
            ]
            if is_op_weight:
                select_op = random.choices(
                    self.unary_postfix_ops,
                    weights=unary_postfix_ops_weights,
                )[0]
            else:
                equal_weight = [1] * len(self.unary_postfix_ops)
                select_op = random.choices(
                    self.unary_postfix_ops,
                    weights=equal_weight,
                )[0]
            # select_op = random.choice(self.unary_postfix_ops)
            expr_node = UnaryExpressionNode(select_op)
            expr_node.unary_expr = self.generate_expression(
                cur_depth + 1, max_depth, atom_choice
            )
            expr_node.unary_expr.position = "unary"
            return expr_node
        elif expr_type == "atoms":
            expr_node = expr_node = self.generate_atoms(atom_choice)
            return expr_node


    def create_single_operator_expression(self, func_id:str):
        opinfo=self.operator_manager.get_operator_by_func_id(func_id)
        if opinfo.n_ary==1:
            expr_node = UnaryExpressionNode(opinfo)
            expr_node.unary_expr = NumberNode(
                self.generate_random_value(), self.generate_random_base()
            )
            expr_node.unary_expr.position = "unary"
        elif opinfo.n_ary==2:
            expr_node = BinaryExpressionNode(opinfo)
            expr_node.left_expr = NumberNode(
                self.generate_random_value(), self.generate_random_base()
            )
            expr_node.left_expr.position = "left"
            expr_node.right_expr = NumberNode(
                self.generate_random_value(), self.generate_random_base()
            )
            expr_node.right_expr.position = "right"
        

        expr_result_base = None
        longer_result_info = None
        if self.result_base_random_flag:
            expr_result_base = random.randint(2, self.max_base)
        else:
            expr_result_base = self.result_base
        if self.longer_result_compute_flag:
            longer_result_info = LongerResultInfo(
                target_base=self.longer_result_compute_base, flag=False,
            )

        self.expr_evaluator.init_expr(
            expression_tree=expr_node,
            id=self.cur_expr_id,
            op_mode=False,
            expr_result_base=expr_result_base,
            longer_result_info=longer_result_info,
        )
        # self.logger.debug(f"Evaluating expression {self.cur_expr_id}")
        properties = self.expr_evaluator.evaluate()
        # print(properties["used_operators"])
        for op_id in properties["used_operators"]:
            self.operators2expr[op_id].append(self.cur_expr_id)

        self.cur_expr_id += 1

        return properties
    
    def create_expression(self, atom_choice: str, fix_func_id:str = None) -> Dict[str, Any]:
        """
        Creates a new expression, evaluates it, and records the used operators.

        Args:
            atom_choice (str): Determines the type of atoms that can be included in the expression.

        Returns:
            Dict[str, Any]: Properties of the evaluated expression, including used operators.
        """
        # self.logger.debug(f"Generating expression {self.cur_expr_id}")
        if fix_func_id is None:
            expression_tree = self.generate_expression(
                cur_depth=0, max_depth=self.max_depth, atom_choice=atom_choice, 
            )
        else:
            expression_tree = self.generate_expression(
                cur_depth=0, max_depth=self.max_depth, atom_choice=atom_choice, fixed_op=
                self.operator_manager.get_operator_by_func_id(fix_func_id)
            )

        expr_result_base = None
        longer_result_info = None
        if self.result_base_random_flag:
            expr_result_base = random.randint(2, self.max_base)
        else:
            expr_result_base = self.result_base
        if self.longer_result_compute_flag:
            longer_result_info = LongerResultInfo(
                target_base=self.longer_result_compute_base, flag=False,
            )

        self.expr_evaluator.init_expr(
            expression_tree=expression_tree,
            id=self.cur_expr_id,
            op_mode=False,
            expr_result_base=expr_result_base,
            longer_result_info=longer_result_info,
        )
        # self.logger.debug(f"Evaluating expression {self.cur_expr_id}")
        properties = self.expr_evaluator.evaluate()
        # print(properties["used_operators"])
        for op_id in properties["used_operators"]:
            self.operators2expr[op_id].append(self.cur_expr_id)

        # return expression_tree
        self.cur_expr_id += 1

        return properties


    def create_expression_str(self, max_depth: int, atom_choice: str) -> str:
        """
        Generates a string representation of an expression with all sub-expressions enclosed in brackets.

        This method creates a new expression tree and evaluates it to obtain a string representation,
        ensuring that all parts of the expression are fully parenthesized for clarity. It also updates
        the unary and binary operators before generating the expression.

        Args:
            atom_choice (str): Specifies the type of atomic elements to include in the expression ('variable', 'number', or 'variable_and_number').

        Returns:
            str: A fully parenthesized string representation of the generated expression.
        """
        self.unary_prefix_ops, self.unary_postfix_ops, self.binary_ops = (
            self.operator_manager.get_unary_and_binary_operators()
        )
        expression_tree = self.generate_expression(
            cur_depth=0, max_depth=max_depth, atom_choice=atom_choice
        )
        self.expr_evaluator.set_with_all_brackets(True)
        self.expr_evaluator.init_expr(expression_tree, self.cur_expr_id, op_mode=True)
        # evaluator = ExpressionEvaluator(expression_tree, self.operator_manager)
        # properties = self.expr_evaluator.evaluate()

        return self.expr_evaluator.expression_str

    def create_expression_str_by_order(self, max_depth: int, atom_choice: str) -> str:
        pass

    def create_n_expression_str_with_order(
        self, max_depth: int, atom_choice: str, order: int, branch_num: int
    ) -> List[str]:

        unary_prefix_ops, unary_postfix_ops, binary_ops = (
            self.operator_manager.get_unary_and_binary_operators()
        )
        self.unary_postfix_ops = [opinfo for opinfo in unary_postfix_ops if opinfo.n_order<=order] 
        self.unary_prefix_ops = [opinfo for opinfo in unary_prefix_ops if opinfo.n_order<=order]
        self.binary_ops = [opinfo for opinfo in binary_ops if opinfo.n_order<=order]
        
        n_order_binary_ops = [
            opinfo for opinfo in binary_ops if opinfo.n_order == order
        ]
        n_order_unary_prefix_ops = [
            opinfo for opinfo in unary_prefix_ops if opinfo.n_order == order
        ]
        n_order_unary_postfix_ops = [
            opinfo for opinfo in unary_postfix_ops if opinfo.n_order == order
        ]
        n_order_unary_ops = n_order_unary_prefix_ops + n_order_unary_postfix_ops

        select_n_order_op = random.choice(n_order_binary_ops + n_order_unary_ops)
        while True:
            expression_trees = []
            all_op_dicts: List[int, int] = []
            for _ in range(branch_num):
                expression_tree = self.generate_expression(
                    cur_depth=0, max_depth=max_depth, atom_choice=atom_choice
                )
                self.expr_evaluator.set_with_all_brackets(True)
                self.expr_evaluator.init_expr(
                    expression_tree, self.cur_expr_id, op_mode=True
                )
                all_op_dicts.append(self.expr_evaluator.all_operators)
                expression_trees.append(expression_tree)
            all_op_id = set().union(*all_op_dicts)
            all_op_info = [
                self.operator_manager.get_operator_by_func_id(op_id) for op_id in all_op_id
            ]

            candidate_replace_op_info = [
                opinfo
                for opinfo in all_op_info
                if opinfo.n_ary == select_n_order_op.n_ary
            ]
            if len(candidate_replace_op_info) > 0:
                break
        replace_op = random.choice(candidate_replace_op_info)

        def replace_target_op(
            node: ExpressionNode, replaced_op: OperatorInfo, target_op: OperatorInfo
        ):
            if isinstance(node, BinaryExpressionNode):
                if node.operator == replaced_op:
                    node.operator = target_op
                replace_target_op(node.left_expr, replaced_op, target_op)
                replace_target_op(node.right_expr, replaced_op, target_op)
            elif isinstance(node, UnaryExpressionNode):
                if node.operator == replaced_op:
                    node.operator = target_op
                replace_target_op(node.unary_expr, replaced_op, target_op)
            else:
                return

        for expression_tree in expression_trees:
            replace_target_op(expression_tree, replace_op, select_n_order_op)

        expression_strs = []
        for expression_tree in expression_trees:
            self.expr_evaluator.set_with_all_brackets(True)
            self.expr_evaluator.init_expr(
                expression_tree, self.cur_expr_id, op_mode=True
            )
            expression_strs.append(self.expr_evaluator.expression_str)

        return expression_strs

    def dump_op2expr(self, file_path):
        """
        Dumps the mapping of operator IDs to expression IDs into a JSON Lines file.

        Each line in the output file contains a JSON object representing the relationship between
        an operator ID and the list of expression IDs that use this operator.

        Args:
            file_path (str): The path to the output file where the operator-expression mappings will be saved.
        """
        with open(file_path, "w") as f:
            for op_id in self.operators2expr:
                data = {
                    "op_id": op_id,
                    "expr_id": self.operators2expr[op_id],
                }
                json.dump(data, f)
                f.write("\n")


# if __name__ == "__main__":
#     # from operatorplus.operator_manager import OperatorManager
#     config_path = "config/generate_operator.yaml"
#     initial_operators_path = "data/operator_100/2_order/2_order_initial.jsonl"
#     global config
#     config = ParamConfig(config_path)
#     logging_config = config.get_logging_config()
#     log = LogConfig(logging_config)
#     global logger
#     logger = log.get_logger()
#     # Initialize Operator Manager
#     op_manager = OperatorManager(initial_operators_path, config, log)
#     expr_generator = ExpressionGenerator(config, log, op_manager)
#     exprs = expr_generator.create_n_expression_str_with_order(
#         random.randint(1, expr_generator.max_depth),
#         atom_choice="variable_and_number",
#         order=2,
#         branch_num=3,
#     )
#     print(exprs)

# if __name__ == "__main__":
#     # from operatorplus.operator_manager import OperatorManager

#     test_depth = [3]
#     all_scale = [
#         10,
#     ]
#     result = {}
#     # manager = OperatorManager("data/operator/initial_operators.jsonl")

#     param_config = ParamConfig("config/default.yaml")
#     log_config = LogConfig(param_config.config)
#     op_manager = OperatorManager(
#         param_config=param_config,
#         logger=log_config,
#         config_file="data/operator/op_test_12_8_1000.jsonl",
#     )
#     generator = ExpressionGenerator(op_manager, param_config, log_config)
#     for depth in test_depth:
#         generator.set_max_depth(depth)
#         for num in all_scale:
#             start_time = time.time()  
#             with open("data/expression/expression_test.jsonl", "w") as f:
#                 for i in range(num):
#                     properties = generator.create_expression("number")
#                     json.dump(properties, f)
#                     f.write("\n")
#             generator.dump_op2expr("data/expression/op2expr.jsonl")
#             end_time = time.time()
#             print(f"test_depth:{depth}, num={num}, time={end_time-start_time}")
#             result[depth] = end_time - start_time

# print(result)
# with open("data/expression/efficiency_with_tree.json", "w") as f:
#     json.dump(result, f)


# if __name__ == "__main__":
#     variables = ["a"]
#     operator_manager = OperatorManager(
#         config_file="data/operator/initial_operators.jsonl"
#     )

#     expr_generator = ExpressionGenerator(
#         variables=variables, operator_manager=operator_manager
#     )

#     for _ in range(10):
#         expr = expr_generator.create_expression_str(atom_choice="variable_and_number")
#         print(f"生成的表达式（仅 'a' 变量）: {expr}")
#         print("-" * 50)

#     expr_generator.set_variables(["a", "b"])
#     for _ in range(10):
#         expr = expr_generator.create_expression_str(atom_choice="variable_and_number")
#         print(f"生成的表达式（'a' 和 'b' 变量）: {expr}")
#         print("-" * 50)
