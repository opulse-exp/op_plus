from lark import Lark, Transformer, v_args, Token, Tree
from config import LogConfig, ParamConfig
from operatorplus.operator_manager import OperatorManager
    
class Simple_Expr_Parser:
    def __init__(self, param_config: ParamConfig, logger: LogConfig):
        # Store the provided param_config and logger
        self.param_config = param_config
        self.logger = logger.get_logger()
        
        # Dynamically construct the grammar using `param_config`
        self.grammar = f"""
        ?start: expr
        ?expr: expr OPERATOR term  -> binary_operation
            | term
        ?term: factor
            | OPERATOR factor      -> unary_operation_prefix
            | factor OPERATOR      -> unary_operation_postfix
        ?factor: "{self.param_config.atoms["nan"]}"          -> no_solution
            | VARIABLE      ->variable_conversion
            | INT           ->int_conversion
            | "{self.param_config.atoms["left_parenthesis"]}" expr "{self.param_config.atoms["right_parenthesis"]}"
        OPERATOR: SYMBOL+
        SYMBOL: "+" | "-" | "*" | "/" | "%" | /[\u2200-\u22FF\u2A00-\u2BFF\u2190-\u21FF]+/
        CONDITION_OPERATOR: "==" | ">" | "<" | ">=" | "<="| "!="
        VARIABLE: /[a-zA-Z]/
        NO_SOLUTION: "{self.param_config.atoms["nan"]}"   
        SEMICOLON: ";"
        %import common.INT
        %import common.WS
        %ignore WS
        """

        # Logging the generated grammar for debugging
        self.logger.debug(f"Generated grammar: {self.grammar}")

        # Initialize the Lark parser with the dynamically generated grammar
        self.parser = Lark(self.grammar, start="start")

        # Log that the parser has been successfully initialized
        self.logger.info("Simple_Expr_Parse initialized successfully.")

    def parse_expr(self, expr):
        try:
            parsed_tree = self.parser.parse(expr)
            self.logger.info("Parsing successful.")
            return parsed_tree
        except Exception as e:
            self.logger.error(f"Error while parsing definition: {e}")
            raise

class Simple_Expr_Transformer(Transformer):
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
            operator, is_unary=False
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
            operator, is_unary=True
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
            operator, is_unary=True
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
    def rule(self, expr):
        """
        Converts an unconditional branch into a tuple.

        Parameters:
            expr (str): The expression for the unconditional branch.

        Returns:
            (tuple): A tuple representing the unconditional branch.
        """
        count_str = "+".join(str(item) for item in self.count_result)
        self.count_result.clear()
        result = (expr, count_str)
        return result

    #对简单函数进行一个组合
    def generate_expr_function_str(self, expr):
        expr_str = self.transform(expr)
        return expr_str