from lark import Transformer, v_args, Token, Tree
from operatorplus.operator_manager import OperatorManager
from config import LogConfig, ParamConfig
import re

def add_nan_check_to_conditions(condition):
    # Regular expression to match op_xx(a, b) or op_xx(a)
    pattern = re.compile(r'op_(\d+)\(([^)]+)\)')

    # List to store NaN checks
    nan_checks = []

    # Step 1: Extract all the matching op_xx(a) or op_xx(a, b) instances
    matches = re.findall(pattern, condition)

    # Step 2: Generate NaN checks for each match
    for match in matches:
        func_id = match[0]  # op_xx
        params = match[1]    # a or a,b

        # If there is only one parameter (e.g., op_41(a)), directly check this parameter
        if ',' not in params:
            nan_checks.append(f"op_{func_id}({params}) != 'NaN'")
        # If there are two parameters (e.g., op_4(a, 591)), handle them separately
        else:
            a, b = params.split(',')
            nan_checks.append(f"op_{func_id}({a},{b}) != 'NaN'")

    if matches == None:
        final_condition = f"{condition}"
    else:
        # Step 3: Create the NaN check group
        nan_check_group = ' and '.join(nan_checks)

        # Step 4: Replace the condition with NaN checks added before the original condition
        final_condition = f"({nan_check_group}) and ({condition})"

    return final_condition

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
        result = '"NaN"'  # Ensure to return 'NaN' as a quoted string.
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
            operator, is_unary=False
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({left},{right})"
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
            operator, is_unary=True
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({operand})"
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
            operator, is_unary=True
        )
        self.logger.debug(f"Function ID: {func_id}, Is temporary: {is_temporary}")
        if func_id and not is_temporary:
            result = f"op_{func_id}({operand})"
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
        result = ("if_branch", expr, condition)
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
        result = ("else_branch", expr)
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
        result = ("unconditional_branch", expr)
        self.logger.debug(f"Returning unconditional branch result: {result}")
        return result

    @v_args(inline=True)
    def rhs_expr(self, *args):
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

        func_def = f"def {func_name}({', '.join(params)}):\n"
        count_func_def = f"def {count_func_name}({', '.join(params)}):\n"
        indent = "    "

        if func_unary == 1:
            nan_check = f"{indent}if {params[0]} == 'NaN':\n{indent*2}return 'NaN'\n"
        elif func_unary == 2:
            nan_check = f"{indent}if {params[0]} == 'NaN' or {params[1]} == 'NaN':\n{indent*2}return 'NaN'\n"

        func_def += nan_check
        count_func_def += nan_check

        for _, branch in enumerate(filtered_rhs_expr):
            branch_type = branch[0]
            if branch_type == "if_branch":
                _, expr, condition = branch

                condition = add_nan_check_to_conditions(condition)
                
                #Because of the previous judgement on NaN, all are elif
                func_def += f"{indent}elif {condition}:\n"
                count_func_def += f"{indent}elif {condition}:\n"

                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}return 1\n"
                else:
                    func_def += f"{indent*2}return {expr}\n"
                    count_expr = expr.replace("op_", "op_count_")
                    count_func_def += f"{indent*2}return {count_expr}\n"

            elif branch_type == "else_branch":
                _, expr = branch
                func_def += f"{indent}else:\n"
                count_func_def += f"{indent}else:\n"

                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent*2}return {expr}\n"
                    count_func_def += f"{indent*2}return 1\n"
                else:
                    func_def += f"{indent*2}return {expr}\n"
                    count_expr = expr.replace("op_", "op_count_")
                    count_func_def += f"{indent*2}return {count_expr}\n"

            elif branch_type == "unconditional_branch":
                _, expr = branch
                if isinstance(expr, int) or expr in ["a", "b"]:
                    func_def += f"{indent}return {expr}\n"
                    count_func_def += (
                        f"{indent}return 1\n"
                    )
                else:
                    func_def += f"{indent}return {expr}\n"
                    count_expr = expr.replace("op_", "op_count_")
                    count_func_def += f"{indent}return {count_expr}\n"

        self.logger.debug(f"Generated Compute function:\n{func_def}")
        self.logger.debug(f"Generated Count function:\n{count_func_def}")

        return func_def, count_func_def

