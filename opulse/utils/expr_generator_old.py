import random
from typing import List
from operatorplus.operator_info import OperatorInfo
from operatorplus.operator_manager import OperatorManager

from typing import List, Dict
import random

"""
    TODO:Not thinking about conversions yet?
    TODO:The simplification of expressions should be solved using the sympy library
    #call
"""


class ExprGenerator:
    def __init__(
        self,
        variables: List[str] = None,
        operator_manager: "OperatorManager" = None,
        min_value: int = -10,
        max_value: int = 10,
        max_depth: int = 5,
        expr_type_weights: Dict[str, float] = None,
        term_type_weights: Dict[str, float] = None,
    ):
        """
        Initialize the expression generator.

        Parameters:
            variables (List[str]): list of variables.
            operator_manager: Manage instances of the operator.
            min_value (int): Minimum value of a random integer.
            max_value (int): Maximum value of a random integer.
            max_depth (int): Maximum recursion depth.
            expr_type_weights (Dict[str, float]): Probability distribution of expression type selection.
            term_type_weights (Dict[str, float]): probability distribution of term type selection.
        """
        self.variables = variables or ["a", "b"]
        self.operator_manager = operator_manager
        self.min_value = min_value
        self.max_value = max_value
        self.max_depth = max_depth

        # 设置表达式类型的概率分布，若未传入则使用默认值
        self.expr_type_weights = expr_type_weights or {
            "binary": 0.4,
            "unary": 0.4,
            "term": 0.2,
            "NaN": 0.05,
        }

        # 设置 term 类型的概率分布，若未传入则使用默认值
        self.term_type_weights = term_type_weights or {
            "variable": 0.4,
            "integer": 0.4,
            "grouped_expr": 0.15,
        }

    def set_variables(self, new_variables: List[str]):
        """
        Sets the new value of the variable list.
        
        Parameters:
            new_variables (List[str]): New list of variable names.
        """
        self.variables = new_variables

    def generate_expression(self, depth=0):
        """
        Generates an expression that conforms to the grammar. The depth of the expression increases according to the recursive generation rules.
        
        Parameters:
            depth (int): Current recursion depth.

        Returns:
            (str): The generated expression string.
        """
        if depth > self.max_depth:
            return self.generate_term(depth)

        # 根据 expr_type_weights 确定表达式类型
        expr_type = random.choices(
            ["binary", "unary", "term", "NaN"],
            weights=[
                self.expr_type_weights["binary"],
                self.expr_type_weights["unary"],
                self.expr_type_weights["term"],
                self.expr_type_weights["NaN"],
            ],
        )[0]

        # 如果 expr_type 是 "NaN"，直接返回 NaN，不再生成其他表达式
        if expr_type == "NaN":
            return "NaN"
        elif expr_type == "binary":
            return self.generate_binary_expression(depth + 1)
        elif expr_type == "unary":
            return self.generate_unary_expression(depth + 1)
        else:
            return self.generate_term(depth)

    def generate_binary_expression(self, depth):
        """
        Generates a binary expression using available binary operators.

        Parameters:
            depth (int): Current recursion depth.

        Returns:
            (str): The generated binary expression string.
        """
        _, _, binary_ops = self.operator_manager.get_unary_and_binary_operators()

        # 生成左右表达式
        left = self.generate_expression(depth)
        if left == "NaN":
            return "NaN"  # 如果左侧是 NaN，整个表达式变为 NaN

        right = self.generate_expression(depth)
        if right == "NaN":
            return "NaN"  # 如果右侧是 NaN，整个表达式变为 NaN

        # 否则生成二元表达式
        operator = random.choice(binary_ops).symbol
        return f"({left} {operator} {right})"

    def generate_unary_expression(self, depth):
        """
        Generates a unary expression using available unary prefix or postfix operators.

        Parameters:
            depth (int): Current recursion depth.

        Returns:
            (str): The generated unary expression string.
        """
        unary_prefix_ops, unary_postfix_ops, _ = (
            self.operator_manager.get_unary_and_binary_operators()
        )

        # 生成基本项
        factor = self.generate_term(depth)
        if factor == "NaN":
            return "NaN"  # 如果基本项是 NaN，则整个表达式变为 NaN

        # 随机选择前缀或后缀运算符
        if unary_prefix_ops and (
            not unary_postfix_ops or random.choice(["prefix", "postfix"]) == "prefix"
        ):
            operator = random.choice(unary_prefix_ops).symbol
            return f"({operator}{factor})"
        elif unary_postfix_ops:
            operator = random.choice(unary_postfix_ops).symbol
            return f"({factor}{operator})"
        else:
            return factor

    def generate_term(self, depth):
        """
        Generates a basic term, which can be a variable, an integer, or a grouped expression.

        Parameters:
            depth (int): Current recursion depth.

        Returns:
            (str): The generated term string.
        """
        term_type = random.choices(
            ["variable", "integer", "grouped_expr"],
            weights=[
                self.term_type_weights["variable"],
                self.term_type_weights["integer"],
                self.term_type_weights["grouped_expr"],
            ],
        )[0]

        if term_type == "variable":
            return self.generate_variable()
        elif term_type == "integer":
            return str(random.randint(self.min_value, self.max_value))
        else:
            # 检查生成的子表达式是否包含 "NaN"，如果包含则直接返回 "NaN"
            grouped_expr = self.generate_expression(depth + 1)
            return "NaN" if "NaN" in grouped_expr else f"({grouped_expr})"

    def generate_variable(self):
        """
        Randomly selects and returns a variable from the list.

        Returns:
            (str): A randomly selected variable name.
        """
        return random.choice(self.variables)


if __name__ == "__main__":
    # 初始化 ConditionGenerator 时使用单变量 'a'
    variables = ["a"]
    operator_manager = OperatorManager(
        config_file="op+/data/operator/initial_operators.jsonl"
    )

    expr_generator = ExprGenerator(
        variables=variables, operator_manager=operator_manager
    )

    # 生成条件表达式
    for _ in range(10):
        expr = expr_generator.generate_expression()
        print(f"生成的表达式（仅 'a' 变量）: {expr}")
        print("-" * 50)

    # 更新变量列表为 'a' 和 'b'
    expr_generator.set_variables(["a", "b"])
    for _ in range(10):
        expr = expr_generator.generate_expression()
        print(f"生成的表达式（'a' 和 'b' 变量）: {expr}")
        print("-" * 50)
