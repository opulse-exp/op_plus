from lark import Lark, Transformer, v_args, Token
import logging
import re
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_logging():
    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning message")

test_logging()

class Calculate(Transformer):
    def __init__(self, op_manager):
        self.op_manager = op_manager
        self.compiled_functions = {}

    def number(self, n):
        if isinstance(n, Token) and n.type == "INT":
            return int(n.value)
        elif isinstance(n, list):
            return n[0]
        else:
            raise ValueError("Unexpected token type")
        
    def __getattr__(self, name):
        logging.debug(f"name: {name}")
        def method(args):
            logging.debug(f"args: {args}")
            pattern = r"^expr_\d+$"
            if name == "INT":
                return self.number(args)
            if bool(re.match(pattern, name)) or name == "start":
                return args[0]

            # 通过运算符的 id 动态查找计算函数
            operator_id = name.split("_")[1] 
            logging.debug(f"operator_id: {operator_id}")
            # 查找运算符
            operator = self.op_manager.get_operator_by_id(int(operator_id))
            if operator:
                if operator.op_compute_func:
                    # 执行运算符的计算函数
                    func_code = operator.op_compute_func
                    compiled_func = self._get_or_compile_function(operator_id, func_code)
                    return compiled_func(*args)
                else:
                    raise ValueError(f"Operator '{operator_id}' does not have a compute function.")
            else:
                raise AttributeError(f"No operator found with id: {operator_id}")

        return method
    
    def _get_or_compile_function(self, operator_id, func_code):
        # Check if the function is already compiled, if not, compile it
        if operator_id not in self.compiled_functions:
            compiled_func = compile(func_code, '<string>', 'exec')
            self.compiled_functions[operator_id] = compiled_func
        else:
            compiled_func = self.compiled_functions[operator_id]

        # Create a global dictionary to execute the code and extract the function
        func_globals = {}
        exec(compiled_func, func_globals)

        # Retrieve the function corresponding to the operator id
        operator_func_name = f"op_{operator_id}"  # Ensure correct function name
        op_func = func_globals.get(operator_func_name)

        if op_func is None:
            raise ValueError(f"Compiled function for operator '{operator_func_name}' is not found.")
        
        return op_func

