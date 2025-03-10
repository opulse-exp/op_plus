from lark import Transformer, v_args, Token, Tree
from operatorplus.operator_manager import OperatorManager
from config import LogConfig, ParamConfig
import re
import numba

class OperatorTransformer(Transformer):
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
           operator_manager (OperatorManager, optional): Operator manager for handling operators.
        """
        self.param_config = param_config
        self.logger = logger.get_logger()
        self.operator_manager = operator_manager
        self.count_result = []

    @v_args(inline=True)
    def no_solution(self, token):
        """
        Handles the NO_SOLUTION rule, returns the string 'NaN'.

        Parameters:
            token (Token): The token representing NO_SOLUTION.

        Returns:
            (str): The string '"NaN"'.
        """
        self.logger.debug(f"Processing NO_SOLUTION: {token}")
        result = float('nan')  # Ensure to return 'NaN' as a quoted string.
        self.logger.debug(f"Returning NO_SOLUTION result: {result}")
        return result

    @v_args(inline=True)
    def int_conversion(self, token):
        """
        Converts an INT token to a string.

        Parameters:
            token (Token): The INT token to convert.

        Returns:
            (str): The string representation of the token's value.
        """
        self.logger.debug(f"Converting INT token: {token}")
        result = str(token.value)
        self.logger.debug(f"Returning INT conversion result: {result}")
        return result

    @v_args(inline=True)
    def variable_conversion(self, token):
        """
        Converts a VARIABLE token to its string value.

        Parameters:
            token (Token): The VARIABLE token to convert.

        Returns:
            (str): The string representation of the token's value.
        """
        self.logger.debug(f"Converting VARIABLE token: {token}")
        result = token.value  # Assumes it's a simple variable name like 'a' or 'b'.
        self.logger.debug(f"Returning VARIABLE conversion result: {result}")
        return result

    @v_args(inline=True)
    def binary_operation(self, left, operator, right):
        """
        Converts a binary operation into a function call.

        Parameters:
            left (str): The left operand.
            operator (str): The operator symbol.
            right (str): The right operand.

        Returns:
            (str): The function call string using the operator's function ID.
        """
        self.logger.debug(
            f"Binary operation: left={left}, operator={operator}, right={right}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=False, unary_position="null"
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({left},{right})"
            count_result = f"op_count_{func_id}({left},{right})"
            self.count_result.append(count_result)
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning binary operation result: {result}")
        self.logger.debug(f"self.count_result: {self.count_result}")
        return result

    @v_args(inline=True)
    def unary_operation_prefix(self, operator, operand):
        """
        Converts a prefix unary operation into a function call.

        Parameters:
            operator (str): The operator symbol.
            operand (str): The operand.

        Returns:
            (str): The function call string using the operator's function ID.
        """
        self.logger.debug(
            f"Prefix unary operation: operator={operator}, operand={operand}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=True, unary_position="prefix"
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({operand})"
            count_result = f"op_count_{func_id}({operand})"
            self.count_result.append(count_result)
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning prefix unary operation result: {result}")
        self.logger.debug(f"self.count_result: {self.count_result}")
        return result

    @v_args(inline=True)
    def unary_operation_postfix(self, operand, operator):
        """
        Converts a postfix unary operation into a function call.

        Parameters:
            operand (str): The operand.
            operator (str): The operator symbol.

        Returns:
            (str): The function call string using the operator's function ID.
        """
        self.logger.debug(
            f"Postfix unary operation: operand={operand}, operator={operator}"
        )
        func_id, is_temporary = self.operator_manager.get_operator_function_id(
            operator, is_unary=True, unary_position="postfix"
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({operand})"
            count_result = f"op_count_{func_id}({operand})"
            self.count_result.append(count_result)
        else:
            raise ValueError(
                f"Operator '{operator}' is not supported or lacks a function ID."
            )
        self.logger.debug(f"Returning postfix unary operation result: {result}")
        self.logger.debug(f"self.count_result: {self.count_result}")
        return result

    @v_args(inline=True)
    def grouped_condition(self, condition):
        """
        Wraps a condition in parentheses.

        Parameters:
            condition (str): The condition to wrap.

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

        Parameters:
            left (str): The left operand.
            condition_operator (str): The comparison operator.
            right (str): The right operand.

        Returns:
            (str): The comparison expression as a string.
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
        Wraps the condition with a 'not' operator.

        Parameters:
            condition (str): The condition to negate.

        Returns:
            (str): The negated condition as a string.
        """
        self.logger.debug(f"Processing 'not' condition: {condition}")
        result = f"not ({condition})"
        self.logger.debug(f"Returning 'not' condition result: {result}")
        return result

    @v_args(inline=True)
    def and_condition(self, left, right):
        """
        Converts an 'and' condition into a string representation.

        Parameters:
            left (str): The left operand.
            right (str): The right operand.

        Returns:
            (str): The 'and' condition as a string.
        """
        self.logger.debug(f"Processing 'and' condition: left={left}, right={right}")
        result = f"{left} and {right}"
        self.logger.debug(f"Returning 'and' condition result: {result}")
        return result

    @v_args(inline=True)
    def or_condition(self, left, right):
        """
        Converts an 'or' condition into a string representation.

        Parameters:
            left (str): The left operand.
            right (str): The right operand.

        Returns:
            (str): The 'or' condition as a string.
        """
        self.logger.debug(f"Processing 'or' condition: left={left}, right={right}")
        result = f"{left} or {right}"
        self.logger.debug(f"Returning 'or' condition result: {result}")
        return result

    @v_args(inline=True)
    def if_branch(self, expr, condition):
        """
        Converts an 'if' branch into a tuple.

        Parameters:
            expr (str): The expression for the if branch.
            condition (str): The condition for the if branch.

        Returns:
            (tuple): A tuple representing the if branch.
        """
        self.logger.debug(f"Processing 'if' branch: expr={expr}, condition={condition}")
        count_str = "+".join(str(item) for item in self.count_result)
        self.count_result.clear()
        result = ("if_branch", expr, condition, count_str)
        self.logger.debug(f"Returning 'if' branch result: {result}")
        return result

    @v_args(inline=True)
    def else_branch(self, expr):
        """
        Converts an 'else' branch into a tuple.

        Parameters:
            expr (str): The expression for the else branch.

        Returns:
            (tuple): A tuple representing the else branch.
        """
        self.logger.debug(f"Processing 'else' branch: expr={expr}")
        count_str = "+".join(str(item) for item in self.count_result)
        self.count_result.clear()
        result = ("else_branch", expr, count_str)
        self.logger.debug(f"Returning 'else' branch result: {result}")
        return result

    @v_args(inline=True)
    def unconditional_branch(self, expr):
        """
        Converts an unconditional branch into a tuple.

        Parameters:
            expr (str): The expression for the unconditional branch.

        Returns:
            (tuple): A tuple representing the unconditional branch.
        """
        self.logger.debug(f"Processing unconditional branch: expr={expr}")
        count_str = "+".join(str(item) for item in self.count_result)
        self.count_result.clear()
        result = ("unconditional_branch", expr, count_str)
        self.logger.debug(f"Returning unconditional branch result: {result}")
        return result

    @v_args(inline=True)
    def rhs_expr(self, *args) -> list:
        """
        Processes the right-hand side expressions, filtering out semicolons and empty items.

        Parameters:
            *args: Variadic arguments representing the expressions.

        Returns:
            (list): The filtered list of right-hand side expressions.
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

    def generate_function(self, func_id, func_unary, parsed_definition):
        """
        Generates and saves the function code from the parsed definition.

        Parameters:
            func_id (int): The function ID.
            func_unary (int): Indicates if the function is unary (1) or binary (2).
            parsed_definition (Tree): The parsed definition tree.

        Returns:
            (tuple): A tuple containing the compute function definition and the count function definition as strings.
        """
        rhs_tree = self.extract_rhs_expr(parsed_definition)
        filtered_rhs_expr = self.transform(rhs_tree)

        func_name = f"op_{func_id}"
        count_func_name = f"op_count_{func_id}"
        if func_unary == 1:
            params = ["a"]
        elif func_unary == 2:
            params = ["a", "b"]

        # func_head=f"@numba.jit(nopython=True)\n"
        func_def = f"def {func_name}({', '.join(params)}):\n"
        count_func_def = f"def {count_func_name}({', '.join(params)}):\n"
        indent = "    "

        # if func_unary == 1:
        #     nan_check = f"{indent}if {params[0]} in special_values:\n{indent*2}return 1\n"
        # elif func_unary == 2:
        #     nan_check = f"{indent}if {params[0]} in special_values or {params[1]} in special_values:\n{indent*2}return 1\n"

        # count_func_def += nan_check

        for i, branch in enumerate(filtered_rhs_expr):
            branch_type = branch[0]
            if branch_type == "if_branch":
                _, expr, condition, count_str = branch

                # condition = add_nan_check_to_conditions(condition)
                
                #Because of the previous judgement on NaN, all are elif
                if i == 0:
                    func_def += f"{indent}if {condition}:\n"
                    count_func_def += f"{indent}if {condition}:\n"
                else:
                    func_def += f"{indent}elif {condition}:\n"
                    count_func_def += f"{indent}elif {condition}:\n"

                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}count = 1\n"
                else:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}count = {count_str}\n"

            elif branch_type == "else_branch":
                _, expr,count_str = branch
                func_def += f"{indent}else:\n"
                count_func_def += f"{indent}else:\n"

                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}count = 1\n"
                else:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}count = {count_str}\n"

            elif branch_type == "unconditional_branch":
                _, expr,count_str = branch
                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent}return {expr}\n"
                    count_func_def += (
                        f"{indent}count = 1\n"
                    )
                else:
                    func_def += f"{indent}return {expr}\n"
                    count_func_def += f"{indent}count = {count_str}\n"
        count_func_def += f"{indent}return count\n"
        self.logger.debug(f"Generated Compute function:\n{func_def}")
        self.logger.debug(f"Generated Count function:\n{count_func_def}")

        return func_def, count_func_def

