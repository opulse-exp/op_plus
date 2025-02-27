from dataclasses import dataclass
from typing import List
# 配置expression_evaluator的进位信息，target_base为对应的进制下计算进位，carry_flag为是否产生进位
@dataclass
class CarryInfo:
    target_base: int
    carry_flag: bool

@dataclass
class BaseInfo:
    random_flag: bool
    target_base: int
    max_base: int
    custom_digits: List[int]