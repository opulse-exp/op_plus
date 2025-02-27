# import json


class ExpressionInfo:
    def __init__(
        self,
        id,
        expression,
        highest_degree,
        priority_hierarchical_complexity,
        normalized_expansion_degree,
        operation_count,
        complexity_ratio,
        max_digit_count,
    ):
        """
        Initializes an ExpressionInfo object with various properties of an expression.

        Args:
            id (int): Unique identifier for the expression.
            expression (str): The expression string.
            highest_degree (int): The highest degree of the expression.
            priority_hierarchical_complexity (int): The priority-based hierarchical complexity.
            normalized_expansion_degree (int): The normalized expansion degree of the expression.
            operation_count (int): The total count of operations in the expression.
            complexity_ratio (int): The complexity ratio of the expression.
            max_digit_count (int): The maximum digit count in the expression.
        """
        self.id = id
        self.expression = expression
        self.highest_degree = highest_degree
        self.priority_hierarchical_complexity = priority_hierarchical_complexity
        self.normalized_expansion_degree = normalized_expansion_degree
        self.operation_count = operation_count
        self.complexity_ratio = complexity_ratio
        self.max_digit_count = max_digit_count


#     def __repr__(self):
#         """
#         Returns a string representation of the ExpressionInfo object.

#         Returns:
#             (str): A formatted string with the object's attributes.
#         """
#         return (
#             f"Expression(id={self.id}, expression='{self.expression}', "
#             f"highest_degree={self.highest_degree}, "
#             f"priority_hierarchical_complexity={self.priority_hierarchical_complexity}, "
#             f"normalized_expansion_degree={self.normalized_expansion_degree}, "
#             f"operation_count={self.operation_count}, "
#             f"complexity_ratio={self.complexity_ratio}, "
#             f"max_digit_count={self.max_digit_count})"
#         )

#     def to_json(self):
#         """
#         Export to JSON format

#         Returns:
#             (str): JSON string
#         """
#         return json.dumps(self.__dict__)
