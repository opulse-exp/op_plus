import json
from typing import List, Dict, Optional, Any
from config.constants import thres
import ctypes

class OperatorInfo:
    def __init__(
        self,
        id: int,
        func_id: str,
        symbol: str,
        n_ary: int,  # 1 for unary, 2 for binary
        unary_position: Optional[str],  # 'prefix', 'postfix', or None
        n_order: int,  # Order, used to measure complexity, particularly for recursive definitions
        is_base: Optional[
            int
        ],  # Used to identify the base type, e.g., 2 for binary, 10 for decimal, 16 for hexadecimal
        definition: Optional[str],
        definition_type: Optional[
            str
        ],  # Types: simple_definition, recursive_definition, branch_definition
        priority: int,  # Priority for operations with the same level, higher values represent higher priority
        associativity_direction: Optional[str],  # 'left', 'right', or None
        
        op_compute_func: Optional[
            str
        ],  # Function code for the operator, e.g., "def op_11(a, b): ..."
        op_count_func: Optional[
            str
        ],  # Function code to calculate the count, e.g., base = 0
        z3_compute_func: Optional[
            str
        ] = None,  ##TODO:Still in the process of realising, Used for constraint solving
        properties: Optional[
            Dict[str, bool]
        ] = None,  # Other properties such as "commutative", "associative", "idempotent", etc.
        weight: Optional[float] = 1,  # Probability of being selected
        dependencies: Optional[
            List[int]
        ] = None,  # Record dependencies on other operators
        is_temporary: bool = False,  # Whether the operator is temporary (for incomplete information)
        recursive_used_cases: int = 0b00000000,  # Record used recursive cases
        is_recursion_enabled: bool = True,  # Whether recursion can still be enabled based on the recursive type
        module: Optional[ctypes.CDLL] = None
    ):
        """
        Initializes the OperatorInfo object with various parameters describing the operator's properties.

        Parameters:
            id (int): Unique identifier for the operator.
            func_id (str): Function identifier for the operator.
            symbol (str): Symbol representing the operator.
            n_ary (int): Arity of the operator, either 1 for unary or 2 for binary.
            unary_position (Optional[str]): Position for unary operators ('prefix', 'postfix', or None).
            n_order (int): Order to measure complexity, especially for recursive operators.
            is_base (Optional[int]): Base type identifier (e.g., 2 for binary, 10 for decimal, 16 for hexadecimal).
            definition (Optional[str]): Definition of the operator (could be a string representation of the definition).
            definition_type (Optional[str]): Type of definition ('simple_definition', 'recursive_definition', or 'branch_definition').
            priority (int): Priority of the operator, higher means higher priority.
            associativity_direction (Optional[str]): Direction of associativity ('left', 'right', or None).
            op_compute_func (Optional[str]): Code string for computing the operator's result.
            op_count_func (Optional[str]): Code string for counting the operations.
            z3_compute_func (Optional[str]): Function code for constraint solving (still under development).
            properties (Optional[Dict[str, bool]]): Additional properties of the operator (e.g., commutative, associative, etc.).
            weight (Optional[float]): Probability of the operator being selected.
            dependencies (Optional[List[int]]): List of dependencies on other operators.
            is_temporary (bool): Whether the operator is temporary, typically used when its information is incomplete.
            recursive_used_cases (int): Record of the recursive cases used.
            is_recursion_enabled (bool): Whether recursion is still allowed for this operator.
            module (Optional[ctypes.CDLL]): Compiled module containing the operator's functions.
        """
        self.id = id
        self.func_id = func_id
        self.symbol = symbol
        self.n_ary = n_ary
        self.unary_position = unary_position
        self.n_order = n_order
        self.is_base = is_base
        self.definition = definition
        self.definition_type = definition_type
        self.priority = priority
        self.associativity_direction = associativity_direction
       
        self.op_compute_func = op_compute_func
        self.op_count_func = op_count_func
        self.z3_compute_func = z3_compute_func
        self.properties = properties
        self.weight = weight
        self.dependencies = dependencies
        self.is_temporary = is_temporary
        self.recursive_used_cases = recursive_used_cases
        self.is_recursion_enabled = is_recursion_enabled
        self.module = module
        
    def __repr__(self) -> str:
        """
        Provides a string representation of the operator information object.

        Returns:
            str: A string representation of the OperatorInfo object.
        """
        return (
            f"OperatorInfo(id={self.id}, func_id={self.func_id}, symbol='{self.symbol}', n_ary={self.n_ary}, "
            f"unary_position={self.unary_position!r}, is_base={self.is_base}, "
            f"definition={self.definition!r}, definition_type={self.definition_type!r}, "
            f"priority={self.priority}, "
            f"associativity_direction={self.associativity_direction!r}, n_order={self.n_order}, "
            f"op_compute_func={self.op_compute_func!r}, op_count_func={self.op_count_func!r}, "
            # f"properties={self.properties!r}, "
            f"dependencies={self.dependencies!r}, "
            f"compiled_functions={'{}' if not self.compiled_functions else f'{{...}}'})"
        )

    def to_json(self) -> str:
        """
        Converts the operator information object to a JSON string, excluding temporary and compiled function data.

        Returns:
            str: A JSON string representing the OperatorInfo object.
        """
        serializable_dict = self.__dict__.copy()
        # Remove attributes that should not be serialized
        for key in [
            "properties",
            "weight",
            "z3_compute_func",
            "is_temporary",
            "recursive_used_cases",
            "is_recursion_enabled",
            "module",
        ]:
            serializable_dict.pop(key, None)
        return json.dumps(serializable_dict, ensure_ascii=False)

    def to_dict(self) -> dict:
        """
        Converts the operator information object to a dictionary, excluding temporary and compiled function data.

        Returns:
            dict: A dictionary representing the OperatorInfo object.
        """
        serializable_dict = self.__dict__.copy()
        # Remove attributes that should not be included in the dictionary
        for key in [
            "properties",
            "weight",
            "z3_compute_func",
            "is_temporary",
            "recursive_used_cases",
            "is_recursion_enabled",
            "module",
        ]:
            serializable_dict.pop(key, None)
        return serializable_dict


    @staticmethod
    def from_json(json_str: str) -> "OperatorInfo":
        """
        Creates an OperatorInfo object from a JSON string.

        Args:
            json_str (str): A JSON string representing an OperatorInfo object.

        Returns:
            OperatorInfo: An instance of the OperatorInfo class initialized from the JSON data.
        """
        data = json.loads(json_str)
        return OperatorInfo(**data)

    def get_compute_function(
        self
    ) -> Optional[Any]:
        """
        Retrieves the compute function for the operator from the compiled module.

        Returns:
            Optional[Any]: The compute function object or None if the module or function is unavailable.
        """
        if self.module != None:
            func = getattr(self.module, f"op_{self.func_id}", None)
            return func
        return None

    def get_count_function(
        self
    ) -> Optional[Any]:
        """
        Retrieves the count function for the operator from the compiled module.

        Returns:
            Optional[Any]: The count function object or None if the module or function is unavailable.
        """
        if self.module != None:
            func = getattr(self.module, f"op_{self.func_id}", None)
            return func
        return None
    


