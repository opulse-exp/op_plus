from lark import Transformer, v_args, Token, Tree
from operatorplus.operator_manager import OperatorManager
from config import LogConfig, ParamConfig
from z3 import *


class OperatorTransformerZ3(Transformer):
    def __init__(
        self,
        param_config: ParamConfig,
        logger: LogConfig,
        operator_manager: "OperatorManager" = None,
    ):
        """
        Initializes the OperatorTransformer instance with given configurations.

        Args:
           param_config (ParamConfig): Configuration for parameters.
           logger (LogConfig): Logger configuration for logging debug and info messages.
           operator_manager (OperatorManager, optional): Operator manager for handling operators (default: None).
        """
        self.param_config = param_config
        self.logger = logger.get_logger()
        self.operator_manager = operator_manager

    @v_args(inline=True)
    def no_solution(self, token):
        """
        Handles the NO_SOLUTION rule, returns the string 'NaN'.

        Args:
            token (Token): The token representing NO_SOLUTION.

        Returns:
            (str): The string '"NaN"'.
        """
        self.logger.debug(f"Processing NO_SOLUTION: {token}")
        result = '"NaN"'  # Ensure to return 'NaN' as a quoted string.
        self.logger.debug(f"Returning NO_SOLUTION result: {result}")
        return result

    @v_args(inline=True)
    def int_conversion(self, token):
        """
        Converts an INT token to a string.

        Args:
            token (Token): The token representing an integer.

        Returns:
            (str): The string representation of the integer.
        """
        self.logger.debug(f"Converting INT token: {token}")
        result = str(token.value)
        self.logger.debug(f"Returning INT conversion result: {result}")
        return result

    @v_args(inline=True)
    def variable_conversion(self, token):
        """
        Converts a VARIABLE token to its string value.

        Args:
            token (Token): The token representing a variable.

        Returns:
            (str): The string value of the variable.
        """
        self.logger.debug(f"Converting VARIABLE token: {token}")
        result = token.value  # Assumes it's a simple variable name like 'a' or 'b'.
        self.logger.debug(f"Returning VARIABLE conversion result: {result}")
        return result

    @v_args(inline=True)
    def binary_operation(self, left, operator, right):
        """
        Converts a binary operation into a function call.

        Args:
            left (str): The left operand.
            operator (str): The operator symbol.
            right (str): The right operand.

        Returns:
            (str): The function call string.

        Raises:
            ValueError: If the operator is not supported or lacks a function ID.
        """
        self.logger.debug(
            f"Binary operation: left={left}, operator={operator}, right={right}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=False
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}_z3({left},{right})"
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning binary operation result: {result}")
        return result

    @v_args(inline=True)
    def unary_operation_prefix(self, operator, operand):
        """
        Converts a prefix unary operation into a function call.

        Args:
            operator (str): The operator symbol.
            operand (str): The operand.

        Returns:
            (str): The function call string.

        Raises:
            ValueError: If the operator is not supported or lacks a function ID.
        """
        self.logger.debug(
            f"Prefix unary operation: operator={operator}, operand={operand}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=True
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}_z3({operand})"
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning prefix unary operation result: {result}")
        return result

    @v_args(inline=True)
    def unary_operation_postfix(self, operand, operator):
        """
        Converts a postfix unary operation into a function call.

        Args:
            operand (str): The operand.
            operator (str): The operator symbol.

        Returns:
            (str): The function call string.

        Raises:
            ValueError: If the operator is not supported or lacks a function ID.
        """
        self.logger.debug(
            f"Postfix unary operation: operand={operand}, operator={operator}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=True
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}_z3({operand})"
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning postfix unary operation result: {result}")
        return result

    @v_args(inline=True)
    def grouped_condition(self, condition):
        """
        Wraps a condition in parentheses.

        Args:
            condition (str): The condition to be grouped.

        Returns:
            (str): The condition wrapped in parentheses.
        """
        self.logger.debug(f"Processing grouped condition: {condition}")
        result = f"({condition})"
        self.logger.debug(f"Returning grouped condition result: {result}")
        return result

    @v_args(inline=True)
    def comparison(self, left, condition_operator, right):
        """
        Converts a comparison expression into a string representation.

        Args:
            left (str): The left operand.
            condition_operator (str): The comparison operator.
            right (str): The right operand.

        Returns:
            (str): The comparison expression string.
        """
        self.logger.debug(
            f"Processing comparison: left={left}, operator={condition_operator}, right={right}"
        )
        result = f"{left} {condition_operator} {right}"
        self.logger.debug(f"Returning comparison result: {result}")
        return result

    @v_args(inline=True)
    def not_condition(self, condition):
        """
        Wraps the condition with a 'Not' operator.

        Args:
            condition (str): The condition to be negated.

        Returns:
            (str): The negated condition string.
        """
        self.logger.debug(f"Processing 'not' condition: {condition}")
        result = f"Not({condition})"
        self.logger.debug(f"Returning 'not' condition result: {result}")
        return result

    @v_args(inline=True)
    def and_condition(self, left, right):
        """
        Converts an 'And' condition into a string representation.

        Args:
            left (str): The left condition.
            right (str): The right condition.

        Returns:
            (str): The 'And' condition string.
        """
        self.logger.debug(f"Processing 'and' condition: left={left}, right={right}")
        result = f"And({left}, {right})"
        self.logger.debug(f"Returning 'and' condition result: {result}")
        return result

    @v_args(inline=True)
    def or_condition(self, left, right):
        """
        Converts an 'Or' condition into a string representation.

        Args:
            left (str): The left condition.
            right (str): The right condition.

        Returns:
            (str): The 'Or' condition string.
        """
        self.logger.debug(f"Processing 'or' condition: left={left}, right={right}")
        result = f"Or({left}, {right})"
        self.logger.debug(f"Returning 'or' condition result: {result}")
        return result

    @v_args(inline=True)
    def if_branch(self, expr, condition):
        """
        Converts an 'if' branch into a tuple.

        Args:
            expr (str): The expression for the 'if' branch.
            condition (str): The condition for the 'if' branch.

        Returns:
            (tuple): A tuple representing the 'if' branch.
        """
        self.logger.debug(f"Processing 'if' branch: expr={expr}, condition={condition}")
        result = ("if_branch", expr, condition)
        self.logger.debug(f"Returning 'if' branch result: {result}")
        return result

    @v_args(inline=True)
    def else_branch(self, expr):
        """
        Converts an 'else' branch into a tuple.

        Args:
            expr (str): The expression for the 'else' branch.

        Returns:
            (tuple): A tuple representing the 'else' branch.
        """
        self.logger.debug(f"Processing 'else' branch: expr={expr}")
        result = ("else_branch", expr)
        self.logger.debug(f"Returning 'else' branch result: {result}")
        return result

    @v_args(inline=True)
    def unconditional_branch(self, expr):
        """
        Converts an unconditional branch into a tuple.

        Args:
            expr (str): The expression for the unconditional branch.

        Returns:
            (tuple): A tuple representing the unconditional branch.
        """
        self.logger.debug(f"Processing unconditional branch: expr={expr}")
        result = ("unconditional_branch", expr)
        self.logger.debug(f"Returning unconditional branch result: {result}")
        return result

    @v_args(inline=True)
    def rhs_expr(self, *args):
        """
        Processes the right-hand side expressions.

        Args:
            *args: Variable length argument list of expressions.

        Returns:
            (list): The list of filtered right-hand side expressions.
        """
        self.logger.debug(f"Processing rhs_expr with args: {args}")
        filtered_rhs_expr = [
            item
            for item in args
            if not isinstance(item, Token) or item.type != "SEMICOLON" and item
        ]
        self.logger.debug(f"Filtered rhs_expr: {filtered_rhs_expr}")
        result = filtered_rhs_expr
        self.logger.debug(f"Returning rhs_expr result: {result}")
        return result

    def extract_rhs_expr(self, parsed_tree):
        """
        Extracts the rhs_expr part from the parsed tree.

        Args:
           parsed_tree (Tree): The root of the parsed syntax tree.

        Returns:
            (Tree): The subtree corresponding to rhs_expr, or None if not found.
        """
        self.logger.debug(f"Extracting rhs_expr from parsed tree.")
        for child in parsed_tree.children:
            if isinstance(child, Tree) and child.data == "rhs_expr":
                return child
        return None  # Return None if rhs_expr is not found

    def convert_to_z3_expr(exprs, func_unary):
        """
        Converts lists of expressions into nested Z3 expressions, with support for unary and binary conditions.

        Args:
           exprs (list[str]): list of expressions, e.g. [('if_branch', expr, condition), ...].
           is_unary (bool): whether or not it is a unary operator, if True then it handles unary operators, if False then it handles binary operators
        
        Returns: 
            (str): Generated nested Z3 expression.
        """
        if func_unary == 1:
            current_expr = "If(a == NaN, None)"  
        elif func_unary == 2:
            current_expr = "If(Or(a == NaN, b == NaN), NaN, None)"  

        # 遍历表达式列表
        for _, expr, condition in exprs:
            if condition is not None:
                current_expr = current_expr.replace("None", f"If({condition}, {expr}, None)")
            else:
                current_expr = current_expr.replace("None", expr)

        return current_expr


