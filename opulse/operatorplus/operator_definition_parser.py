from lark import Lark
from config import LogConfig, ParamConfig

class OperatorDefinitionParser:
    """
    A parser class for dynamically generating and parsing operator definitions.

    This class constructs a grammar dynamically based on the provided `ParamConfig` and uses the `Lark` parser 
    to parse operator definitions. The class supports parsing expressions that involve various operators, conditions, 
    and logical structures such as "if", "else", and logical conditions.

    Attributes:
        param_config (ParamConfig): Configuration object containing atoms like operators, parenthesis, and constants.
        logger (LogConfig): Logger configuration to record debugging and information logs.
        parser (Lark): The Lark parser instance to parse operator definitions.
        grammar (str): The dynamically generated grammar used by the Lark parser.
    """

    def __init__(self, param_config: ParamConfig, logger: LogConfig):
        """
        Initializes the OperatorDefinitionParser with given configuration and logger.

        Args:
            param_config (ParamConfig): A configuration object that contains parameter definitions, 
                                         including operators, atomic values, and symbols.
            logger (LogConfig): A logging configuration object used to log debugging and info messages.

        Initializes the grammar dynamically using the `param_config` and configures the Lark parser.
        """

        # Store the provided param_config and logger
        self.param_config = param_config
        self.logger = logger.get_logger()
        
        # Dynamically construct the grammar using `param_config`
        self.grammar = f"""
        ?start: rule
        rule: lhs_expr "{self.param_config.atoms["equal"]}" "{{" rhs_expr "}}"
        lhs_expr: expr
        rhs_expr: branch (SEMICOLON branch)* 
        ?branch: if_branch
            | else_branch
            | unconditional_branch
        if_branch: expr "," "if" condition
        else_branch: expr "," "else"
        unconditional_branch: expr
        ?condition: or_condition
        ?or_condition: or_condition "or" and_condition    -> or_condition
                    | and_condition
        ?and_condition: and_condition "and" comparison     -> and_condition
                    | comparison
        ?comparison: "not" comparison                      -> not_condition
                | expr CONDITION_OPERATOR expr          -> comparison
                | "{self.param_config.atoms["left_parenthesis"]}" condition "{self.param_config.atoms["right_parenthesis"]}"   -> grouped_condition 
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
        self.logger.info("OperatorDefinitionParser initialized successfully.")

    def parse_definition(self, definition):
        """
        Parse the given operator definition using the generated grammar.

        Args:
            definition (str): The operator definition string to be parsed.

        Returns:
            Lark.Tree: A Lark parsing tree representing the parsed definition.

        Logs the parsing process and any issues during parsing.
        """
        try:
            self.logger.info(f"Attempting to parse definition: {definition}")
            parsed_tree = self.parser.parse(definition)
            self.logger.info("Parsing successful.")
            return parsed_tree
        except Exception as e:
            self.logger.error(f"Error while parsing definition: {e}")
            raise

    def update_definition(self, definition) -> str:
        """
        Update the operator definition by replacing indexed numeric atoms with their values from `param_config`.

        This method performs a replacement in the expression, replacing placeholders such as '0', '1', etc. 
        with corresponding values from `numeric_atoms`.

        Args:
            definition (str): The operator definition to be updated.

        Returns:
            str: The updated operator definition with numeric atoms replaced.
        
        Logs each replacement performed in the update process for debugging.
        """
        updated_expr = definition

        self.logger.info(f"Starting update of definition: {definition}")
        
        # Limit to the first 10 numeric atoms for replacement
        for idx, numeric_atom in enumerate(self.param_config.atoms["numeric_atoms"][:10]):
            self.logger.debug(f"Replacing index '{idx}' with numeric atom value '{numeric_atom}'")
            updated_expr = updated_expr.replace(f'{idx}', str(numeric_atom))

        self.logger.info(f"Updated definition: {updated_expr}")
        return updated_expr




