from operatorplus.operator_info import OperatorInfo
from operatorplus.operator_manager import OperatorManager
from expression.base_converter import BaseConverter
from expression.expression_base_converter import ExpressionBaseConverter


class ExpressionNode:
    def __init__(self):
        """
        Initializes a basic expression node with a position attribute.
        """
        self.position = None

    def to_dict(self):
        """
        Abstract method to convert the node to a dictionary representation.
        Subclasses should implement this method.
        """
        raise NotImplementedError("Subclasses should implement this method")


class NumberNode(ExpressionNode):
    def __init__(self, value: int, base: int = 10):
        """
        Initializes a number node with a value and an optional base.

        Args:
            value (int): The numeric value of the node.
            base (int): The base of the number (default is 10).
        """
        super().__init__()
        self.value = value
        self.base = base

    def to_dict(self):
        """
        Converts the number node to a dictionary representation.

        Returns
            (dict): A dictionary with the node's type, value, and base.
        """
        return {"type": "numeric_atoms", "value": self.value, "base": self.base}

    def to_str_no_base_symbol(self, surround_symbol: str = None):
        """
        Converts the node's value to a string without base symbols.

        Args:
           surround_symbol: The symbol surrounding the value.

        Returns:
            (str): A string representation of the value.
        """
        if surround_symbol:
            return f"{surround_symbol}{self.value}{surround_symbol}"
        else:
            return f"{self.value}"

    def to_str(self, operator_manager: OperatorManager, base_converter: BaseConverter):
        """
        Converts the node's value to a string with base symbols.

        Args:
           operator_manager (OperatorManager): The operator manager to get base operators.
           base_converter (BaseConverter): The base converter to convert the value.

        Returns:
            (str): A string representation of the value with base symbols.

        Raises:
            ValueError: If base_converter is None.
        """
        return ExpressionBaseConverter.convert_int_to_targetbase(
            input=self.value,
            output_base=self.base,
            base_converter=base_converter,
            operator_manager=operator_manager,
        )
        # pass


class VariableNode(ExpressionNode):
    def __init__(self, variable: str):
        """
        Initializes a variable node with a variable name.

        Args:
           variable (str): The name of the variable.
        """
        super().__init__()
        self.v = variable

    def to_dict(self):
        """
        Converts the variable node to a dictionary representation.

        Returns:
            (dict): A dictionary with the node's type and variable name.
        """
        return {
            "type": "variable",
            "variable": self.v,
        }


class BinaryExpressionNode(ExpressionNode):
    def __init__(self, operator: OperatorInfo):
        """
        Initializes a binary expression node with an operator.

        Args:
           operator (OperatorInfo): The operator information for the expression.
        """
        super().__init__()
        self.left_expr: ExpressionNode = None
        self.right_expr: ExpressionNode = None
        self.operator = operator

    def to_dict(self):
        """
        Converts the binary expression node to a dictionary representation.

        Returns:
            (dict): A dictionary with the node's type, operator, and child expressions.
        """
        return {
            "type": "binary",
            "operator": self.operator.symbol,
            "left_expr": self.left_expr.to_dict(),
            "right_expr": self.right_expr.to_dict(),
        }


class UnaryExpressionNode(ExpressionNode):
    def __init__(self, operator: OperatorInfo):
        """
        Initializes a unary expression node with an operator.

        Args:
            operator (OperatorInfo): The operator information for the expression.
        """
        super().__init__()
        self.operator = operator
        self.unary_expr: ExpressionNode = None

    def to_dict(self):
        """
        Converts the unary expression node to a dictionary representation.

        Returns:
            (dict): A dictionary with the node's type, operator, and unary expression.
        """
        return {
            "type": "unary",
            "operator": self.operator.symbol,
            "unary_expr": self.unary_expr.to_dict(),
        }