#     def generate_z3_function(self, func_id, func_unary, parsed_definition):
#         """Generate and save the function code from the parsed definition."""

#         # 假设你从 parsed_definition 中提取右侧表达式
#         rhs_tree = self.extract_rhs_expr(parsed_definition)
#         filtered_rhs_expr = self.transform(rhs_tree)

#         # 基本定义
#         z3_func_name = f"op_{func_id}_z3"

#         if func_unary == 1:
#             params = ["a"]
#         elif func_unary == 2:
#             params = ["a", "b"]

#         # 生成函数签名
#         z3_func_def = f"def {z3_func_name}({', '.join(params)}):\n"

#         indent = "    "

#         convert_to_z3_expr(exprs, is_unary=True)

#         z3_func_def += f"{indent}return {z3_func_code}\n"

#         # 打印生成的 Python 和 Z3 函数
#         self.logger.debug(f"Generated Compute function:\n{func_def}")
#         self.logger.debug(f"Generated Count function:\n{count_func_def}")
#         self.logger.debug(f"Generated Z3 function:\n{z3_func_def}")

#         return func_def, count_func_def, z3_func_def


# if __name__ == "__main__":
#     param_config = ParamConfig("config/param_config.json")
#     log_config = LogConfig("config/log_config.json")

#     operator_transformer = OperatorTransformer(param_config, log_config)
