def calculate_layers(total_elements, num_layers, ratio):
    """
    计算每一层的元素数目，使用比例递减的方法。
    
    :param total_elements: 总元素数目
    :param num_layers: 层数
    :param ratio: 每层相对于上一层的递减比例 (例如，0.8 表示每层是上一层的 80%)
    :return: 每一层的元素数量
    """
    # 计算每一层的元素数目
    x = total_elements / sum([ratio**i for i in range(num_layers)])
    layers = [int(x * ratio**i) for i in range(num_layers)]
    
    # 计算实际的总和
    total_calculated = sum(layers)
    
    # 如果总和不足，补充到目标总数
    if total_calculated < total_elements:
        # 计算剩余的元素数目
        remaining = total_elements - total_calculated
        # 将剩余元素添加到最后一层
        layers[-1] += remaining
    
    return layers

# 示例：500个运算符，5层，比例递减为 0.6
total_elements = 100000
num_layers = 5
ratio = 0.6

# 计算比例递减的每层元素数
layers = calculate_layers(total_elements, num_layers, ratio)
print("比例递减方法 (每层是上一层的 60%):", layers)
