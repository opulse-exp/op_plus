from typing import List, Union, Tuple


class BaseConverter:
    """
    Tool class that converts an integer to a string representation in the specified binary.

    Supports any base between 2 and 36, using numbers and letters as symbols.
    The conversion behavior can be customized by setting different configuration items.
    """

    # 默认字符集：0-9, A-Z
    DEFAULT_DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, max_base=10, digits: str = None):
        """
        Initializes the BaseConverter instance.

        Parameters:
            max_base (int): target base, defaults to 10.
            digits (str): the character set used to represent the value, defaults to the default character set.
        """
        self.max_base = max_base
        self.digits = digits if digits else self.DEFAULT_DIGITS[:max_base]

    def get_digits(self):
        return self.digits
    
    def get_max_base(self):
        return self.max_base

    def convert(self, number: int, base: int) -> str:
        """
        Converts an integer to a string representation in the specified binary.

        Parameters:
            number (int): The integer to be converted.

        Returns:
            (str): The string representation in the specified hexadecimal system.
        """
        if number == 0:
            return f"{self.digits[0]}"

        if number < 0:
            sign = "-"
            number = -number
        else:
            sign = ""

        result = ""
        try:
            while number > 0:
                remainder = number % base
                result = self.digits[remainder] + result
                number = number // base
        except Exception as e:
            print(f"remainder: {remainder}, number: {number}, base: {base} {e}")
            raise e
        return f"{sign}{result}"

    @staticmethod
    def get_supported_bases():
        """
        Return the supported base range
        
        Returns:
            (List[int]): The supported base range.
        """
        return list(range(2, 37))


# # 示例用法
# if __name__ == "__main__":
#     converter = BaseConverter(base=16, prefix=True, suffix=True)
#     print(converter.convert(255))  # 输出: 0xFF_16

#     binary_converter = BaseConverter(base=2, prefix=True)
#     print(binary_converter.convert(-255))  # 输出: -0b11111111

#     octal_converter = BaseConverter(base=8, suffix=True)
#     print(octal_converter.convert(100))  # 输出: 144_8

#     custom_digits_converter = BaseConverter(base=16, digits="0123456789ABCDEF")
#     print(custom_digits_converter.convert(255))  # 输出: FF

#     decimal_converter = BaseConverter(base=10)
#     print(decimal_converter.convert(0))  # 输出: 0
