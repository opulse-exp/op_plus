import logging
import random
from config import LogConfig
from operatorplus.operator_manager import OperatorManager

class OperatorPriorityManager:
    def __init__(
        self,
        logger: LogConfig,
        operator_manager: "OperatorManager" = None,
    ):
        """
        Initializes the OperatorPriorityManager with a logger and an optional OperatorManager.

        Parameters:
            logger (logging.Logger): Logger instance for logging messages.
            operator_manager (OperatorManager, optional): An instance of OperatorManager for managing operators.
        """
        self.logger = logger.get_logger()
        self.operator_manager = operator_manager

    def assign_priorities(self):
        """
        Assigns priorities and associativities to operators.
        
        Rules:
        1. Postfix operators have a higher priority than prefix operators.
        2. Operators with the same priority have the same associativity.

        This method assigns priorities and associativities to all operators managed by the OperatorManager.
        The assignment follows the rules defined above.
        """
        self.logger.info("Starting to assign operator priorities and associativities...")

        # A dictionary to hold the associativity direction for each priority level
        self.priority_associativity = {}
        self.max_priority = 0

        # Reset the current priority and associativity of each operator
        for op in self.operator_manager.operators.values():
            op.priority = 0
            op.associativity_direction = None

        # Iterate over all operators to assign priority and associativity
        for op in self.operator_manager.operators.values():
            if op.n_ary == 1:
                # Assign priority for unary operators (either prefix or postfix)
                if op.unary_position == "prefix":
                    # Prefix operators typically have right associativity
                    available_priority = [
                        p for p, a in self.priority_associativity.items() if a == "right"
                    ]
                    available_priority.append(self.max_priority + 1)
                    op.priority = random.choice(available_priority)
                    op.associativity_direction = "right"
                    self.logger.debug(f"Assigned 'prefix' unary operator '{op.symbol}' a priority of {op.priority} and right associativity.")
                elif op.unary_position == "postfix":
                    # Postfix operators typically have left associativity
                    available_priority = [
                        p for p, a in self.priority_associativity.items() if a == "left"
                    ]
                    available_priority.append(self.max_priority + 1)
                    op.priority = random.choice(available_priority)
                    op.associativity_direction = "left"
                    self.logger.debug(f"Assigned 'postfix' unary operator '{op.symbol}' a priority of {op.priority} and left associativity.")

                # If a new priority was assigned, update max_priority and associativity
                if op.priority == self.max_priority + 1:
                    self.max_priority += 1
                    self.priority_associativity[self.max_priority] = op.associativity_direction

            elif op.n_ary == 2:
                # Assign priority for binary operators
                available_priority = [p for p, a in self.priority_associativity.items()]
                available_priority.append(self.max_priority + 1)
                op.priority = random.choice(available_priority)

                # If a new priority is assigned, set associativity
                if op.priority == self.max_priority + 1:
                    op.associativity_direction = random.choice(["left", "right"])
                    self.max_priority += 1
                    self.priority_associativity[self.max_priority] = op.associativity_direction
                    self.logger.debug(f"Assigned binary operator '{op.symbol}' a new priority of {op.priority} and random associativity.")
                else:
                    op.associativity_direction = self.priority_associativity[op.priority]
                    self.logger.debug(f"Assigned binary operator '{op.symbol}' the existing priority of {op.priority} and associativity {op.associativity_direction}.")

            # Log the assigned priority and associativity for each operator
            self.logger.info(
                f"Assigned operator '{op.symbol}' ({op.n_ary}-ary, ID: {op.id}) with priority: {op.priority}, associativity: {op.associativity_direction}"
            )

        self.logger.info("Operator priority and associativity assignment completed.")
