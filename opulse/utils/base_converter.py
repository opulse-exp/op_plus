import random

class BaseConverter:
    """
    Classes for converting between arbitrary alphabets, with support for arbitrary alphabets (up to a custom base).
    Support for extending the representation of values by passing in an external character set.
    #TODO: you can follow the yaml file in the config to configure , set the maximum base and numeric character set .
    """
    def __init__(self, max_base=36, custom_digits=None):
        """
        Initializes the BaseConverter class to allow custom character sets.

        Parameters: 
            max_base (int): the maximum supported base.
            custom_digits (str, optional): customized character set for representing values in larger base.
        """
        if custom_digits:
            self.digits = custom_digits
        else:
            self.digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.max_base = max_base

    def to_base(self, value: int, base: int) -> str:
        """
        Converts a decimal integer to a string representation of the specified base.

        Parameters: value (int)
            value (int): the decimal integer to be converted. (Since only positive numbers are used for match-and-replace)
            base (int): target base (2-max).

        Returns:
            str: The string representation of the specified base.
        """
        if base < 2 or base > self.max_base:
            raise ValueError(f"Base must be between 2 and {self.max_base}")
        
        if value == 0:
            return self.digits[0]
        
        is_negative = value < 0
        n = abs(value)
        result = ""
        
        while n > 0:
            result = self.digits[n % base] + result
            n //= base
        
        # 如果是负数，添加负号
        return "-" + result if is_negative else result

    def from_base(self, value_str: str, base: int) -> int:
        """
        Converts a string representation of the specified binary to a decimal integer.

        Arguments: 
            value_str (str): the string representation in the specified base.
            base (int): the base (2-max) of the string.

        Returns:
            (int): the converted decimal integer.
        """
        if base < 2 or base > self.max_base:
            raise ValueError(f"Base must be between 2 and {self.max_base}")
        
        is_negative = value_str[0] == "-"
        if is_negative:
            value_str = value_str[1:]
        
        # 将字符串从高位到低位逐位转换成整数
        n = 0
        for char in value_str:
            n = n * base + self.digits.index(char)
        
        return -n if is_negative else n

    def generate_random_number(self, base: int, length: int) -> str:
        """
        Generates a random string of numbers based on the specified binary.

        Parameters.
            base (int): the base (between 2 and the largest base).
            length (int): length of the random number.

        Returns: 
            (str): A randomly generated numeric string in the specified base.
        """
        if base < 2 or base > self.max_base:
            raise ValueError(f"Base must be between 2 and {self.max_base}")
        
        # 从符号集中选择字符，生成指定长度的随机数
        return ''.join(random.choice(self.digits[:base]) for _ in range(length))


# 示例使用
if __name__ == "__main__":
    # 使用自定义字符集，允许更多的字符
    custom_digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"  # 自定义符号集
    converter = BaseConverter(max_base=32, custom_digits=custom_digits)  # 假设最大支持128进制

    # 转换示例
    print(converter.to_base(255, 2))   # 转换为二进制
    print(converter.to_base(255, 16))  # 转换为16进制


    # 反向转换示例
    print(converter.from_base("11111111", 2))   # 从二进制转换为十进制
    print(converter.from_base("FF", 16))         # 从16进制转换为十进制
    print(converter.from_base("73", 36))         # 从36进制转换为十进制
    print(converter.from_base("3E", 64))         # 从64进制转换为十进制

    # 随机生成数字示例
    print(converter.generate_random_number(128, 8))  # 生成一个8位的128进制随机数
    print(converter.generate_random_number(128, 6))  # 生成一个6位的128进制随机数
