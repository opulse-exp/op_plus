import random
from operatorplus.operator_definition_parser import OperatorDefinitionParser
from operatorplus.operator_manager import OperatorManager
from operatorplus.condition_generator import ConditionGenerator
from operatorplus.operator_info import OperatorInfo
from expression.expression_generator import ExpressionGenerator
from operatorplus.operator_transformer import OperatorTransformer
from typing import Dict, List, Optional, Any
from config import LogConfig, ParamConfig
from config.constants import thres
from nanoid import generate
alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class OperatorGenerator:
    def __init__(
        self,
        param_config: ParamConfig,
        logger: LogConfig,
        condition_generator: ConditionGenerator,
        expr_generator: ExpressionGenerator,
        operator_manager: OperatorManager
    ):
        """
        Initialize the OperatorGenerator.

        Parameters:
            param_config (ParamConfig): Configuration object containing parameters like symbols and operator details.
            logger (LogConfig): Logger configuration to handle logging functionality.
            condition_generator (ConditionGenerator): A generator responsible for producing conditions.
            expr_generator (ExpressionGenerator): A generator responsible for producing expressions.
            operator_manager (OperatorManager): Manages operator-related functionality.

        Attributes:
            param_config (ParamConfig): Configuration object that holds various parameters.
            logger (Logger): Logger instance used for logging debug and info messages.
            standard_symbols (list): A list of standard operator symbols.
            unicode_symbols (list): A list of Unicode operator symbols.
            valid_symbols (list): A combined list of valid operator symbols (standard + Unicode).
            condition_generator (ConditionGenerator): The generator used to generate conditions.
            expr_generator (ExpressionGenerator): The generator used to generate expressions.
            operator_manager (OperatorManager): Manages operators for the generator.
            unary_variables (list): List of variables used in unary operations.
            binary_variables (list): List of variables used in binary operations.
            max_base (int): Maximum base value used in the generation process.
            operator_symbol_min_len (int): Minimum length for operator symbols.
            operator_symbol_max_len (int): Maximum length for operator symbols.
            max_if_branches (int): Maximum number of branches in conditional expressions.
        """
        self.param_config = param_config
        self.logger = logger.get_logger()  # Get logger instance for logging
        self.standard_symbols = self.param_config.get("basic_operator_symbols")
        self.unicode_symbols = self.get_unicode_symbols()
        self.valid_symbols = self.standard_symbols + self.unicode_symbols
        self.condition_generator = condition_generator  # Condition generator instance
        self.expr_generator = expr_generator  # Expression generator instance
        self.operator_manager = operator_manager  # Operator manager instance
        self.unary_variables = [self.param_config.atoms["left_operand"]]
        self.binary_variables = [
            self.param_config.atoms["left_operand"],
            self.param_config.atoms["right_operand"],
        ]
        self.max_base = self.param_config.get("max_base")
        self.operator_symbol_min_len = self.param_config.get("operator_symbol_min_len")
        self.operator_symbol_max_len = self.param_config.get("operator_symbol_max_len")
        self.max_if_branches = self.param_config.get("max_if_branches")

        # self.expr_parser = expr_parser
        # self.expr_transformer = expr_transformer
        # Log initialization details
        self.logger.info(
            "OperatorGenerator initialized with the following configuration:"
        )
        self.logger.debug(f"Standard symbols: {self.standard_symbols}")
        self.logger.debug(f"Unicode symbols: {self.unicode_symbols}")
        self.logger.debug(f"Valid symbols: {self.valid_symbols}")
        self.logger.debug(f"Unary variables: {self.unary_variables}")
        self.logger.debug(f"Binary variables: {self.binary_variables}")
        self.logger.debug(f"Max base: {self.max_base}")
        self.logger.debug(f"Operator symbol min length: {self.operator_symbol_min_len}")
        self.logger.debug(f"Operator symbol max length: {self.operator_symbol_max_len}")
        self.logger.debug(f"Max if branches: {self.max_if_branches}")

    def get_unicode_symbols(self) -> list:
        """
        Collects valid Unicode operator symbols from predefined ranges.

        This method retrieves symbols from several mathematical and arrow ranges in Unicode:
        - Mathematical Operators (U+2200 to U+22FF)
        - Supplemental Mathematical Operators (U+2A00 to U+2AFF)
        - Arrows (U+2190 to U+21FF)

        Returns:
            list: A list of valid Unicode operator symbols.
        """
        self.logger.info("Collecting Unicode symbols from predefined ranges.")
        unicode_ranges = [
            (0x2200, 0x22FF),  # Mathematical Operators
            (0x2A00, 0x2AFF),  # Supplemental Mathematical Operators
            (0x2190, 0x21FF),  # Arrows
        ]

        symbols = []

        for start, end in unicode_ranges:
            for codepoint in range(start, end + 1):
                char = chr(codepoint)
                symbols.append(char)

        self.logger.debug(f"Collected {len(symbols)} Unicode symbols.")
        return symbols

    def random_operator(self, existing_symbols: List[str]) -> str:
        """
        Generates a random operator string composed of one or more valid symbols.

        This method generates a random operator string with a length between
        `operator_symbol_min_len` and `operator_symbol_max_len`, ensuring that
        the generated operator does not already exist in the list of `existing_symbols`.

        Parameters:
            existing_symbols (List[str]): A list of currently existing operator symbols.
                                            The new symbol must not be in this list.

        Returns:
            str: The generated random operator string that is unique and within the specified length range.
        """
        self.logger.info("Generating a random operator string.")

        # Loop until a unique operator is generated
        while True:
            # Randomly choose a length for the operator within the specified range
            length = random.randint(
                self.operator_symbol_min_len, self.operator_symbol_max_len
            )

            # Generate the new symbol by randomly picking characters from valid symbols
            new_symbol = "".join(
                random.choice(self.valid_symbols) for _ in range(length)
            )

            # Check if the generated symbol is unique (not in existing_symbols)
            if new_symbol not in existing_symbols:
                self.logger.debug(
                    f"Generated new operator symbol: {new_symbol} with length {length}."
                )
                return new_symbol
            else:
                self.logger.debug(
                    f"Generated operator {new_symbol} already exists. Retrying..."
                )

    def random_operator_type_and_position(self) -> tuple:
        """
        Generates a random operator type and its position (if applicable).

        This method randomly selects an operator type, either "unary" or "binary".
        If the type is "unary", it also randomly chooses its position, either "prefix" or "postfix".
        For "binary" operators, the position is not applicable (set to None).

        Returns:
            tuple: A tuple containing the operator type and its position.
                If the operator type is "unary", the position is either "prefix" or "postfix".
                If the operator type is "binary", the position is None.
        """
        self.logger.info("Generating random operator type and position.")

        # Randomly select the operator type
        op_type = random.choice(["unary", "binary"])

        # Initialize unary_position as None
        unary_position = None

        # If the operator type is "unary", randomly choose its position
        if op_type == "unary":
            unary_position = random.choice(["prefix", "postfix"])

        # Log the final operator type and position
        self.logger.info(
            f"Operator type: {op_type}, Position: {unary_position if unary_position else 'None'}"
        )

        return op_type, unary_position

    def generate_base_operators(self):
        """
        Generates unary prefix operators for each base from 2 to self.max_base.

        This method creates a unary prefix operator for each base in the range from 2 to `self.max_base`.
        For each base, a random operator symbol is generated, and the operator is added to the operator manager.
        The operator is stored with additional properties, such as its base number and the unary position.

        """
        self.logger.info(
            "Starting to generate base operators for each base from 2 to max_base."
        )

        # Iterate through the range of bases from 2 to max_base
        for n in range(2, self.max_base + 1):
            self.logger.debug(f"Generating operator for base {n}.")

            # Get existing operator symbols to avoid duplication
            existing_symbols = self.operator_manager.get_operator_symbols()

            # Generate a random operator symbol that isn't already used
            op_symbol = self.random_operator(existing_symbols)

            # Define operator type and position
            op_type = "unary"
            op_position = "prefix"
            func_id = generate(size=10,alphabet=alphabet)
            # Construct the operator data
            operator_data = {
                "id": None,
                "func_id":  func_id,
                "symbol": op_symbol,
                "n_ary": 1,  # Unary operator
                "unary_position": op_position if op_type == "unary" else None,
                "n_order": None,
                "is_base": n,  # Base number
                "definition": None,
                "definition_type": None,
                "priority": None,
                "associativity_direction": None,
                "op_compute_func": None,
                "op_count_func": None,
                "properties": None,
                "dependencies": None,
                "is_temporary": False,
            }
            
            new_base_operator = OperatorInfo(**operator_data)

            # Add the generated operator to the operator manager
            self.operator_manager.add_operator(new_base_operator)

            self.logger.info(
                f"Base operator for base {n} with symbol '{op_symbol}' added successfully."
            )

        self.logger.info("Base operator generation completed.")

    def generate_lhs(self, op_symbol, op_type, op_position) ->str:
        """
        Generates the left-hand side (LHS) of an expression based on the operator type and position.

        This method constructs the left-hand side of an expression depending on the type of operator
        (unary or binary) and its position (prefix or postfix). It uses the operator symbol and operands
        defined in the configuration.

        Parameters:
            op_symbol (str): The operator symbol to be used in the expression (e.g., "+", "⊕").
            op_type (str): The type of the operator, either "unary" or "binary".
            op_position (str): The position of the operator, either "prefix" or "postfix" (only for unary operators).

        Returns:
            str: The generated left-hand side expression as a string.

        Raises:
            ValueError: If the operator type is neither "unary" nor "binary".
        """

        self.logger.debug(
            f"Generating LHS for operator '{op_symbol}', type '{op_type}', position '{op_position}'."
        )

        # Handle the case for unary operators
        if op_type == "unary":
            if op_position == "prefix":
                lhs = f"{op_symbol}{self.param_config.atoms['left_operand']}"  # e.g., "-a"
            elif op_position == "postfix":
                lhs = f"{self.param_config.atoms['left_operand']}{op_symbol}"  # e.g., "a-"
            else:
                self.logger.error(
                    f"Invalid position '{op_position}' for unary operator."
                )
                raise ValueError(
                    f"Invalid position '{op_position}' for unary operator."
                )

        # Handle the case for binary operators
        elif op_type == "binary":
            lhs = f"{self.param_config.atoms['left_operand']}{op_symbol}{self.param_config.atoms['right_operand']}"  # e.g., 'a + b', 'a⊕b'
        else:
            self.logger.error(f"Invalid operator type '{op_type}' received.")
            raise ValueError(f"Operator type must be either 'unary' or 'binary'.")

        self.logger.info(f"LHS generated: {lhs}")
        return lhs

    def generate_branches(self, order) -> list:
        """
        Generates a list of conditional branches for an expression, including 'if' and 'else' branches.

        This method generates a random number of 'if' branches based on the maximum allowed number
        of branches (`max_if_branches`), each containing a randomly generated expression and a condition.
        Additionally, an 'else' branch is added with a randomly generated expression.

        The format of each branch is a tuple containing the expression and the corresponding condition.

        Returns:
            list: A list of tuples, each containing a generated expression and its associated condition.
            Each tuple is in the form (expression, condition).
        """
        self.logger.debug("Generating branches for conditional expressions.")

        num_if_branches = random.randint(2, self.max_if_branches)
        branches = []

        self.logger.info(f"Generating {num_if_branches} 'if' branches.")


        exprs = self.expr_generator.create_n_expression_str_with_order(
                max_depth=random.randint(1, self.expr_generator.max_depth),
                atom_choice="variable_and_number",
                order=order,
                branch_num=num_if_branches,
            )

        for i, expr in enumerate(exprs[:-1]):  
            condition = self.condition_generator.generate_condition_expr()
            branches.append((expr, f"if {condition}"))
            self.logger.debug(f"Generated 'if' branch {i+1}: {expr} with condition {condition}")

        last_expr = exprs[-1]  
        branches.append((last_expr, "else"))  
        self.logger.debug(f"Generated 'else' branch: {last_expr}")

        self.logger.info(f"Total branches generated: {len(branches)}.")

        return branches

    def generate_recursive_call(self, op_symbol, op_type, op_position):
        """
        Generates recursive expressions for binary and unary operators.

        This function creates recursive calls for both unary and binary operators
        based on the following rules:

        For binary operators:
            - If b == 0, generates a basic expression involving a and b.
            - If b > 0, generates an expression involving a and (b-1), where the expression on the right side must include (b-1).
            - If b < 0, generates an expression involving a and (b+1), where the expression on the right side must include (b+1).

        For unary operators:
            - If a == 0, randomly generates a number.
            - If a > 0, generates an expression solely involving (a-1), with its own symbol, and only related to (a-1).
            - If a < 0, generates an expression solely involving (a+1), with its own symbol, and only related to (a+1).

        Parameters:
        op_symbol (str): The operator symbol (e.g., '+', '-', '*', etc.) to be used in the expressions.
        op_type (str): The type of the operator. Can be either 'unary' or 'binary'.
        op_position (str): The position of the unary operator. Can be either 'prefix' or 'postfix' (relevant only for unary operators).

        Returns:
        str: A string representing the recursive expression for the operator, with conditions based on the values of 'a' and 'b'.

        Raises:
        ValueError: If the provided operator type is neither 'unary' nor 'binary'.
        """
        if op_type == "binary":
            # The recursive expression for generating binary operators with operands a and b.
            self.expr_generator.set_variables(
                [
                    self.param_config.atoms["left_operand"],
                    self.param_config.atoms["right_operand"],
                ]
            )

            # If b == 0, generate a basic expression with a and b.
            expr_base = self.expr_generator.create_expression_str(
                atom_choice="variable_and_number"
            )

            # If b > 0, generate an expression involving a and (b-1) (note that the expression on the right side must include b-1).
            recursive_variable = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}-1{self.param_config.atoms['right_parenthesis']}{self.param_config.atoms['right_parenthesis']}"
            self.expr_generator.set_variables(
                [
                    self.param_config.atoms["left_operand"],
                    self.param_config.atoms["right_operand"],
                    recursive_variable,
                ]
            )
            recursive_expr_1 = ""
            while recursive_variable not in recursive_expr_1:
                recursive_expr_1 = self.expr_generator.create_expression_str(
                    atom_choice="variable_and_number"
                )

            # If b < 0, generate an expression involving a and (b+1).
            recursive_variable = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}+1{self.param_config.atoms['right_parenthesis']}{self.param_config.atoms['right_parenthesis']}"
            self.expr_generator.set_variables(
                [
                    self.param_config.atoms["left_operand"],
                    self.param_config.atoms["right_operand"],
                    recursive_variable,
                ]
            )
            recursive_expr_2 = ""
            while recursive_variable not in recursive_expr_2:
                recursive_expr_2 = self.expr_generator.create_expression_str(
                    atom_choice="variable_and_number"
                )

            return f"{expr_base}, if {self.param_config.atoms['right_operand']} == 0 ; {recursive_expr_1}, if {self.param_config.atoms['right_operand']} > 0 ; {recursive_expr_2}, else"

        elif op_type == "unary":
            # For unary operators, generate a recursive expression with a single parameter.
            self.expr_generator.set_variables([self.param_config.atoms["left_operand"]])

            # If a == 0, randomly generate a number.
            expr_base = self.expr_generator.create_expression_str(atom_choice="number")

            # If a > 0, generate an expression solely involving (a-1), with its own symbol, and only related to (a-1).
            if op_position == "prefix":
                recursive_variable = (
                    f"{op_symbol}({self.param_config.atoms['left_operand']}-1)"
                )
            elif op_position == "postfix":
                recursive_variable = (
                    f"({self.param_config.atoms['left_operand']}-1){op_symbol}"
                )
            self.expr_generator.set_variables(
                [self.param_config.atoms["left_operand"], recursive_variable]
            )
            recursive_expr_1 = ""
            while recursive_variable not in recursive_expr_1:
                recursive_expr_1 = self.expr_generator.create_expression_str(
                    atom_choice="variable_and_number"
                )

            # If a < 0, generate an expression solely involving (a+1), with its own symbol, and only related to (a+1).
            if op_position == "prefix":
                recursive_variable = (
                    f"{op_symbol}({self.param_config.atoms['left_operand']}+1)"
                )
            elif op_position == "postfix":
                recursive_variable = (
                    f"({self.param_config.atoms['left_operand']}+1){op_symbol}"
                )
            self.expr_generator.set_variables(
                [self.param_config.atoms["left_operand"], recursive_variable]
            )
            recursive_expr_2 = ""
            while recursive_variable not in recursive_expr_2:
                recursive_expr_2 = self.expr_generator.create_expression_str(
                    atom_choice="variable_and_number"
                )

            return f"{expr_base}, if {self.param_config.atoms['left_operand']} == 0 ; {recursive_expr_1}, if {self.param_config.atoms['left_operand']} > 0 ; {recursive_expr_2}, else"

        else:
            raise ValueError(
                "Unsupported operator type. Only 'unary' and 'binary' are supported."
            )

    def generate_definition(self, op_symbol, op_type, op_position, choice, order) -> str:
        """
        Generates a complete operator definition rule based on the provided parameters.

        This method constructs the definition of an operator, which can vary depending on the
        `choice` parameter. It can generate a simple expression, a recursive call, or a branching
        expression with conditional logic.

        The definition can be generated in three different forms:
            1. **Simple Definition**: A basic operator definition without any conditional branching.
            2. **Recursive Definition**: A definition where the operator is recursively applied, based on the operator type (unary or binary).
            3. **Branch Definition**: A definition with multiple branches, using conditional logic (if-else statements) to determine the behavior.

        Parameters:
            op_symbol (str): The symbol representing the operator (e.g., '+', '-', '*', etc.).
            op_type (str): The type of the operator, either 'unary' (one operand) or 'binary' (two operands).
            op_position (str): The position of the unary operator, either 'prefix' or 'postfix'.
            choice (str): A string that determines the type of operator definition to generate:
                        - "simple_definition": generates a simple expression without branching.
                        - "recursive_definition": generates an expression with a recursive call.
                        - "branch_definition": generates an expression with branching logic (if-else).

        Returns:
            str: A string representing the operator definition. The content of the string depends on the `choice` parameter:
                - For "simple_definition", a simple expression is returned.
                - For "recursive_definition", a recursive call expression is returned.
                - For "branch_definition", an expression with conditional branches is returned.

        Raises:
            ValueError: If the `choice` parameter is not one of the recognized options ("simple_definition", "recursive_definition", "branch_definition").
        """
        self.logger.debug(
            f"Generating definition for operator: {op_symbol}, Type: {op_type}, Position: {op_position}, Choice: {choice}"
        )

        # Generate the left-hand side of the operator definition
        lhs = self.generate_lhs(op_symbol, op_type, op_position)

        if choice == "simple_definition":
            # Simple expression, no branches
            # expr = self.expr_generator.create_expression_str(
            #     max_depth=random.randint(1, self.expr_generator.max_depth),
            #     atom_choice="variable_and_number",
            # )
            expr = self.expr_generator.create_n_expression_str_with_order(
                max_depth=random.randint(1, self.expr_generator.max_depth),
                atom_choice="variable_and_number",
                order=order,
                branch_num=1,
            )
            self.logger.info(
                f"Simple definition generated: {lhs} {self.param_config.atoms['equal']} {{ {expr[0]} }}"
            )
            return f"{lhs} {self.param_config.atoms['equal']} {{ {expr[0]} }}"

        elif choice == "recursive_definition":
            recursive_call = self.generate_recursive_call(
                op_symbol, op_type, op_position
            )
            return f"{lhs} = {{ {recursive_call} }}"

        elif choice == "branch_definition":
            # Generate branches with conditions
            branches = self.generate_branches(order)

            # Build the branch strings
            branch_strings = []
            for expr, condition in branches:
                if condition.startswith("if"):
                    branch_strings.append(f"{expr} , {condition}")
                elif condition == "else":
                    branch_strings.append(f"{expr}, else")

            # Join branches with semicolons
            rhs = " ; ".join(branch_strings)
            definition = f"{lhs} {self.param_config.atoms['equal']} {{ {rhs} }}"
            self.logger.info(f"Branch definition generated: {definition}")
            return definition

        else:
            self.logger.warning(f"Unknown choice: {choice}. Returning None.")
            return None

    def generate_operator_data_by_definition(self, choice, order) -> dict:
        """
        Generates operator data based on a specified operator definition type.

        This method generates an operator symbol, determines its type (unary or binary), and sets
        its position (prefix or postfix). Then, it creates an operator definition based on the given
        `choice` parameter, which determines whether the operator definition is simple or involves
        conditional branching. The generated operator data includes the operator's symbol, type,
        position, and its corresponding definition.

        Parameters:
            choice (str): The type of operator definition to generate.
                        Can be one of the following:
                        - "simple_definition": Generates a basic operator expression without branching.
                        - "branch_definition": Generates an operator definition with conditional branching (if-else).
                        - "recursive_definition": generates an expression with a recursive call.

        Returns:
            dict: A dictionary containing the generated operator data.
        """
        self.logger.debug(
            f"Generating operator data by definition with choice: {choice}"
        )

        # Generate a random operator symbol that doesn't already exist in the operator manager
        existing_symbols = self.operator_manager.get_operator_symbols()
        op_symbol = self.random_operator(existing_symbols)
        self.logger.debug(f"Generated operator symbol: {op_symbol}")

        # Determine the type (unary or binary) and position (prefix or postfix) of the operator
        op_type, op_position = self.random_operator_type_and_position()
        self.logger.debug(f"Operator type: {op_type}, Operator position: {op_position}")

        # Choose the appropriate variables based on the operator type
        variables = (
            self.unary_variables if op_type == "unary" else self.binary_variables
        )
        self.condition_generator.set_variables(variables)
        self.expr_generator.set_variables(variables)
        self.logger.debug(f"Operator variables set to: {variables}")

        # Generate the operator definition based on the choice (simple or branch definition)
        definition = self.generate_definition(op_symbol, op_type, op_position, choice, order)
        self.logger.debug(f"Generated operator definition: {definition}")

        func_id = generate(size=10,alphabet=alphabet)
        # Construct the operator data dictionary
        operator_data = {
            "id": None,  
            "func_id": func_id,
            "symbol": op_symbol,
            "n_ary": (
                1 if op_type == "unary" else 2
            ),  # Unary operators have 1 operand, binary have 2
            "unary_position": op_position if op_type == "unary" else None,
            "n_order": None,
            "is_base": None,  # Not a base operator for now
            "definition": definition,
            "definition_type": choice,  # The type of definition generated (simple or branch)
            "priority": None,  # Priority is not assigned for now
            "associativity_direction": None,  # Not assigned for now
            "op_compute_func": None,  # Compute function will be defined by the parser
            "op_count_func": None,  # Count function will be defined by the parser
            "properties": None,  # Properties are not assigned for now
            "dependencies": None,  # Dependencies are not yet defined
            "is_temporary": True,  # Indicates that this operator is temporary
        }

        self.logger.info(f"Generated operator data: {operator_data}")
        return operator_data

    def get_random_recursive_call_operator(self, order) -> OperatorInfo:
        """
        Selects a random operator that supports recursion from the operator manager.

        This method filters the operators managed by the `operator_manager` to find those
        that have recursion enabled (i.e., `is_recursion_enabled` is True). It then selects
        a random operator from the filtered list and returns the corresponding `OperatorInfo` object.

        Raises:
            ValueError: If no operators are available in the operator manager.
            ValueError: If no operators with recursion enabled are available.

        Returns:
            OperatorInfo: The selected operator's `OperatorInfo` object, including its ID, symbol, and other properties.
        """
        self.logger.debug("Attempting to get a random recursive call operator.")

        # Check if there are any operators available in the operator manager
        if not self.operator_manager.operators:
            self.logger.error("No operators available in the operator manager.")
            raise ValueError("No operators available.")

        # Filter operators that have recursion enabled
        recursive_operators = [
            (operator_id, operator_info)
            for operator_id, operator_info in self.operator_manager.operators.items()
            if operator_info.n_order==order-1
        ]

        self.logger.debug(
            f"Filtered operators with recursion enabled: {recursive_operators}"
        )

        # If no operators with recursion are available, raise an exception
        if not recursive_operators:
            self.logger.error("No operators with recursion enabled.")
            raise ValueError("No operators with recursion enabled.")

        # Randomly select one operator from the filtered list
        _, operator_info = random.choice(recursive_operators)
        self.logger.debug(f"Selected operator: {operator_info}")

        # Return the `OperatorInfo` instance instead of a tuple
        self.logger.info(f"Random recursive call operator selected: {operator_info}")
        return operator_info  # Returning an instance of OperatorInfo

    def generate_recursive_operator_data_by_loop(self, order) -> Optional[dict]:
        """
        Generates recursive operator data, including both unary and binary operators,
        and defines recursive computation functions for the operators. The recursion
        involves calling other operators within the defined computation functions.

        This method constructs recursive operator definitions and the corresponding
        computation functions for both unary and binary operators based on the
        random operator type, position, and symbols. It checks recursion validity
        and ensures that recursion will not lead to infinite loops.

        The generated operator data includes:
        - The operator's symbol
        - Its type (unary or binary)
        - A computation function
        - A count function
        - A definition for the operator's behavior

        Returns:
            dict: A dictionary containing the operator data, including the operator's
                  symbol, definition, and computation functions.
            None: If the recursion validity check fails, returns None.
        """

        self.logger.debug("Fetching existing operator symbols to avoid duplication.")
        existing_symbols = self.operator_manager.get_operator_symbols()

        # Randomly select a new operator symbol
        op_symbol = self.random_operator(existing_symbols)

        self.logger.debug(f"Selected operator symbol: {op_symbol}")

        # Randomly choose operator type (unary or binary) and position
        # op_type, op_position = self.random_operator_type_and_position()
        op_type, op_position = "binary", None
        # Set the variables for condition and expression generators
        variables = (
            self.unary_variables if op_type == "unary" else self.binary_variables
        )
        self.condition_generator.set_variables(variables)
        self.expr_generator.set_variables(variables)

        # Generate the operator ID
        func_id = generate(size=10,alphabet=alphabet)

        self.logger.debug(f"Generated operator Func ID: {func_id}")

        # Fetch a random recursive operator to be called in the recursion
        called_operator_info = self.get_random_recursive_call_operator(order)
        called_id = called_operator_info.func_id
        called_symbol = called_operator_info.symbol
        # called_operator_info.is_recursion_enabled=False#设置为不可以被递归调用了

        self.logger.debug(
            f"Chosen operator for recursion: {called_symbol} (ID: {called_id})"
        )

        # Generate the left-hand side expression
        lhs = self.generate_lhs(op_symbol, op_type, op_position)

        indent = "    "
        
        #Generate a basic expr here to use as the initial value of the result
        choices = [self.param_config.atoms["left_operand"], self.param_config.atoms["right_operand"], int(random.uniform(-100, 100))]  
        expr_str = f"{random.choice(choices)}"

        #The range of the loop variable is restricted here.
        if order == 3:
            loop_thres=int(1e6)
        elif order == 4:
            loop_thres=int(1e3)
        elif order == 5:
            loop_thres=int(1e2)
        else:
            loop_thres=int(thres)
        
        # Handle binary operator recursion
        if op_type == "binary":
            loop_variable = random.choice([self.param_config.atoms["left_operand"], self.param_config.atoms["right_operand"]])
            thres_check = f" or (abs({loop_variable}) > {loop_thres})" if order>=3 else ""
            
            
            self.logger.debug("Generating recursive binary operator.")

            if called_operator_info.n_ary == 2:
                # Randomly select the parameter order for recursion
                param_order = random.choice(
                    [
                        ("result", "result"),
                        ("result", self.param_config.atoms["left_operand"]),
                        ("result", self.param_config.atoms["right_operand"]),
                        (self.param_config.atoms["left_operand"], "result"),
                        (self.param_config.atoms["right_operand"], "result"),
                    ]
                )
                param1, param2 = param_order
                
                self.logger.debug(
                    f"Selected parameter order for recursion: {param_order}"
                )

                # # Check recursion validity
                # if not self.check_and_set_recursion_validity(
                #     called_operator_info, op_type, param_order
                # ):
                #     self.logger.warning("Recursion validity check failed.")
                #     return None

                # Generate the recursive computation function for binary operator
                op_compute_fun = f"""def op_{func_id}(a, b):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if ({loop_variable} != {loop_variable}) or ({loop_variable} in special_values){thres_check}:
{indent*2}return float('nan')
{indent}result = {expr_str}
{indent}for _ in range(abs({loop_variable})):
{indent*2}temp_result = op_{called_id}({param1}, {param2})
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if {loop_variable} > 0 else -temp_result
{indent}return result
"""


                op_count_fun = f"""def op_count_{func_id}(a, b):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if ({loop_variable} != {loop_variable}) or ({loop_variable} in special_values){thres_check}:
{indent*2}return 1
{indent}result = {expr_str}
{indent}count = 0 
{indent}for _ in range(abs({loop_variable})):
{indent*2}temp_result = op_{called_id}({param1}, {param2})
{indent*2}count += op_count_{called_id}({param1}, {param2})
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if {loop_variable} > 0 else -temp_result
{indent}return count if count > 0 else 1
"""
                if loop_variable==self.param_config.atoms['left_operand']:
                    variable_a_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                    variable_a_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    variable_b_str_1 = self.param_config.atoms['right_operand']
                    variable_b_str_2 = self.param_config.atoms['right_operand']
                else:
                    variable_a_str_1 = self.param_config.atoms['left_operand']
                    variable_a_str_2 = self.param_config.atoms['left_operand']
                    variable_b_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                    variable_b_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    
                # Generate the right-hand side expressions for the recursive function
                if param1 == "result":
                    param1_str_1 = f"{variable_a_str_1}{op_symbol}{variable_b_str_1}"
                    param1_str_2 = f"{variable_a_str_2}{op_symbol}{variable_b_str_2}"
                else:
                    param1_str_1 = param1
                    param1_str_2 = param1

                if param2 == "result":
                    param2_str_1 = f"{variable_a_str_1}{op_symbol}{variable_b_str_1}"
                    param2_str_2 = f"{variable_a_str_2}{op_symbol}{variable_b_str_2}"
                else:
                    param2_str_1 = param2
                    param2_str_2 = param2

                rhs_1 = f"{self.param_config.atoms['left_parenthesis']}{param1_str_1}{self.param_config.atoms['right_parenthesis']}{called_symbol}{self.param_config.atoms['left_parenthesis']}{param2_str_1}{self.param_config.atoms['right_parenthesis']}"
                rhs_2 = f"{self.param_config.atoms['left_parenthesis']}{param1_str_2}{self.param_config.atoms['right_parenthesis']}{called_symbol}{self.param_config.atoms['left_parenthesis']}{param2_str_2}{self.param_config.atoms['right_parenthesis']}"
                
                if order >= 3:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0 and abs({loop_variable}) < {loop_thres}; -{rhs_2}, if {loop_variable} < 0 and abs({loop_variable}) < {loop_thres}; {self.param_config.atoms['nan']}, else}}"
                else:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0; -{rhs_2}, else}}"
                self.logger.debug(f"Binary operator definition generated: {definition}")

            elif called_operator_info.n_ary == 1:
                # # Check recursion validity for unary call within binary operator
                # if not self.check_and_set_recursion_validity(
                #     called_operator_info, op_type, None
                # ):
                #     self.logger.warning("Recursion validity check failed.")
                #     return None

                op_compute_fun = f"""def op_{func_id}(a, b):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if ({loop_variable} != {loop_variable}) or ({loop_variable} in special_values){thres_check}:
{indent*2}return float('nan')
{indent}result = {expr_str}
{indent}for _ in range(abs({loop_variable})):
{indent*2}temp_result = op_{called_id}(result)
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if {loop_variable} > 0 else -temp_result
{indent}return result
"""

                op_count_fun = f"""def op_count_{func_id}(a, b):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if ({loop_variable} != {loop_variable}) or ({loop_variable} in special_values){thres_check}:
{indent*2}return 1
{indent}result = {expr_str}
{indent}count = 0 
{indent}for _ in range(abs({loop_variable})):
{indent*2}temp_result = op_{called_id}(result)
{indent*2}count += op_count_{called_id}(result)
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if {loop_variable} > 0 else -temp_result
{indent}return count if count > 0 else 1
"""
                
                if loop_variable==self.param_config.atoms['left_operand']:
                    variable_a_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                    variable_a_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    variable_b_str_1 = self.param_config.atoms['right_operand']
                    variable_b_str_2 = self.param_config.atoms['right_operand']
                else:
                    variable_a_str_1 = self.param_config.atoms['left_operand']
                    variable_a_str_2 = self.param_config.atoms['left_operand']
                    variable_b_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                    variable_b_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['right_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    
                param_str_1 = f"{variable_a_str_1}{op_symbol}{variable_b_str_1}"
                param_str_2 = f"{variable_a_str_2}{op_symbol}{variable_b_str_2}"

                if called_operator_info.unary_position == "prefix":
                    rhs_1 = f"{called_symbol}{self.param_config.atoms['left_parenthesis']}{param_str_1}{self.param_config.atoms['right_parenthesis']}"
                    rhs_2 = f"{called_symbol}{self.param_config.atoms['left_parenthesis']}{param_str_2}{self.param_config.atoms['right_parenthesis']}"
                elif called_operator_info.unary_position == "postfix":
                    rhs_1 = f"{self.param_config.atoms['left_parenthesis']}{param_str_1}{self.param_config.atoms['right_parenthesis']}{called_symbol}"
                    rhs_2 = f"{self.param_config.atoms['left_parenthesis']}{param_str_2}{self.param_config.atoms['right_parenthesis']}{called_symbol}"

                if order >= 3:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0 and abs({loop_variable}) < {loop_thres}; -{rhs_2}, if {loop_variable} < 0 and abs({loop_variable}) < {loop_thres}; {self.param_config.atoms['nan']}, else}}"
                else:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0; -{rhs_2}, else}}"
                    
                self.logger.debug(
                    f"Unary operator within binary operator definition generated: {definition}"
                )

        # Handle unary operator recursion
        elif op_type == "unary":
            loop_variable = self.param_config.atoms["left_operand"]
            thres_check = f" or (abs(a) > {loop_thres})" if order>=3 else ""
            
            self.logger.debug("Generating recursive unary operator.")

            if called_operator_info.n_ary == 2:
                param_order = random.choice(
                    [
                        ("result", "result"),
                        ("result", self.param_config.atoms["left_operand"]),
                        (self.param_config.atoms["left_operand"], "result"),
                    ]
                )
                param1, param2 = param_order

                self.logger.debug(
                    f"Selected parameter order for recursion: {param_order}"
                )

                # if not self.check_and_set_recursion_validity(
                #     called_operator_info, op_type, param_order
                # ):
                #     self.logger.warning("Recursion validity check failed.")
                #     return None

                op_compute_fun = f"""def op_{func_id}(a):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if (a != a) or (a in special_values){thres_check}:
{indent*2}return float('nan')
{indent}result = {expr_str}
{indent}for _ in range(abs(a)):
{indent*2}temp_result = op_{called_id}({param1}, {param2})
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if a > 0 else -temp_result
{indent}return result
"""

                op_count_fun = f"""def op_count_{func_id}(a):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if (a != a) or (a in special_values){thres_check}:
{indent*2}return 1
{indent}result = {expr_str}
{indent}count = 0 
{indent}for _ in range(abs(a)):
{indent*2}temp_result = op_{called_id}({param1}, {param2})
{indent*2}count += op_count_{called_id}({param1}, {param2})
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if a > 0 else -temp_result
{indent}return count if count > 0 else 1
"""


                if param1 == "result":
                    if op_position == "prefix":
                        param1_str_1 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                        param1_str_2 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    elif op_position == "postfix":
                        param1_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}{op_symbol}"
                        param1_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}{op_symbol}"
                else:
                    param1_str_1 = param1
                    param1_str_2 = param1

                if param2 == "result":
                    if op_position == "prefix":
                        param2_str_1 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                        param2_str_2 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                    elif op_position == "postfix":
                        param2_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}{op_symbol}"
                        param2_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}{op_symbol}"
                else:
                    param2_str_1 = param1
                    param2_str_2 = param1

                rhs_1 = f"{self.param_config.atoms['left_parenthesis']}{param1_str_1}{self.param_config.atoms['right_parenthesis']}{called_symbol}{self.param_config.atoms['left_parenthesis']}{param2_str_1}{self.param_config.atoms['right_parenthesis']}"
                rhs_2 = f"{self.param_config.atoms['left_parenthesis']}{param1_str_2}{self.param_config.atoms['right_parenthesis']}{called_symbol}{self.param_config.atoms['left_parenthesis']}{param2_str_2}{self.param_config.atoms['right_parenthesis']}"
                
                if order >= 3:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0 and abs({loop_variable}) < {loop_thres}; -{rhs_2}, if {loop_variable} < 0 and abs({loop_variable}) < {loop_thres}; {self.param_config.atoms['nan']}, else}}"
                else:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0; -{rhs_2}, else}}"
                    
                self.logger.debug(
                    f"Unary operator recursive definition generated: {definition}"
                )

            elif called_operator_info.n_ary == 1:
                # Check recursion validity for unary operator
                # if not self.check_and_set_recursion_validity(
                #     called_operator_info, op_type, None
                # ):
                #     self.logger.warning("Recursion validity check failed.")
                #     return None

                op_compute_fun = f"""def op_{func_id}(a):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if (a != a) or (a in special_values){thres_check}:
{indent*2}return float('nan')
{indent}result = {expr_str}
{indent}for _ in range(abs(a)):
{indent*2}temp_result = op_{called_id}(result)
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if a > 0 else -temp_result
{indent}return result
"""

                op_count_fun = f"""def op_count_{func_id}(a):
{indent}special_values = [float('inf'), float('-inf')]
{indent}if (a != a) or (a in special_values){thres_check}:
{indent*2}return 1
{indent}result = {expr_str}
{indent}count = 0 
{indent}for _ in range(abs(a)):
{indent*2}temp_result = op_{called_id}(result)
{indent*2}count += op_count_{called_id}(result)
{indent*2}if abs(temp_result) > thres:
{indent*3}temp_result = float("inf")
{indent*2}result = temp_result if a > 0 else -temp_result
{indent}return count if count > 0 else 1
"""

                if op_position == "prefix":
                    param_str_1 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}"
                    param_str_2 = f"{op_symbol}{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}"
                elif op_position == "postfix":
                    param_str_1 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}-1{self.param_config.atoms['right_parenthesis']}{op_symbol}"
                    param_str_2 = f"{self.param_config.atoms['left_parenthesis']}{self.param_config.atoms['left_operand']}+1{self.param_config.atoms['right_parenthesis']}{op_symbol}"

                if called_operator_info.unary_position == "prefix":
                    rhs_1 = f"{called_symbol}{self.param_config.atoms['left_parenthesis']}{param_str_1}{self.param_config.atoms['right_parenthesis']}"
                    rhs_2 = f"{called_symbol}{self.param_config.atoms['left_parenthesis']}{param_str_2}{self.param_config.atoms['right_parenthesis']}"
                elif called_operator_info.unary_position == "postfix":
                    rhs_1 = f"{self.param_config.atoms['left_parenthesis']}{param_str_1}{self.param_config.atoms['right_parenthesis']}{called_symbol}"
                    rhs_2 = f"{self.param_config.atoms['left_parenthesis']}{param_str_2}{self.param_config.atoms['right_parenthesis']}{called_symbol}"

                if order >= 3:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0 and abs({loop_variable}) < {loop_thres}; -{rhs_2}, if {loop_variable} < 0 and abs({loop_variable}) < {loop_thres}; {self.param_config.atoms['nan']}, else}}"
                else:
                    definition = f"{lhs} = {{{expr_str}, if {loop_variable} == 0; {rhs_1}, if {loop_variable} > 0; -{rhs_2}, else}}"

                self.logger.debug(f"Unary operator definition generated: {definition}")
        else:
            raise ValueError(
                "Unsupported operator type. Only 'unary' and 'binary' are supported."
            )

        operator_data = {
            "id": None,  # Unique identifier for the operator.
            "func_id": func_id,
            "symbol": op_symbol,  # The symbol representing the operator (e.g., "+", "-", "*").
            "n_ary": (
                1 if op_type == "unary" else 2
            ),  # Arity of the operator (1 for unary, 2 for binary).
            "unary_position": (
                op_position if op_type == "unary" else None
            ),  # Position of the unary operator, None for binary.
            "n_order": order,  # Computation order, managed by OperatorManager.
            "is_base": None,  # Initially no base operator flag.
            "definition": definition,  # Recursive definition of the operator.
            "definition_type": "recursive_definition",  # Type of the definition ("recursive_definition").
            "priority": None,  # Operator priority, not assigned yet.
            "associativity_direction": None,  # Operator associativity, not assigned yet.
            "op_compute_func": op_compute_fun,  # Function to compute the operator.
            "op_count_func": op_count_fun,  # Function to count operations or recursive calls.
            "properties": None,  # Additional properties of the operator, None initially.
            "dependencies": None,  # Dependencies of the operator, None initially.
            "is_temporary": True,  # Flag indicating the operator is temporarily generated.
        }

        # Log the generated operator data for tracking purposes.
        self.logger.info(f"Generated operator data: {operator_data}")

        return operator_data

    def create_operator_info(self, choice: str, order: str) -> Dict[str, Any]:
        """
        Generate an OperatorInfo object.
        """
        if choice == "recursive_definition":
            operator_data = self.generate_recursive_operator_data_by_loop(order)
        else:
            operator_data = self.generate_operator_data_by_definition(choice, order)
        return operator_data
