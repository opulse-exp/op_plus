from typing import Tuple, Optional, Union, Dict, List
from operatorplus.operator_manager import OperatorManager
from collections import defaultdict
from expression.expression_node import (
    ExpressionNode,
    NumberNode,
    BinaryExpressionNode,
    UnaryExpressionNode,
    VariableNode,
)
from expression.expression_base_converter import ExpressionBaseConverter
from typing import cast
from operatorplus.operator_info import OperatorInfo
from expression.base_converter import BaseConverter
from config import ParamConfig, LogConfig
# from operatorplus import op_func
from dataclasses import dataclass, asdict
import os
from operatorplus.compiler import CythonCompiler

@dataclass
class LongerResultInfo:
    target_base: int
    flag: bool


class ExpressionEvaluator:

    def __init__(
        self,
        param_config: ParamConfig,
        logger: LogConfig,
        cython_cache_dir: str,
        operator_manager: OperatorManager,
        base_converter: BaseConverter = None,
    ):
        """
        Initializes an instance of the ExpressionEvaluator class.

        This constructor sets up the expression evaluator with necessary configurations and managers.
        It initializes attributes to manage expression trees, operators, logging, and base conversions.
        Additionally, it prepares data structures to track operator priorities, operation counts, and highest n-order values.

        Parameters:
            param_config (ParamConfig): Configuration settings for controlling the behavior of the expression evaluator.
            logger (LogConfig): Configuration for setting up logging. Used to create a logger instance for this evaluator.
            operator_manager (OperatorManager): Manager object that provides information about operators used in expressions.
            base_converter (BaseConverter, optional): Converter object for handling different numerical bases in expressions. Defaults to None.
        """
        self.param_config = param_config
        self.logger = logger.get_logger()
        # Initialization of relevant expressions to None
        self.id = None
        self.expression_tree: ExpressionNode = None
        self.expression_str: str = None
        self.operator_manager = operator_manager
        self.base_converter = base_converter
        self.all_priority = []
        self.operation_count = 0
        self.highest_n_order = 0
        # Record all operators key: op id, value: number of occurrences
        self.all_operators: Dict[str, int] = defaultdict(int)
        self.with_all_brackets = False
        self.cython_cache_dir = cython_cache_dir
        # Used to replace meta words in expression strings
        self.load_atoms()

    def set_with_all_brackets(self, with_all_brackets: bool) -> None:
        """
        Sets whether to include all brackets in the expression string.

        This method configures the behavior for generating expression strings. If set to True, it ensures that all parts of the
        expression that require parentheses for correct order of operations will be enclosed in brackets. This can be useful
        for ensuring clarity or for specific formatting requirements.

        Parameters:
            with_all_brackets (bool): A flag indicating whether to include all necessary brackets in the expression string.
        """
        self.with_all_brackets = with_all_brackets

    def load_atoms(self) -> None:
        """
        Loads atomic symbols from the parameter configuration.
        """
        self.atoms = {
            "left_bracket": self.param_config.get("other_symbols_atoms")[
                "left_parenthesis"
            ],
            "right_bracket": self.param_config.get("other_symbols_atoms")[
                "right_parenthesis"
            ],
            "NaN": self.param_config.get("other_symbols_atoms")["nan_symbol"],
            "equal": self.param_config.get("other_symbols_atoms")["equals_sign"],
            "Inf": self.param_config.get("other_symbols_atoms")["inf_symbol"],
            "-Inf": self.param_config.get("other_symbols_atoms")["neg_inf_symbol"],
        }

    def init_expr(
        self,
        expression_tree,
        id,
        op_mode: bool = False,
        expr_result_base: int = None,
        longer_result_info: LongerResultInfo = None,
    ):
        """
        Initializes expression attributes with an expression tree and ID.

        This method sets up the initial state for an expression by assigning an identifier and an expression tree.
        It also initializes counters and dictionaries that will be used to track various properties of the expression,
        such as operator priorities, operation counts, and operator occurrences. Finally, it generates string representations
        of the expression based on the provided tree structure and optional parameters.

        Parameters:
            expression_tree (ExpressionNode): The root node of the expression tree to initialize.
            id (any): An identifier for the expression, which can be any type that uniquely identifies the expression.
            op_mode (bool, optional): A flag indicating whether the expression should be processed in operator mode. Defaults to False.
        """
        self.id = id
        self.expression_tree = expression_tree
        self.cot_info: List[str] = []
        self.cot: List[str] = []
        self.all_priority = []
        self.operation_count = 0
        self.number_count = 0
        self.variable_count = 0
        self.highest_n_order = 0
        self.expr_result = None
        self.normalized_expansion_degree = None
        self.all_operators: Dict[str, int] = defaultdict(int)
        self.expr_result_base = expr_result_base
        self.longer_result_info = longer_result_info
        if op_mode:
            self.expression_str = self.tree_to_str(self.expression_tree, op_mode=True)
        else:
            self.expression_str = self.tree_to_str(self.expression_tree, statistic_analysis=True)
            self.expression_str_no_base_symbol = self.tree_to_str(
                self.expression_tree, with_base_symbol=False
            )

    def op_info_sub_tree(self, node) -> None:
        if isinstance(node, NumberNode):
            return
        if isinstance(node, BinaryExpressionNode):
            self.op_info_sub_tree(node.left_expr)
            self.op_info_sub_tree(node.right_expr)
            self.all_operators[node.operator.func_id] += 1
            return
        elif isinstance(node, UnaryExpressionNode):
            self.op_info_sub_tree(node.unary_expr)
            self.all_operators[node.operator.func_id] += 1
            return
        elif isinstance(node, VariableNode):
            return
        else:
            raise NotImplementedError("ExpressionEvaluator.op_info_sub_tree")

    def all_op_info(self) -> Dict[int, int]:
        self.all_operators = defaultdict(int)
        self.op_info_sub_tree(self.expression_tree)

        return self.all_operators

    def tree_to_str(
        self,
        node: ExpressionNode,
        parent_op: OperatorInfo = None,
        with_base_symbol: bool = True,
        op_mode: bool = False,
        statistic_analysis:bool = False,
    ) -> str:
        """
        Converts an expression tree node to a string representation.

        This method recursively traverses the expression tree and builds a string representation based on the node type.
        For binary and unary expression nodes, it checks the operator priority relative to the parent node's operator priority
        to determine if parentheses are needed to preserve correct order of operations.
        For number and variable nodes, it returns their direct string representations.

        Parameters:
            node (ExpressionNode): The expression node to convert.
            parent_op (OperatorInfo, optional): Information about the parent operator, used to determine if parentheses are needed. Defaults to None.
            with_base_symbol (bool, optional): Whether to include base symbols in the string. Defaults to True.
            op_mode (bool, optional): A flag indicating operator mode. Defaults to False.

        Returns:
            str: String representation of the expression node.

        Raises:
            NotImplementedError: If an unsupported expression node type is encountered.
        """

        # Requires the priority of the parent node's operator for determining whether to add brackets
        if isinstance(node, NumberNode):
            node = cast(NumberNode, node)
            if op_mode:
                # when op_mode, we don't generate any base-related symbol
                return f"{node.to_str_no_base_symbol()}"
            else:
                if statistic_analysis:
                    self.number_count += 1
                if with_base_symbol:
                    return f"{node.to_str(self.operator_manager,self.base_converter)}"
                else:
                    return f"{node.to_str_no_base_symbol(surround_symbol='$')}"
        elif isinstance(node, VariableNode):
            return f"{node.v}"
        elif isinstance(node, BinaryExpressionNode):
            node = cast(BinaryExpressionNode, node)
            if not op_mode:
                if statistic_analysis:
                    # Statistical priority for calculating calculate_priority_hierarchical_complexity
                    if (
                        node.operator.priority != None
                        and node.operator.priority not in self.all_priority
                    ):
                        self.all_priority.append(node.operator.priority)
                    # Count the number of operations and associate the expression with the operator
                    self.operation_count += 1
                    self.all_operators[node.operator.func_id] += 1
                    # Count the n_order info
                    if self.highest_n_order < node.operator.n_order:
                        self.highest_n_order = node.operator.n_order
            else:
                self.operation_count += 1
                self.all_operators[node.operator.func_id] += 1
            # Convert the expression of the subtree
            left_str = self.tree_to_str(
                node.left_expr,
                node.operator,
                with_base_symbol=with_base_symbol,
                op_mode=op_mode,
                statistic_analysis=statistic_analysis,
            )
            right_str = self.tree_to_str(
                node.right_expr,
                node.operator,
                with_base_symbol=with_base_symbol,
                op_mode=op_mode,
                statistic_analysis=statistic_analysis,
            )

            if self.with_all_brackets:
                return f"{self.atoms['left_bracket']}{left_str}{node.operator.symbol}{right_str}{self.atoms['right_bracket']}"
            # self.logger.debug(f"parent_op: {parent_op}")
            if parent_op != None and node.operator.priority < parent_op.priority:
                return f"{self.atoms['left_bracket']}{left_str}{node.operator.symbol}{right_str}{self.atoms['right_bracket']}"
            elif parent_op != None and node.operator.priority == parent_op.priority:
                # If it has the same priority as parent op, choose whether to add parentheses or not based on location and binding.
                if (
                    parent_op.associativity_direction == "left"
                    and node.position == "right"
                ):
                    return f"{self.atoms['left_bracket']}{left_str}{node.operator.symbol}{right_str}{self.atoms['right_bracket']}"
                elif (
                    parent_op.associativity_direction == "right"
                    and node.position == "left"
                ):
                    return f"{self.atoms['left_bracket']}{left_str}{node.operator.symbol}{right_str}{self.atoms['right_bracket']}"
                else:
                    return f"{left_str}{node.operator.symbol}{right_str}"
            else:
                return f"{left_str}{node.operator.symbol}{right_str}"
        elif isinstance(node, UnaryExpressionNode):
            node = cast(UnaryExpressionNode, node)
            if not op_mode:
                if statistic_analysis:
                    # Statistical priority for calculating calculate_priority_hierarchical_complexity
                    if (
                        node.operator.priority != None
                        and node.operator.priority not in self.all_priority
                    ):
                        self.all_priority.append(node.operator.priority)
                    # Count the number of operations and associate the expression with the operator
                    self.operation_count += 1
                    self.all_operators[node.operator.func_id] += 1
                    # Count the n_order info
                    if node.operator.n_order==None:
                        print(node.operator.func_id)
                    if self.highest_n_order < node.operator.n_order:
                        self.highest_n_order = node.operator.n_order
            else:
                self.operation_count += 1
                self.all_operators[node.operator.func_id] += 1
            unary_str = self.tree_to_str(
                node.unary_expr,
                node.operator,
                with_base_symbol=with_base_symbol,
                op_mode=op_mode,
                statistic_analysis=statistic_analysis,
            )
            if node.operator.unary_position=='postfix':
                return f"({unary_str}{node.operator.symbol})"
            elif node.operator.unary_position=='prefix':
            # Doubt: Always choose to add brackets to unary
                return f"({node.operator.symbol}{unary_str})"
        else:
            raise NotImplementedError("ExpressionEvaluator.tree_to_str")

    def calculate_highest_n_order(self) -> int:
        """
        Calculates the highest n-order of the expression.

        Returns:
            (int): The highest n-order value.
        """
        return self.highest_n_order

    def calculate_priority_hierarchical_complexity(self) -> int:
        """
        Calculates the priority-based hierarchical complexity.

        Returns:
            (int): The complexity value.
        """
        return len(self.all_priority)

    def calculate_normalized_expansion_degree(self) -> Union[int, str]:
        # Implementing the computational logic for normalized expansion degree
        """
        Calculates the normalized expansion degree of the expression.

        Returns:
            (int): The normalized expansion degree or "NaN".
        """
        normalized_expansion_degree = self.normalized_expansion_degree
        if self.normalized_expansion_degree is not None:
            # return (
            #     self.normalized_expansion_degree
            #     if self.normalized_expansion_degree != "NaN"
            #     else self.atoms["NaN"]
            # )
            normalized_expansion_degree = self.normalized_expansion_degree
        else:
            degree, result = self.calculate_normalized_expansion_degree_node(
                self.expression_tree
            )
            self.normalized_expansion_degree = degree
            self.expr_result = result
            normalized_expansion_degree = degree

        if normalized_expansion_degree != normalized_expansion_degree:
            return self.atoms["NaN"]
        elif normalized_expansion_degree == float("inf"):
            return self.atoms["Inf"]
        elif normalized_expansion_degree == float("-inf"):
            return self.atoms["-Inf"]
        else:
            return self.normalized_expansion_degree

    def calculate_result(self) -> Union[str, int]:
        """
        Calculates the normalized expansion degree of the expression.

        The normalized expansion degree is a measure that represents how much an expression has been expanded or simplified.
        It can be used to evaluate the complexity of the expression in terms of its structure and size after operations.

        Returns:
            (Union[int, str]): The normalized expansion degree or "NaN".s an integer or "NaN" if it cannot be calculated.
        """
        expr_result = None
        if self.expr_result is not None:
            expr_result = self.expr_result
            # return self.expr_result if self.expr_result != "NaN" else self.atoms["NaN"]
        else:
            degree, result = self.calculate_normalized_expansion_degree_node(
                self.expression_tree
            )
            self.normalized_expansion_degree = degree
            self.expr_result = result
            expr_result = result
            # return self.expr_result if self.expr_result != "NaN" else self.atoms["NaN"]

        if self.expr_result_base != None and type(expr_result) == int:
            return ExpressionBaseConverter.convert_int_to_targetbase(
                input=expr_result,
                output_base=self.expr_result_base,
                base_converter=self.base_converter,
                operator_manager=self.operator_manager,
            )
        elif expr_result != expr_result:
            return self.atoms["NaN"]
        elif expr_result == float("inf"):
            return self.atoms["Inf"]
        elif expr_result == float("-inf"):
            return self.atoms["-Inf"]
        else:
            return expr_result
    # def get_compute_count_func(self, func_id:str):
    #     compiler = self.operator_manager.compiler
    #     op_module = compiler.import_module(f"module_{func_id}")

    #     compute_func = getattr(op_module, f"op_{func_id}", None)
    #     count_func = getattr(op_module, f"op_count_{func_id}", None)
    #     return compute_func, count_func

    def get_compute_count_func(self, operator:OperatorInfo):
        if operator.module == None:
            for depend_id in operator.dependencies:
                so_file = f"module_{depend_id}.cpython-310-x86_64-linux-gnu.so"
                full_path = os.path.join(self.cython_cache_dir, so_file)
                if os.path.exists(full_path):
                    self.operator_manager.compiler.import_module_from_path(f"module_{operator.func_id}")
            so_file = f"module_{operator.func_id}.cpython-310-x86_64-linux-gnu.so"
            full_path = os.path.join(self.cython_cache_dir, so_file)
            if os.path.exists(full_path):
                operator.module = self.operator_manager.compiler.import_module_from_path(f"module_{operator.func_id}")
        compute_func = getattr(operator.module, f"op_{operator.func_id}", None)
        count_func = getattr(operator.module, f"op_count_{operator.func_id}", None)
        return compute_func, count_func
    
    def get_target_base_str(self, value:int, target_base:int )->str:
        if value == float("inf") or value == float("-inf") or value != value:
            value_str_with_base=f"{value}"
        else:
            value_str_with_base=ExpressionBaseConverter.convert_int_to_targetbase(
                input=int(value),
                output_base=self.longer_result_info.target_base,
                base_converter=self.base_converter,
                operator_manager=self.operator_manager,
            )
        return value_str_with_base
    
    def calculate_normalized_expansion_degree_node(
        self, node: ExpressionNode, cot_layer: int = 0
    ) -> Tuple[Union[int, str], Union[int, str]]:
        """
        Helper method to recursively calculate the normalized expansion degree for each node in the expression tree.

        This method traverses the expression tree and computes the degree based on the type and structure of nodes.

        Args:
            node (ExpressionNode): The current node in the expression tree.

        Returns:
            (Tuple[Union[int, str], Union[int, str]]): A tuple containing the normalized expansion degree and the evaluation result of the node.

        Raises:
            NotImplementedError: If the node type is not recognized.

        """
        # For a single expression tree node, compute the normalized expansion of the tree rooted at this node and the resultant
        # if isinstance(node, NumberNode):
        #     return 0, node.value
        # elif isinstance(node, UnaryExpressionNode):
        #     sub_degree, sub_result = self.calculate_normalized_expansion_degree_node(
        #         node.unary_expr
        #     )
        #     if sub_degree == "NaN" or sub_result == "NaN":
        #         return "NaN", "NaN"
        #     cur_result = node.operator.get_compute_function()(sub_result)
        #     cur_degree = node.operator.get_count_function()(sub_result)
        #     if cur_degree == "NaN" or cur_result == "NaN":
        #         return "NaN", "NaN"
        #     return cur_degree + sub_degree, cur_result
        # elif isinstance(node, BinaryExpressionNode):
        #     # 二元操作符，分别计算左右子树的归一展开度
        #     left_degree, left_result = self.calculate_normalized_expansion_degree_node(
        #         node.left_expr
        #     )
        #     if left_degree == "NaN" or left_result == "NaN":
        #         return "NaN", "NaN"
        #     right_degree, right_result = (
        #         self.calculate_normalized_expansion_degree_node(node.right_expr)
        #     )
        #     if right_degree == "NaN" or right_result == "NaN":
        #         return "NaN", "NaN"
        #     cur_result = node.operator.get_compute_function()(left_result, right_result)
        #     cur_degree = node.operator.get_count_function()(left_result, right_result)
        #     if cur_degree == "NaN" or cur_result == "NaN":
        #         return "NaN", "NaN"
        #     return cur_degree + left_degree + right_degree, cur_result
        # elif isinstance(node, VariableNode):
        #     return "NaN", "NaN"
        # else:
        #     raise NotImplementedError(
        #         "ExpressionEvaluator.calculate_normalized_expansion_degree_node"
        #     )

        digits = self.base_converter.get_digits()
        


        def check_carry(input: List[int], output: int):
            pass
        special_values = [float("inf"), float("-inf")]
        try:
            if isinstance(node, NumberNode):
                self.cot_info.append(
                    {
                        "info": f"number node, value={node.value}",
                        "layer": cot_layer,
                    }
                )
                return 0, node.value
            elif isinstance(node, UnaryExpressionNode):
                sub_degree, sub_result = (
                    self.calculate_normalized_expansion_degree_node(
                        node.unary_expr, cot_layer=cot_layer + 1
                    )
                )
                # print(f"in compute, {node.operator.id}")
                # cur_result = getattr(op_func, f"op_{node.operator.id}")(sub_result)
                # cur_degree = getattr(op_func, f"op_count_{node.operator.id}")(sub_result)

                # cur_result = node.operator.get_compute_function()(sub_result)
                # cur_degree = node.operator.get_count_function()(sub_result)
                compute_func,count_func=self.get_compute_count_func(node.operator)

                cur_result = compute_func(sub_result)
                cur_degree = count_func(sub_result)

                if self.longer_result_info and self.longer_result_info.flag == False:
                    # if get a longer result by target base, set the flag to True
                    if cur_result == float("inf") or cur_result == float("-inf") or sub_result == float("inf") or sub_result == float("-inf") or cur_result != cur_result or sub_result != sub_result:
                        self.longer_result_info.flag = False # TODO: check this
                    else:
                        cur_result_str = self.base_converter.convert(
                            number=int(cur_result), base=self.longer_result_info.target_base
                        )
                        sub_result_str = self.base_converter.convert(
                            number=int(sub_result), base=self.longer_result_info.target_base
                        )
                        if len(cur_result_str) > len(sub_result_str):
                            self.longer_result_info.flag = True

                self.cot_info.append({
                    "info":f"compute unary expreesion, input={sub_result}, op_id = {node.operator.func_id}, unary_op_definition = '{node.operator.definition}', output={cur_result}","layer":cot_layer}
                )
                
                # prepare for cot
                cur_result_str_with_base = self.get_target_base_str(value = cur_result,target_base = self.longer_result_info.target_base)
                sub_result_str_with_base = self.get_target_base_str(value = sub_result,target_base = self.longer_result_info.target_base)

                if node.operator.unary_position=="prefix":
                    self.cot.append({"info":f"{node.operator.symbol}{sub_result_str_with_base}={cur_result_str_with_base}","layer":cot_layer})
                elif node.operator.unary_position=="postfix":
                    self.cot.append({"info":f"{sub_result_str_with_base}{node.operator.symbol}={cur_result_str_with_base}","layer":cot_layer})

                if cur_result !=cur_result or cur_result in special_values:
                    pass
                else:
                    cur_result = int(cur_result)
                return cur_degree + sub_degree, cur_result
            elif isinstance(node, BinaryExpressionNode):
                # 二元操作符，分别计算左右子树的归一展开度
                left_degree, left_result = (
                    self.calculate_normalized_expansion_degree_node(
                        node.left_expr, cot_layer=cot_layer + 1
                    )
                )
                right_degree, right_result = (
                    self.calculate_normalized_expansion_degree_node(
                        node.right_expr, cot_layer=cot_layer + 1
                    )
                )

                # print(f"in compute, {node.operator.id}")
                # cur_result = getattr(op_func, f"op_{node.operator.id}")(left_result, right_result)
                # cur_degree = getattr(op_func, f"op_count_{node.operator.id}")(left_result, right_result)
                compute_func,count_func=self.get_compute_count_func(node.operator)

                cur_result = compute_func(left_result, right_result)
                cur_degree = count_func(left_result, right_result)
                # cur_result = node.operator.get_compute_function()(
                #     left_result, right_result
                # )
                # cur_degree = node.operator.get_count_function()(
                #     left_result, right_result
                # )
                if self.longer_result_info and self.longer_result_info.flag == False:
                    if cur_result == float("inf") or cur_result == float("-inf") or left_result == float("inf") or left_result == float("-inf") or right_result == float("inf") or right_result == float("-inf") or cur_result != cur_result or left_result != left_result or right_result != right_result:
                        self.longer_result_info.flag = False
                    else:
                    # if get a longer result by target base, set the flag to True
                        cur_result_str = self.base_converter.convert(
                            number=int(cur_result), base=self.longer_result_info.target_base
                        )
                        left_result_str = self.base_converter.convert(
                            number=int(left_result), base=self.longer_result_info.target_base
                        )
                        right_result_str = self.base_converter.convert(
                            number=int(right_result), base=self.longer_result_info.target_base
                        )
                        if len(cur_result_str) > len(left_result_str) and len(
                            cur_result_str
                        ) > len(right_result_str):
                            self.longer_result_info.flag = True

                self.cot_info.append(
                    {
                        "info": f"compute binary expreesion, left_input={left_result}, right_input={right_result}, op_id = {node.operator.func_id} binary_op_definition= '{node.operator.definition}', output={cur_result}",
                        "layer": cot_layer,
                    }
                )
                # prepare for cot
                left_result_str_with_base = self.get_target_base_str(value = left_result,target_base = self.longer_result_info.target_base)
                right_result_str_with_base = self.get_target_base_str(value = right_result,target_base = self.longer_result_info.target_base)
                cur_result_str_with_base = self.get_target_base_str(value = cur_result,target_base = self.longer_result_info.target_base)

                self.cot.append({ "info": f"{left_result_str_with_base}{node.operator.symbol}{right_result_str_with_base}={cur_result_str_with_base}","layer": cot_layer,})
                
                if cur_result !=cur_result or cur_result in special_values:
                    pass
                else:
                    cur_result = int(cur_result)
                return cur_degree + left_degree + right_degree, cur_result
            elif isinstance(node, VariableNode):
                return float("nan"), float("nan")
            else:
                raise NotImplementedError(
                    "ExpressionEvaluator.calculate_normalized_expansion_degree_node"
                )
        except Exception as e:
            # print(f"node: {node.operator.id}")
            if isinstance(node, BinaryExpressionNode):
                self.logger.error(f"Error in ExpressionEvaluator.tree_to_str: {e},cur_result={cur_result},left_result={left_result},right_result={right_result}")
            elif isinstance(node,UnaryExpressionNode):
                self.logger.error(f"Error in ExpressionEvaluator.tree_to_str: {e},cur_result={cur_result},sub_result={sub_result}")
            else:
                self.logger.error(f"Error in ExpressionEvaluator.tree_to_str: {e}")
            raise e

    def calculate_operation_count(self):
        """
        Calculates the total number of operations in the expression.

        This method returns the count of all operations that were encountered during the construction of the expression tree.

        Returns:
            (int): The operation count as an integer.
        """
        # 实现运算次数的计算逻辑
        return self.operation_count
    def all_dependent_operators(self)->List:
        used_ops_func_id = list(self.all_operators.keys())
        dependent_ops = []
        for op_func_id in used_ops_func_id:
            if self.operator_manager.get_operator_by_func_id(op_func_id=op_func_id).dependencies!=None:
                dependent_ops += self.operator_manager.get_operator_by_func_id(op_func_id=op_func_id).dependencies
        return dependent_ops
    
    def number_count(self)->int:
        return self.number_count

    def calculate_complexity_ratio(self):
        """
        Calculates the complexity ratio based on normalized expansion degree and operation count.

        The complexity ratio provides a measure of how complex the expression is relative to the number of operations it contains.
        It is calculated by dividing the normalized expansion degree by the operation count.

        Returns:
            (int): The complexity ratio as a floating-point number. Returns 0 if the operation count is 0 or the expansion degree is "NaN".
        """
        operation_count = self.calculate_operation_count()
        normalized_expansion_degree = self.calculate_normalized_expansion_degree()
        return (
            normalized_expansion_degree / operation_count
            if operation_count > 0 and normalized_expansion_degree != "NaN"
            else 0
        )

    # def calculate_max_digit_count(self):
    #     """
    #     Calculates the maximum digit count in the expression string.

    #     This method extracts all numbers from the expression string, converts them to integers, and determines the length of the largest number.

    #     Returns:
    #         (int): The maximum digit count as an integer. Returns 0 if there are no digits in the expression string.
    #     """
    #     numbers = [int(num) for num in self.expression_str.split() if num.isdigit()]
    #     return max((len(str(num)) for num in numbers), default=0)
    def get_base(self):
        if self.param_config.get("random_base")["flag"]==False:
            return self.param_config.get("random_base")["base"]
        else:
            return None
    def evaluate(self):
        """
        Evaluates the expression and returns its properties.

        This method aggregates various metrics about the expression, such as its highest n-order, hierarchical complexity,
        normalized expansion degree, operation count, complexity ratio, maximum digit count, and result.

        Returns:
            (dict): A dictionary containing various properties of the evaluated expression.
        """
        return {
            "id": self.id,
            "expression_no_base_symbol": self.expression_str_no_base_symbol,
            "expression": self.expression_str,
            "highest_n_order": self.calculate_highest_n_order(),
            "priority_hierarchical_complexity": self.calculate_priority_hierarchical_complexity(),
            "normalized_expansion_degree": self.calculate_normalized_expansion_degree(),
            "operation_count": self.calculate_operation_count(),
            "complexity_ratio": self.calculate_complexity_ratio(),
            # "max_digit_count": self.calculate_max_digit_count(),
            "tree": self.expression_tree.to_dict(),
            "used_operators": list(self.all_operators.keys()),
            "dependent_operators": self.all_dependent_operators(),
            "result": self.calculate_result(),
            "longer_result_info": asdict(self.longer_result_info),
            "cot_info": self.cot_info,
            "base": self.get_base(),
            "result_base": self.expr_result_base,
            "text": f"{self.expression_str}={self.calculate_result()}",
            "cot": self.cot,
        }


# if __name__ == "__main__":
#     # 示例使用
#     from expression.expression_generator import ExpressionGenerator
#     from operatorplus.operator_manager import OperatorManager

#     manager = OperatorManager("data/operator/available_operators.jsonl")
#     expr_generator = ExpressionGenerator("data/operator/available_operators.jsonl")
#     rand_expr_tree = expr_generator.create_expression()
#     # expression = "(3 ⊗ (2 ⊕ 5) ⊖ (4 ⊘ 2)) ⊕ 9"
#     evaluator = ExpressionEvaluator()
#     properties = evaluator.evaluate()
