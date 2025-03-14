from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from operatorplus.operator_info import OperatorInfo
from config import LogConfig, ParamConfig
import json
from lark.tree import Tree
import re
import os
import numpy as np
from config.constants import thres, special_values
import cython
from operatorplus.compiler import CythonCompiler


# def exponential_decay(n_order, decay_rate=0.2, max_weight=1.0, min_weight=0.05):
#     weight = max_weight * np.exp(-decay_rate * n_order)
#     return max(weight, min_weight)

class OperatorManager:
    def __init__(self, config_file: str, param_config: ParamConfig, logger: LogConfig, cython_cache_dir: str, compiler: CythonCompiler, load_compile: True):
        """
        Initializes the OperatorManager with configuration details and sets up internal data structures.
        
        Parameters:
            config_file (str): Path to the JSONL file containing operator definitions.
            param_config (ParamConfig): Configuration object containing necessary settings.
            logger (LogConfig): Logger configuration object for logging.
            cython_cache_dir (str): Directory to store compiled Cython modules.
            compiler (CythonCompiler): Compiler object for compiling operator functions.
            load_compile (bool): Whether to compile operators during loading.
        """
        
        self.config_file = config_file
        self.param_config = param_config
        self.logger = logger.get_logger()
        self.compiler = compiler
        self.operators: Dict[str, OperatorInfo] = (
            {}
        )  # key: operator id, value: OperatorInfo
        self.symbol_to_operators: Dict[str, List[OperatorInfo]] = defaultdict(
            list
        )  # key: operator symbol, value: list of OperatorInfo
        self.base_operators: Dict[int, List[OperatorInfo]] = defaultdict(list)
        # key: is_base, value: list of OperatorInfo

        # self.available_funcs: Dict[str, Any] = {}  # to store available functions
        # self.available_funcs_str = f"thres = {2**31 - 1}\n\n"
        # self.max_workers = max_workers
        self.load_compile = load_compile
        self.cython_cache_dir = cython_cache_dir
        self.load_operators()

    def load_operators(self):
        """
        Loads operator definitions from a JSONL file.

        This method reads the configuration file line by line, parses each line into an
        `OperatorInfo` object, and stores the operators in various structures:
        - `self.operators`: A dictionary with operator ID as the key and `OperatorInfo` as the value.
        - `self.symbol_to_operators`: A dictionary with operator symbol as the key and a list of `OperatorInfo` as the value.
        - `self.base_operators`: A dictionary to store base operators based on their base status.

        Additionally, it updates the available functions for computation and counting based on the loaded operators.

        Logs relevant information about the loading process for monitoring and debugging purposes.
        """
        self.logger.info(
            f"Loading operators from configuration file: {self.config_file}"
        )
        
        with open(self.config_file, "r", encoding="utf-8") as f:
            line_count = 0
            for line in f:
                line_count += 1
                if not line.strip():
                    self.logger.debug(f"Skipping empty line {line_count}.")
                    continue  # Skip empty lines
                try:
                    operator = OperatorInfo.from_json(line)
                    if self.load_compile:
                        so_file = f"module_{operator.func_id}.cpython-310-x86_64-linux-gnu.so"
                        full_path = os.path.join(self.cython_cache_dir, so_file)
                        if os.path.exists(full_path):
                            operator.module = self.compiler.import_module_from_path(f"module_{operator.func_id}")
                        else:    
                            func_code_str = f"thres = {2**31 - 1}\n\n"#Add the value and limit of the thres variable.
                            func_code_str += f"# Operator Func ID: {operator.func_id} - op_compute_func\n"
                            func_code_str += f"{operator.op_compute_func}\n\n"
                            func_code_str += f"# Operator Func ID: {operator.func_id} - op_count_func\n"
                            func_code_str += f"{operator.op_count_func}\n\n"
                            self.compiler.compile_function(func_code_str, operator.func_id, deps = None) 
                            operator.module = self.compiler.import_module_from_path(f"module_{operator.func_id}")
                        
                    self.operators[operator.func_id] = operator
                    self.symbol_to_operators[operator.symbol].append(operator)

                    # Update available functions for the operator
                    if operator.is_base:
                        self.base_operators[operator.is_base].append(operator)

                    # self._update_available_funcs(operator)
                    self.logger.info(
                        f"Loaded operator {operator.id} ({operator.symbol}) from line {line_count}."
                    )

                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse operator from line {line_count}: {e}"
                    )
        # self.save_op_funcs_to_file()   
        self.logger.info(
            f"Successfully loaded {len(self.operators)} operators from the configuration file."
        )
        
    def save_op_funcs_to_file(self, file_path:str):
        """
        Saves all operator functions to a `.pyx` file for compilation.
        
        This method writes the compute and count functions of all operators to a `.pyx` file,
        ensuring that they can be compiled later.
        """
        with open(file_path, "w") as file:
            # Write the necessary imports and initializations at the start of the file
            file.write(f"thres = {2**31 - 1}\n\n")
            
            # Now, write the operator functions
            for op_func_id, operator_info in self.operators.items():
                # Ensure both op_compute_func and op_count_func exist
                if hasattr(operator_info, 'op_compute_func') and hasattr(operator_info, 'op_count_func'):
                    # Write the op_compute_func (as string)
                    op_compute_func_str = operator_info.op_compute_func
                    file.write(f"# Operator ID: {op_func_id} - op_compute_func\n")
                    file.write(f"{op_compute_func_str}\n\n")
                    
                    # Write the op_count_func (as string)
                    op_count_func_str = operator_info.op_count_func
                    file.write(f"# Operator ID: {op_func_id} - op_count_func\n")
                    file.write(f"{op_count_func_str}\n\n")
                else:
                    self.logger.warning(f"Operator ID {op_func_id} does not have a valid op_compute_func or op_count_func.")
                    
    def save_operators_to_jsonl(self, file_path: str):
        """
        Saves all operators to a JSONL file.
        
        This method serializes each operator in `self.operators` and writes it to the specified file path in JSONL format.
        
        Parameters:
            file_path (str): The path to the file where the operators should be saved.
        
        Logs the process of saving operators to the file.
        """
        self.logger.info(f"Saving operators to {file_path}.")

        with open(file_path, "w", encoding="utf-8") as file:
            for operator in self.operators.values():
                json_line = operator.to_json()
                file.write(json_line + "\n")
                file.flush()  
                self.logger.debug(
                    f"Saved operator {operator.id} ({operator.symbol}) to {file_path}."
                )

        self.logger.info(f"Successfully saved all operators to {file_path}.")
        

    def get_operator_by_func_id(self, op_func_id: str) -> OperatorInfo:
        """
        Retrieves an operator by its function ID.
        
        Parameters:
            op_func_id (str): The function ID of the operator.
        
        Returns:
            OperatorInfo: The operator corresponding to the given function ID.
        
        Raises:
            ValueError: If no operator with the given function ID exists.
        """
        self.logger.debug(f"Fetching operator with func ID {op_func_id}.")

        if op_func_id not in self.operators:
            self.logger.error(f"Operator ID {op_func_id} does not exist.")
            raise ValueError(f"Operator ID {op_func_id} does not exist.")

        self.logger.debug(f"Operator ID {op_func_id} found.")
        return self.operators[op_func_id]

    def get_operators_by_symbol(self, symbol: str) -> List[OperatorInfo]:
        """
        Retrieves all operators corresponding to a given symbol.

        Args:
            symbol (str): The operator symbol.

        Returns:
            List[OperatorInfo]: A list of operators corresponding to the symbol.
        """
        self.logger.debug(f"Fetching operators with symbol '{symbol}'.")

        operators = self.symbol_to_operators.get(symbol, [])

        self.logger.debug(f"Found {len(operators)} operators for symbol '{symbol}'.")
        return operators

    def get_operator_symbols(self) -> List[str]:
        """
        Retrieves a list of all operator symbols.

        Returns:
            List[str]: A list of operator symbols.
        """
        self.logger.debug("Fetching all operator symbols.")

        symbols = list(self.symbol_to_operators.keys())

        self.logger.debug(f"Found {len(symbols)} operator symbols.")
        return symbols

    def get_operator_function_id(
        self, operator_symbol: str, is_unary: bool, unary_position: str
    ) -> Optional[tuple[int, bool]]:
        """
        Retrieves the function ID and temporary status of an operator based on its symbol and type (unary or binary).

        Args:
            operator_symbol (str): The operator symbol.
            is_unary (bool): A boolean indicating whether the operator is unary (True) or binary (False).

        Returns:
            Optional[tuple[int, bool]]: A tuple containing the operator's function ID and its temporary status.
                                        If no matching operator is found, returns (None, False).
        """
        self.logger.debug(
            f"Fetching function ID for operator symbol '{operator_symbol}' and type {'unary' if is_unary else 'binary'}."
        )

        for operator in self.symbol_to_operators.get(operator_symbol, []):
            if (is_unary and operator.n_ary == 1 and operator.unary_position == unary_position) or (
                not is_unary and operator.n_ary == 2
            ):
                self.logger.debug(
                    f"Found operator {operator.id} ({operator.symbol}) matching the criteria."
                )
                return operator.func_id, operator.is_temporary

        self.logger.debug(
            f"No matching operator found for symbol '{operator_symbol}' and type {'unary' if is_unary else 'binary'}."
        )
        return None, False

    def get_operator_by_base(self, base: int) -> OperatorInfo:
        """
        Retrieves an operator based on the given base (number system).

        Args:
            base (int): The base (e.g., 2 for binary, 10 for decimal, etc.).

        Returns:
            OperatorInfo: The operator corresponding to the given base.

        Raises:
            ValueError: If no operators are available for the given base.
        """
        self.logger.debug(f"Fetching operator for base {base}.")

        if base not in self.base_operators:
            self.logger.error(f"Base type {base} does not exist.")
            raise ValueError(f"Base type {base} does not exist.")

        self.logger.debug(f"Found operator(s) for base {base}.")
        return self.base_operators[base]

    def get_unary_and_binary_operators(
        self,
    ) -> Tuple[List[OperatorInfo], List[OperatorInfo], List[OperatorInfo]]:
        """
        Retrieves the lists of unary prefix operators, unary postfix operators, and binary operators.

        This method categorizes the operators into three types:
        - Unary prefix operators: Operators that appear before their operands.
        - Unary postfix operators: Operators that appear after their operands.
        - Binary operators: Operators that take two operands.

        Returns:
            Tuple[List[OperatorInfo], List[OperatorInfo], List[OperatorInfo]]:
            A tuple containing three lists:
            1. List of unary prefix operators
            2. List of unary postfix operators
            3. List of binary operators
        """
        self.logger.debug("Fetching unary and binary operators.")

        # Get unary prefix operators
        unary_prefix_ops = [
            op
            for op in self.operators.values()
            if op.n_ary == 1 and op.unary_position == "prefix"
        ]

        self.logger.debug(f"Found {len(unary_prefix_ops)} unary prefix operators.")

        # Get unary postfix operators
        unary_postfix_ops = [
            op
            for op in self.operators.values()
            if op.n_ary == 1 and op.unary_position == "postfix"
        ]

        self.logger.debug(f"Found {len(unary_postfix_ops)} unary postfix operators.")

        # Get binary operators
        binary_ops = [op for op in self.operators.values() if op.n_ary == 2]

        self.logger.debug(f"Found {len(binary_ops)} binary operators.")

        return unary_prefix_ops, unary_postfix_ops, binary_ops

    def get_operators_by_priority(self) -> List[OperatorInfo]:
        """
        Sorts and returns operators based on their priority.

        This method sorts all operators by their priority, where operators with lower priority come first.

        Returns:
            List[OperatorInfo]: A list of operators sorted by priority.
        """
        self.logger.debug("Sorting operators by priority.")

        # Sort operators by priority in ascending order (lower priority first)
        sorted_operators = sorted(
            self.operators.values(), key=lambda op: op.priority, reverse=False
        )

        self.logger.debug(f"Sorted {len(sorted_operators)} operators by priority.")

        return sorted_operators

    def extract_op_dependencies(self, operator:OperatorInfo):
        """
        Extracts dependencies of a given operator by analyzing its compute function.
        
        This method uses a regular expression to match operator IDs in the `op_compute_func`
        field of the operator and identifies any dependencies (operators that the current
        operator relies on).

        Parameters:
            operator (OperatorInfo): The operator whose dependencies need to be extracted.

        Updates:
            - The `dependencies` attribute of the operator is updated to a list of dependent operator IDs.
        """
        # Regular expression pattern to match operator dependencies (e.g., op_1, op_2, etc.)
        op_pattern = r"op_(\w+)\("

        # Use re.findall to extract all matching operator IDs from the function
        op_strs = re.findall(op_pattern, operator.op_compute_func)

        # Convert matched strings and remove duplicates
        op_strs = list(set(op_strs)) 

        # If the operator itself is in the list of dependencies, remove it
        if operator.func_id in op_strs:
            op_strs.remove(operator.func_id)

        # Update operator dependencies
        operator.dependencies = op_strs

    def calculate_order(self, operator:OperatorInfo):
        """
        Calculates the order (n_order) of a specific operator based on its dependencies.
        
        Parameters:
            operator (OperatorInfo): The operator whose order needs to be calculated.
        
        Updates:
            - The `n_order` attribute of the operator is updated based on its dependencies.
        """
        # If the operator has dependencies, calculate its order based on them
        if operator.dependencies:
            # Get the n_order values of all dependencies
            dependency_orders = [
                self.operators[dep_id].n_order for dep_id in operator.dependencies
            ]
            self.logger.debug(
                f"Dependency orders for operator {operator.func_id}: {dependency_orders}."
            )

            if operator.definition_type == "recursive_definition":
                # For recursive definitions, the order is the max order of dependencies + 1
                operator.n_order = max(dependency_orders) + 1
                self.logger.debug(
                    f"Operator {operator.func_id} is recursive; setting n_order to {operator.n_order}."
                )
            else:
                # For non-recursive definitions, the order is the max order of dependencies
                operator.n_order = max(dependency_orders)
                self.logger.debug(
                    f"Operator {operator.func_id} is non-recursive; setting n_order to {operator.n_order}."
                )
        else:
            # If the operator has no dependencies, set its order to 1
            operator.n_order = 1
            self.logger.debug(
                f"Operator {operator.func_id} has no dependencies; setting n_order to 1."
            )
        # operator_info.weight = exponential_decay(operator_info.n_order)
        # Log the final n_order value for the operator
        self.logger.info(
            f"Operator {operator.symbol} (ID: {operator.func_id}) has n_order: {operator.n_order}."
        )

    def update_operator_temporary_status(
        self, op_func_id: str, new_status: bool
    ) -> bool:
        """
        Updates the 'is_temporary' status of the specified operator.

        This function looks for an operator by its ID and sets its 'is_temporary' status
        to the provided new status.

        Parameters:
            op_func_id (int): The ID of the operator to update.
            new_status (bool): The new 'is_temporary' status to set for the operator.

        Returns:
            bool: Returns True if the update was successful, otherwise returns False if the operator was not found.
        """
        self.logger.debug(
            f"Attempting to update 'is_temporary' status for operator ID {op_func_id} to {new_status}."
        )

        # Loop through all operators to find the one with the specified ID
        for operators in self.symbol_to_operators.values():
            for operator in operators:
                if operator.func_id == op_func_id:
                    # Found the operator, updating its is_temporary status
                    operator.is_temporary = new_status
                    self.logger.info(
                        f"Operator {op_func_id}: 'is_temporary' status successfully updated to {new_status}."
                    )
                    return True  # Update successful

        # If the operator ID was not found, log an error and return False
        self.logger.error(f"Operator with ID {op_func_id} not found. Update failed.")
        return False  # Operator not found

    def add_operator(self, operator: OperatorInfo):
        """
        Dynamically adds a new operator to the system.
        
        Parameters:
            operator (OperatorInfo): The operator to be added.
        
        Raises:
            ValueError: If an operator with the same function ID already exists.
        """

        if operator.func_id in self.operators:
            self.logger.error(f"Operator ID {operator.func_id} already exists.")
            raise ValueError(f"Operator ID {operator.func_id} already exists.")


        # Add the operator to the operators dictionary
        self.operators[operator.func_id] = operator

        # Map the operator to its symbol in the symbol_to_operators dictionary
        if operator.symbol not in self.symbol_to_operators:
            self.symbol_to_operators[operator.symbol] = []
        self.symbol_to_operators[operator.symbol].append(operator)
        self.logger.debug(
            f"Operator {operator.symbol} (ID: {operator.func_id}) added to symbol_to_operators."
        )

        # Add the operator to the base_operators dictionary based on its base type
        if operator.is_base is not None:
            if operator.is_base not in self.base_operators:
                self.base_operators[operator.is_base] = []
            self.base_operators[operator.is_base].append(operator)
            self.logger.debug(
                f"Operator {operator.symbol} (ID: {operator.func_id}) added to base_operators."
            )

    
    def remove_operator(self, op_func_id: str):
        """
        Dynamically removes an operator from the system.

        This method removes an operator by its ID, updating the internal storage
        (both `self.operators` and `self.symbol_to_operators`) accordingly.

        Parameters:
            op_func_id (int): The ID of the operator to be removed.

        Raises:
            ValueError: If the operator ID does not exist in the system.
        """
        self.logger.debug("Attempting to remove operator with ID: %s", op_func_id)

        if op_func_id not in self.operators:
            self.logger.error(f"Operator ID {op_func_id} does not exist.")
            raise ValueError(f"Operator ID {op_func_id} does not exist.")

        # Retrieve and remove the operator from the operators dictionary
        operator = self.operators.pop(op_func_id)
        self.logger.info(f"Removed operator {operator.symbol} (ID: {op_func_id}).")

        # Remove the operator from the symbol_to_operators mapping
        if operator.symbol in self.symbol_to_operators:
            self.symbol_to_operators[operator.symbol].remove(operator)
            self.logger.debug(
                f"Operator {operator.symbol} (ID: {op_func_id}) removed from symbol_to_operators."
            )

    def update_operator(self, op_func_id: str, updated_data: Dict[str, Any]):
        """
        Dynamically updates an existing operator in the system.

        This method replaces the operator with the given ID (`op_id`) using the data
        in `updated_data`. It performs the necessary checks and ensures that all required fields
        are provided before updating the operator in the internal storage.

        Parameters:
            op_func_id (int): The ID of the operator to be updated.
            updated_data (dict): A dictionary containing the updated data for the operator.

        Raises:
            ValueError: If the operator ID does not exist or required fields are missing.
        """
        self.logger.debug("Attempting to update operator with ID: %s", op_func_id)

        # Check if the operator exists
        if op_func_id not in self.operators:
            self.logger.error(f"Operator ID {op_func_id} does not exist.")
            raise ValueError(f"Operator ID {op_func_id} does not exist.")

        # Ensure the 'id' in updated_data matches the op_id
        updated_data["func_id"] = op_func_id

        # Ensure 'compute_func' is provided in the updated data
        if "compute_func" not in updated_data or not updated_data["compute_func"]:
            self.logger.error("compute_func must be provided.")
            raise ValueError("compute_func must be provided.")

        # Set 'n_order' to None, letting calculate_order handle it later
        updated_data["n_order"] = None

        # Remove the old operator
        old_operator = self.operators.pop(op_func_id)
        self.symbol_to_operators[old_operator.symbol].remove(old_operator)
        self.logger.info(f"Removed old operator {old_operator.symbol} (ID: {op_func_id}).")

        # Add the updated operator
        updated_operator = OperatorInfo(**updated_data)
        self.operators[updated_operator.id] = updated_operator
        self.symbol_to_operators[updated_operator.symbol].append(updated_operator)
        self.logger.info(f"Updated operator {updated_operator.symbol} (ID: {op_func_id}).")

        # Recalculate order after the update
        self.calculate_order()
        self.logger.debug(f"Recalculated order for operator ID: {op_func_id}.")

    def delete_one_operator(self, op_func_id: str) -> None:
        """
        Delete an operator and recursively remove dependent operators.
        Afterward, reassign IDs for the remaining operators.

        Parameters:
            op_func_id (int): The ID of the operator to be deleted.
        """
        self.logger.debug("Attempting to delete operator with ID: %s", op_func_id)

        # Recursively delete the operator and its dependencies
        self.delete_one_operator_by_dep(op_func_id)

        # Reassign operator IDs after deletion
        sorted_keys = sorted(self.operators.keys())
        op_pattern = r"def op_(\s+)"
        op_count_pattern = r"def op_count_(\s+)"

        for i, old_key in enumerate(sorted_keys, start=1):
            if old_key != i:
                self.operators[i] = self.operators[old_key]
                # Update the ID of the operator
                self.operators[i].id = i
                # Update the operator's function string
                self.operators[i].op_compute_func = re.sub(
                    op_pattern,
                    lambda m: f"def op_{i}",
                    self.operators[i].op_compute_func,
                    count=1,
                )
                self.operators[i].op_count_func = re.sub(
                    op_count_pattern,
                    lambda m: f"def op_count_{i}",
                    self.operators[i].op_count_func,
                    count=1,
                )
                for operator in self.operators.values():
                    if old_key in operator.dependencies:
                        # Replace old_key with i in dependencies
                        operator.dependencies = [
                            i if dep == old_key else dep
                            for dep in operator.dependencies
                        ]
                        # Also, update the operator's compute functions to reflect the new op_id
                        operator.op_compute_func = re.sub(
                            rf"op_{old_key}",
                            lambda m: f"op_{i}",
                            operator.op_compute_func,
                        )
                        operator.op_count_func = re.sub(
                            rf"op_count_{old_key}",
                            lambda m: f"op_count_{i}",
                            operator.op_count_func,
                        )
                del self.operators[old_key]

        self.logger.info(
            "Operator with ID %s and its dependencies removed. Operator IDs reassigned.",
            op_func_id)

    def delete_one_operator_by_dep(self, op_func_id: str) -> None:
        """
        Recursively delete an operator and its dependencies.

        Parameters:
            op_func_id (int): The ID of the operator to be deleted.

        Raises:
            ValueError: If the operator with the given ID does not exist.
        """
        self.logger.debug(
            "Attempting to recursively delete operator with ID: %s", op_func_id
        )

        # Check if the operator exists
        if op_func_id not in self.operators:
            self.logger.error(f"Operator ID {op_func_id} does not exist.")
            raise ValueError(f"Operator ID {op_func_id} does not exist.")

        # Set to keep track of operators that need to be deleted
        to_delete_ids = set()

        # Recursively find all operators that depend on the given operator
        self._find_all_dependent_operator_ids(op_func_id, to_delete_ids)

        # Remove the operators
        for op_id_to_delete in to_delete_ids:
            self.remove_operator(op_id_to_delete)

        self.logger.debug(
            "Completed recursive deletion for operator ID: %s and its dependencies.",
            op_func_id,
        )

    def _find_all_dependent_operator_ids(self, op_func_id: str, to_delete_ids: set) -> None:
        """
        Helper function to recursively find all dependent operators that should be deleted.

        Parameters:
            op_func_id (int): The ID of the operator whose dependencies should be found.
            to_delete_ids (set): A set that stores all operator IDs that should be deleted.
        """
        # If this operator has already been marked for deletion, return early
        if op_func_id in to_delete_ids:
            return

        # Mark this operator for deletion
        to_delete_ids.add(op_func_id)

        # Recursively find operators that depend on the current operator
        for operator in self.operators.values():
            if op_func_id in operator.dependencies:
                self._find_all_dependent_operator_ids(operator.func_id, to_delete_ids)
