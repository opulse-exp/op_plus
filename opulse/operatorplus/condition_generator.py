import random
from typing import List, Dict
from operatorplus.operator_info import OperatorInfo
from operatorplus.operator_manager import OperatorManager
from config import LogConfig, ParamConfig

class ConditionGenerator:
    def __init__(
        self,
        param_config: ParamConfig,
        logger: LogConfig,
        operator_manager: "OperatorManager" = None,
    ):
        """
        Initializes the generator with a list of variable names, unary operators, binary operators, 
        numeric range for values, and the range for the number of conditions to generate.

        Parameters:
            param_config (ParamConfig): Configuration object containing necessary settings.
            logger (LogConfig): Logger configuration object for logging.
            operator_manager (OperatorManager, optional): Operator manager object for accessing operator information.
        """
        self.param_config = param_config
        self.logger = logger.get_logger()
        self.operator_manager = operator_manager
        self.variables = [self.param_config.atoms["left_operand"], self.param_config.atoms["right_operand"]]
        self.comparison_ops = self.param_config.get("comparison_ops")
        self.logical_connectors = self.param_config.get("logical_connectors")
        self.min_value = self.param_config.get("condition_numeric_range")["min_value"]
        self.max_value = self.param_config.get("condition_numeric_range")["max_value"]
        self.condition_probabilities = self.param_config.get('condition_probabilities')
        
        # Log initial configuration
        self.logger.debug(f"ConditionGenerator initialized with variables: {self.variables}")
        self.logger.debug(f"Comparison operators: {self.comparison_ops}")
        self.logger.debug(f"Logical connectors: {self.logical_connectors}")
        self.logger.debug(f"Numeric range: {self.min_value} to {self.max_value}")

    def set_variables(self, new_variables: List[str]):
        """
        Sets new values for the list of variables.

        Parameters:
            new_variables (List[str]): A new list of variables, e.g., ['a'] or ['a', 'b'].
        """
        self.variables = new_variables
        self.logger.debug(f"Variables set to: {self.variables}")

    def set_condition_probabilities(self, condition_probs: Dict[int, float]):
        """
        Sets the condition probability dictionary. The keys are numbers and the values are probabilities.
        If an empty dictionary is passed, the default values are restored.

        Parameters:
            condition_probs (Dict[int, float]): A dictionary of condition probabilities, where keys are numbers and values are the probabilities.

        Raises:
            ValueError: If the values in the probability dictionary are not within the valid range (0, 1).
        """
        # Check if the values in the dictionary are valid probabilities
        for key, prob in condition_probs.items():
            if not (0 <= prob <= 1):  # Ensure the probability is between 0 and 1
                raise ValueError(f"Probability for key {key} is out of valid range: {prob}")
        
        self.condition_probabilities = condition_probs
        self.param_config['condition_probabilities'] = condition_probs
        self.logger.debug(f"Condition probabilities set to: {self.condition_probabilities}")

    def generate_operand(self, var: str) -> str:
        """
        Randomly generates an expression with a unary or binary operator, or simply returns a variable.

        Parameters:
            var (str): The variable name.

        Returns:
            str: The generated expression, which can be a variable, a unary operator applied to the variable, 
                 or a binary operator with a constant.
        """
        unary_prefix_ops, unary_postfix_ops, binary_ops = (
            self.operator_manager.get_unary_and_binary_operators()
        )
        # Randomly choose the type of expression to generate: variable, unary operator, or binary operator
        expr_type = random.choice(
            ["variable", "unary_prefix", "unary_postfix", "binary"]
        )
        self.logger.debug(f"Generating operand for variable '{var}', chosen type: {expr_type}")

        if expr_type == "unary_prefix" and unary_prefix_ops:
            # Generate unary operator prefix expression
            unary_op = random.choice(unary_prefix_ops).symbol
            self.logger.debug(f"Generated unary prefix operator: {unary_op}")
            return f"{self.param_config.atoms['left_parenthesis']}{unary_op}{var}{self.param_config.atoms['right_parenthesis']}"

        elif expr_type == "unary_postfix" and unary_postfix_ops:
            # Generate unary operator postfix expression
            unary_op = random.choice(unary_postfix_ops).symbol
            self.logger.debug(f"Generated unary postfix operator: {unary_op}")
            return f"{self.param_config.atoms['left_parenthesis']}{var}{unary_op}{self.param_config.atoms['right_parenthesis']}"

        elif expr_type == "binary" and binary_ops:
            # Generate binary operator expression
            binary_op = random.choice(binary_ops).symbol
            value = random.randint(self.min_value, self.max_value)  # Can adjust the range
            self.logger.debug(f"Generated binary operator: {binary_op} with value: {value}")
            return f"{self.param_config.atoms['left_parenthesis']}{var} {binary_op} {value}{self.param_config.atoms['right_parenthesis']}"

        # Return the variable itself
        self.logger.debug(f"Returning variable: {var}")
        return var

    def generate_condition(self) -> str:
        """
        Generates a condition expression.

        Returns:
            str: The generated condition expression, in the form "operand comparison_op value".
        """
        var = random.choice(self.variables)
        operand = self.generate_operand(var)
        comp_op = random.choice(self.comparison_ops)
        mid_value = random.randint(self.min_value, self.max_value)
        value = random.randint(self.min_value, mid_value)
        condition = f"{operand} {comp_op} {value}"
        self.logger.debug(f"Generated condition: {condition}")
        return condition

    def choose_num_conditions(self) -> int:
        """
        Chooses the number of conditions based on the probability distribution in condition_probabilities.

        Returns:
            int: The number of conditions to generate, selected based on the probability distribution.
        """
        # Select the number of conditions based on the given probability distribution
        population = list(self.condition_probabilities.keys())
        weights = list(self.condition_probabilities.values())
        num_conditions = random.choices(population, weights=weights, k=1)[0]
        self.logger.debug(f"Chosen number of conditions: {num_conditions}")
        return num_conditions

    
    ##!这个地方好像写的有点问题，感觉都用一个连接词连接了啊
    def generate_condition_expr(self) -> str:
        """
        Generates an expression consisting of multiple conditions, including logical operators and condition parentheses.

        Returns:
            str: The generated condition expression, which can either be a single condition or a combination of conditions connected by logical operators.
        """
        # Choose the number of conditions based on condition_probabilities
        num_conditions = self.choose_num_conditions()

        # Generate the list of conditions
        conditions = [self.generate_condition() for _ in range(num_conditions)]
        self.logger.debug(f"Generated conditions: {conditions}")

        # Concatenate the conditions to form the final expression
        if num_conditions == 1:
            condition_expr = conditions[0]
        else:
            # Combine conditions with randomly chosen logical operators
            expr_parts = [conditions[0]]
            for i in range(1, num_conditions):
                connector = random.choice(self.logical_connectors)  # Pick a different connector for each pair
                expr_parts.append(connector)
                expr_parts.append(conditions[i])

                # Randomly decide whether to wrap the last two conditions with parentheses
                if random.choice([True, False]):
                    expr_parts[-3:] = [f"({expr_parts[-3]} {expr_parts[-2]} {expr_parts[-1]})"]

            condition_expr = " ".join(expr_parts)

            self.logger.debug(f"Generated final conditional expression: {condition_expr}")
            self.logger.info(f"Generated final conditional expression: {condition_expr}")
            return condition_expr




