class GrammarGenerator:
    def __init__(self, op_manager):
        self.op_manager = op_manager

    def generate(self):
        operators = self.op_manager.get_operators_by_priority()
        if len(operators) == 0:
            raise ValueError("len(operators)=0")

        current_exp_level = -1
        base_grammar = f"""
        start: expr_0 \n
        """

        current_priority = None
        for op in operators:
            info = op  # 操作符信息

            # 根据优先级动态生成表达式规则
            if info.priority != current_priority:
                current_exp_level += 1
                current_priority = info.priority
                base_grammar += (
                    f"?expr_{current_exp_level}: expr_{current_exp_level+1}\n"
                )

            # 根据运算符的 n_ary 属性生成文法规则
            if info.n_ary == 1:  # 单目运算符
                if info.unary_position == "prefix":
                    base_grammar += f" | \"{info.symbol}\" expr_{current_exp_level} -> op_{info.id}\n"
                elif info.unary_position == "postfix":
                    base_grammar += f" | expr_{current_exp_level} \"{info.symbol}\" -> op_{info.id}\n"
            elif info.n_ary == 2:  # 二目运算符
                if info.associativity_direction == "left":
                    base_grammar += f"| expr_{current_exp_level} \"{info.symbol}\" expr_{current_exp_level+1} -> op_{info.id}\n"
                elif info.associativity_direction == "right":
                    base_grammar += f"| expr_{current_exp_level+1} \"{info.symbol}\" expr_{current_exp_level} -> op_{info.id}\n"

        # 默认括号有最高的优先级
        base_grammar += (
            f'expr_{current_exp_level+1}: INT ->number\n   | "(" expr_0 ")" \n '
        )
        base_grammar += """
        %import common.INT
        %import common.WS
        %ignore WS
        """
        return base_grammar

