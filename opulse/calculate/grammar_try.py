from lark import Transformer, v_args, Token
import re


class GrammarGenerator:
    def __init__(self, op_manager):
        self.op_manager = op_manager

    def generate(self):
        operators = self.op_manager.get_operators_by_priority()
        if len(operators) == 0:
            raise ValueError("len(operators)=0")
        lowest_priority = operators[0]["priority"]

        current_exp_level = -1
        base_grammar = f"""
        start: expr_0 \n
        """

        # 生成运算符规则
        current_priority = None
        pre_priority = None
        for symbol, info in [(op["symbol"], op) for op in operators]:
            # generate grammar
            if info["priority"] != current_priority:
                current_exp_level += 1
                current_priority = info["priority"]
                base_grammar += (
                    f"?expr_{current_exp_level}: expr_{current_exp_level+1}\n"
                )
            if info["n-ary"] == 1:
                if info["unary_position"] == "prefix":
                    base_grammar += f" | \"{info['symbol']}\" expr_{current_exp_level} -> {info['name']}\n"
                elif info["unary_position"] == "suffix":
                    base_grammar += f" | expr_{current_exp_level} \"{info['symbol']}\"  -> {info['name']}\n"
            elif info["n-ary"] == 2:
                if info["associativity"] == "left":
                    base_grammar += f"| expr_{current_exp_level} \"{info['symbol']}\" expr_{current_exp_level+1} -> {info['name']}\n"
                elif info["associativity"] == "right":
                    base_grammar += f"| expr_{current_exp_level+1} \"{info['symbol']}\" expr_{current_exp_level} -> {info['name']}\n"

        # 默认括号有最高的优先级
        base_grammar += (
            f'expr_{current_exp_level+1}: NUMBER   -> number\n   | "(" expr_0 ")" \n '
        )
        base_grammar += """
        %import common.NUMBER
        %import common.WS
        %ignore WS
        """
        return base_grammar


# below is only for test
from lark import Transformer, v_args


class OperatorManager:
    def __init__(self):
        self.operators = []

    def add_operator(
        self,
        symbol,
        name,
        priority,
        associativity,
        compute_func,
        n_ary=2,
        unary_position="null",
    ):
        self.operators.append(
            {
                "symbol": symbol,
                "name": name,
                "priority": priority,
                "associativity": associativity,
                "compute_func": compute_func,
                "n-ary": n_ary,
                "unary_position": unary_position,
            }
        )

    def get_operators(self):
        return self.operators

    def get_operators_by_priority(self):
        return sorted(self.operators, key=lambda x: x["priority"])





class Calculate(Transformer):
    def __init__(self, op_manager):
        self.op_manager = op_manager

    def number(self, n):
        if isinstance(n, Token) and n.type == "NUMBER":
            return int(n.value)
        elif isinstance(n, list):
            return n[0]
        else:
            raise ValueError("Unexpected token type")

    def __getattr__(self, name):
        def method(args):
            pattern = r"^expr_\d+$"
            if name == "NUMBER":
                return self.number(args)
            if bool(re.match(pattern, name)) or name == "start":
                return args[0]
            for op in self.op_manager.get_operators():
                if op["name"] == name:
                    if op["n-ary"] == 1:
                        return op["compute_func"](args[0])
                    else:
                        return op["compute_func"](args[0], args[1])
            raise AttributeError(f"No operator found with name: {name}")

        return method


class number:
    def __call__(self, n):
        return int(n)


class ComplexAddition:
    def __call__(self, a, b):
        result = a + b
        if result > 10:
            return result * 2
        return result


class ComplexMultiplication:
    def __call__(self, a, b):
        return a * b + (a - b)


class ComplexAddition:
    def __call__(self, a, b):
        result = a + b
        if result > 10:
            return result * 2
        return result


class ComplexMultiplication:
    def __call__(self, a, b):
        return a * b + (a - b)


from lark import Lark

if __name__ == "__main__":
    # 创建 OperatorManager 实例
    op_manager = OperatorManager()

    # 添加运算符
    op_manager.add_operator("⊕", "complex_addition", 1, "left", ComplexAddition())
    op_manager.add_operator(
        "⊗", "complex_multiplication", 2, "left", ComplexMultiplication()
    )
    op_manager.add_operator("+", "add", 3, "left", lambda a, b: a + b)
    op_manager.add_operator("-", "sub", 3, "left", lambda a, b: a - b)
    op_manager.add_operator("*", "mul", 4, "left", lambda a, b: a * b)
    op_manager.add_operator("/", "div", 4, "left", lambda a, b: a / b)
    op_manager.add_operator("**", "pow", 5, "right", lambda a, b: a**b)
    op_manager.add_operator("!", "prefix_op", 4, "null", lambda a: -2 * a, 1, "prefix")
    op_manager.add_operator("^", "prefix_op2", 4, "null", lambda a: -2 * a, 1, "prefix")
    op_manager.add_operator("&", "suffix_op", 4, "null", lambda a: 10 * a, 1, "suffix")

    # 生成文法
    grammar = GrammarGenerator(op_manager).generate()

    print(grammar)

    # 初始化计算类并解析表达式
    calc = Calculate(op_manager)
    parser = Lark(grammar, start="start")
    tree = parser.parse("3 ⊕ 4 ⊗ 2 + ! ^ 5 * (10 - 4) / 2 ** 3 ** 4 &")
    print(tree.pretty())
    result = calc.transform(tree)
    print(result)  # 输出结果