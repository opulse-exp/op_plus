from expression.base_converter import BaseConverter
from operatorplus.operator_manager import OperatorManager
import re


class ExpressionBaseConverter:
    # def __init__(self, input_base: int = 10, output_base: int = 10):
    #     """
    #     Initializes the ExpressionBaseConverter class and sets the base for input and output.

    #     :param input_base: Enter the base of the expression, which defaults to decimal (10).
    #     :param output_base: The base of the output expression, defaults to decimal (10).
    #     """
    #     self.input_base = input_base
    #     self.output_base = output_base
    @staticmethod
    def convert_int_to_targetbase(
        input: int,
        output_base: int,
        base_converter: BaseConverter,
        operator_manager: OperatorManager,
    ) -> str:
        op_info = operator_manager.base_operators[output_base]
        # only for debugging
        if len(op_info) == 0:
            return f"{input}"
        assert len(op_info) == 1
        return f"{op_info[0].symbol}{base_converter.convert(input, output_base)}"

    @staticmethod
    def convert_expr_str_to_targetbase(
        expression: str,
        output_base: int,
        base_converter: BaseConverter,
        operator_manager: OperatorManager,
    ) -> str:
        """
        Converts all decimal digits surrounded by $ in the expression to the target base and removes the $ sign.

        This static method takes a mathematical expression string where numbers are marked with dollar signs ($),
        converts those numbers from decimal to the specified target base, and returns a new string with the updated numbers.
        The conversion is performed using the provided BaseConverter instance.

        Args:
            expression (str): The original math expression string containing numbers marked with $...$.
            output_base (int): The target base to which the numbers should be converted.
            base_converter (BaseConverter): An instance of BaseConverter used for converting between bases.

        Returns:
            str: A new math expression string with numbers converted to the target base and without the $ sign.

        Example:
            Given an expression "$100$ + $25$" and output_base 2,
            the returned string would be "1100100 + 11001".
        """

        def replacer(match):
            decimal_str = match.group(1)
            decimal_num = int(decimal_str)
            converted_str = base_converter.convert(decimal_num, output_base)
            return converted_str

        # 使用正则表达式替换所有匹配的部分
        pattern = r"\$(\d+)\$"
        new_expression = re.sub(pattern, replacer, expression)
        return new_expression


# 示例使用
# if __name__ == "__main__":
#     expr = "$5$+$4$"  # 输入表达式
#     target_base = 16  # 目标基数（例如十六进制）

#     try:
#         converted_expr = ExpressionBaseConverter.replace_decimal_with_base(
#             expr, target_base
#         )
#         print(f"Converted expression: {converted_expr}")
#     except ValueError as e:
#         print(e)
