class SpecialValue:
    def __init__(self, value):
        self.value = value  # value 用来区分正无穷、负无穷和 NaN

    # 重载小于运算符
    def __lt__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return False

        if isinstance(other, SpecialValue):
            if self.value == float("inf") and other.value == float("-inf"):
                return False
            if self.value == float("-inf") and other.value == float("inf"):
                return True
            return self.value < other.value

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return False
            if self.value == float("-inf"):
                return True
            return self.value < other

        return False

    # 重载大于运算符
    def __gt__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return False

        if isinstance(other, SpecialValue):
            if self.value == float("inf") and other.value == float("-inf"):
                return True
            if self.value == float("-inf") and other.value == float("inf"):
                return False
            return self.value > other.value

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return True
            if self.value == float("-inf"):
                return False
            return self.value > other

        return False

    # 重载等于运算符
    def __eq__(self, other):
        if isinstance(other, SpecialValue):
            return self.value == other.value

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            return self.value == other

        return False

    # 重载不等于运算符
    def __ne__(self, other):
        return not self.__eq__(other)

    # 重载小于等于运算符
    def __le__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return False
        return self.__lt__(other) or self.__eq__(other)

    # 重载大于等于运算符
    def __ge__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return False
        return self.__gt__(other) or self.__eq__(other)

    def __repr__(self):
        if self.value != self.value:  # 如果是 NaN，显示为 NaN
            return "SpecialValue(NaN)"
        return f"SpecialValue({self.value})"  # 方便打印输出

    # 重载加法运算符
    def __add__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            # 有问题
            if self.value == float("inf") and other.value == float("-inf"):
                return 0  # 直接返回 int(0)
            if self.value == float("inf") or other.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf") or other.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return SpecialValue(self.value + other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return self.value + other

        return SpecialValue(float("nan"))

    # 重载减法运算符
    def __sub__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return SpecialValue(self.value - other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return self.value - other

        return SpecialValue(float("nan"))

    # 重载乘法运算符
    def __mul__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            if self.value == float("inf") or other.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf") or other.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return SpecialValue(self.value * other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return SpecialValue(self.value * other)

        return SpecialValue(float("nan"))

    # 重载除法运算符
    def __truediv__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            if other.value == float("inf"):
                return SpecialValue(0)
            if other.value == float("-inf"):
                return SpecialValue(0)
            return SpecialValue(self.value / other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            if other == 0:
                return SpecialValue(float("inf"))
            return SpecialValue(self.value / other)

        return SpecialValue(float("nan"))

    # 重载整除运算符
    def __floordiv__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            if self.value == float("inf") or other.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf") or other.value == float("-inf"):
                return SpecialValue(float("-inf"))
            return SpecialValue(self.value // other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            if other == 0:
                return SpecialValue(float("inf"))
            return SpecialValue(self.value // other)

        return SpecialValue(float("nan"))

    # 重载取模运算符
    def __mod__(self, other):
        if self.value != self.value or (
            isinstance(other, SpecialValue) and other.value != other.value
        ):
            return SpecialValue(float("nan"))

        if isinstance(other, SpecialValue):
            if self.value == float("inf") or other.value == float("inf"):
                return SpecialValue(float("nan"))
            if self.value == float("-inf") or other.value == float("-inf"):
                return SpecialValue(float("nan"))
            return SpecialValue(self.value % other.value)

        if isinstance(other, (int, float)):  # 支持与普通数字的比较
            if self.value == float("inf"):
                return SpecialValue(float("inf"))
            if self.value == float("-inf"):
                return SpecialValue(float("-inf"))
            if other == 0:
                return SpecialValue(float("nan"))
            return SpecialValue(self.value % other)

        return SpecialValue(float("nan"))


# 对于加减乘除，python内置的
# 加
# inf+1=inf, -inf+1=-inf
# inf+inf=inf, -inf+(-inf)=-inf
# inf+(-inf)=nan
# 减
# inf-1=inf, -inf-1=-inf
# inf-inf =nan  -inf-(-inf)=nan
# inf-(-inf)=inf, -inf-(inf)=-inf
# 乘
# inf*2=inf, -inf*2=-inf
# inf*inf=inf,inf*(-inf)=-inf,(-inf)*(-inf)=inf
# inf*0 = nan
# 除
# inf//2=nan(需要改) inf//inf=nan
# 取余
# inf % 2 =nan 


# 测试
# 创建特殊值对象
POS_INF = SpecialValue(float("inf"))
NEG_INF = SpecialValue(float("-inf"))
NaN = SpecialValue(float("nan"))

# # 测试特殊值之间的比较
# print(POS_INF < NEG_INF)
# assert False == False
# assert (POS_INF < NEG_INF) == False
# assert (NEG_INF < POS_INF) == True
# assert (POS_INF < POS_INF) == False
# assert (NEG_INF < NEG_INF) == False

# # 测试 NaN
# assert (5 < NaN) == False
# assert (POS_INF < NaN) == False
# assert (POS_INF < 5) == False
# assert (NaN < NaN) == False
# assert (NEG_INF < NaN) == False
# assert (NEG_INF < 5) == True

# print("===========================")

# # 测试特殊值之间的比较
# assert (POS_INF > NEG_INF) == True
# assert (NEG_INF > POS_INF) == False
# assert (POS_INF > POS_INF) == False
# assert (NEG_INF > NEG_INF) == False

# # 测试 NaN
# assert 5 > NaN == False
# assert (POS_INF > NaN) == True
# assert (NaN > NaN) == False
# assert (NEG_INF > NaN) == False

# print("===========================")

# # 小于等于 (<=) 测试
# assert (POS_INF <= NEG_INF) == False
# assert (NEG_INF <= POS_INF) == True
# assert (POS_INF <= POS_INF) == True
# assert (NEG_INF <= NEG_INF) == True

# print("===========================")
# # 大于等于 (>=) 测试
# assert (POS_INF >= NEG_INF) == True
# assert (NEG_INF >= POS_INF) == False
# assert (POS_INF >= POS_INF) == True
# assert (NEG_INF >= NEG_INF) == True

# print("===========================")
# # 不等于 (!=) 测试
# assert (POS_INF != NEG_INF) == True
# assert (NEG_INF != POS_INF) == True
# assert (POS_INF != POS_INF) == False
# assert (NEG_INF != NEG_INF) == False

# print("===========================")
# # 加法 (+) 测试
# assert (POS_INF + NEG_INF).value == float("nan")  # Inf + -Inf == NaN
# assert (POS_INF + 5).value == float("inf")  # Inf + 5 == Inf
# assert (NEG_INF + 5).value == float("-inf")  # -Inf + 5 == -Inf
# assert (NaN + 5).value == float("nan")  # NaN + 5 == NaN
# assert (5 + NaN).value == float("nan")  # 5 + NaN == NaN

# print("===========================")
# # 减法 (-) 测试
# assert (POS_INF - NEG_INF).value == float("nan")  # Inf - -Inf == NaN
# assert (POS_INF - 5).value == float("inf")  # Inf - 5 == Inf
# assert (NEG_INF - 5).value == float("-inf")  # -Inf - 5 == -Inf
# assert (NaN - 5).value == float("nan")  # NaN - 5 == NaN
# assert (5 - NaN).value == float("nan")  # 5 - NaN == NaN

# print("===========================")
# # 乘法 (*) 测试
# assert (POS_INF * NEG_INF).value == float("-inf")  # Inf * -Inf == -Inf
# assert (POS_INF * 5).value == float("inf")  # Inf * 5 == Inf
# assert (NEG_INF * 5).value == float("-inf")  # -Inf * 5 == -Inf
# assert (NaN * 5).value == float("nan")  # NaN * 5 == NaN
# assert (5 * NaN).value == float("nan")  # 5 * NaN == NaN

# print("===========================")
# # 除法 (/) 测试
# assert (POS_INF / NEG_INF).value == float("-inf")  # Inf / -Inf == -Inf
# assert (POS_INF / 5).value == float("inf")  # Inf / 5 == Inf
# assert (NEG_INF / 5).value == float("-inf")  # -Inf / 5 == -Inf
# assert (NaN / 5).value == float("nan")  # NaN / 5 == NaN
# assert (5 / NaN).value == float("nan")  # 5 / NaN == NaN

# print("===========================")
# # 取模 (%) 测试
# assert (POS_INF % NEG_INF).value == float("nan")  # Inf % -Inf == NaN
# assert (POS_INF % 5).value == float("inf")  # Inf % 5 == Inf
# assert (NEG_INF % 5).value == float("-inf")  # -Inf % 5 == -Inf
# assert (NaN % 5).value == float("nan")  # NaN % 5 == NaN
# assert (5 % NaN).value == float("nan")  # 5 % NaN == NaN
# assert (5 % 2).value == 1  # 5 % 2 == 1

# print("All tests passed!")


# 创建特殊值对象
POS_INF = float("inf")
NEG_INF = float("-inf")
NaN = float("nan")

# 测试 POS_INF 和 int 的比较
assert (POS_INF < 5) == False  # POS_INF 大于任何有限数字
assert (POS_INF > 5) == True  # POS_INF 大于任何有限数字
assert (POS_INF == 5) == False  # POS_INF 不等于任何有限数字
assert (POS_INF != 5) == True  # POS_INF 不等于任何有限数字

# 测试 NEG_INF 和 int 的比较
assert (NEG_INF < 5) == True  # NEG_INF 小于任何有限数字
assert (NEG_INF > 5) == False  # NEG_INF 小于任何有限数字
assert (NEG_INF == 5) == False  # NEG_INF 不等于任何有限数字
assert (NEG_INF != 5) == True  # NEG_INF 不等于任何有限数字

# 测试 NaN 和 int 的比较
assert (NaN < 5) == False  # NaN 和任何数比较结果为 False
assert (NaN > 5) == False  # NaN 和任何数比较结果为 False
assert (NaN == 5) == False  # NaN 不等于任何数字
assert (NaN != 5) == True  # NaN 不等于任何数字

POS_INF = float("inf")  # 浮点数中的正无穷大
# 如果将 POS_INF 转换为整数，结果会变成最大可表示的整数
INT_POS_INF = int(POS_INF)

result = INT_POS_INF * 0
print(result)  # 输出: 0
