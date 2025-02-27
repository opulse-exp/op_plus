import yaml
import os

class ParamConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config(config_path)
        self.atoms = self.load_atoms()
    
    def load_config(self, config_path: str) -> dict:
        """Load Configuration File"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file {config_path} does not exist")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)  # 使用 yaml 库读取配置文件
        return config

    def get(self, key: str, default=None):
        """Get configuration parameters by key"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Set configuration parameters"""
        self.config[key] = value

    def save(self):
        """Save Configuration File"""
        with open(self.config_path, 'w') as file:
            yaml.safe_dump(self.config, file)
    
    def load_atoms(self) -> dict:
        """Load atomic data, generate numerical atoms and other symbols"""
        # 获取配置参数
        self.max_base = self.get("max_base", 36)  # 默认最大基数为 36
        self.custom_digits = self.get("custom_digits", "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        variable_atoms = self.get("variable_atoms", [])
        left_operand = variable_atoms[0]["left_operand"] if len(variable_atoms) > 0 else "a"
        right_operand = variable_atoms[1]["right_operand"] if len(variable_atoms) > 1 else "b"

        # 生成数值原子，从 0 到 max_base - 1，并使用 custom_digits 映射
        numeric_atoms = [self.custom_digits[i] for i in range(self.max_base)]

        # 获取其他符号
        left_parenthesis = self.get("other_symbols_atoms", {}).get("left_parenthesis", "(")
        right_parenthesis = self.get("other_symbols_atoms", {}).get("right_parenthesis", ")")
        nan_symbol = self.get("other_symbols_atoms", {}).get("nan_symbol", "NaN")
        equal_sign = self.get("other_symbols_atoms", {}).get("equal_sign", "=")

        # 生成的原子数据
        atoms = {
            "left_operand": left_operand,  # 如果有配置就使用配置的值，否则使用默认值 "a"
            "right_operand": right_operand,  # 同上
            "numeric_atoms": numeric_atoms,  # 生成的数值原子列表
            "left_parenthesis": left_parenthesis,
            "right_parenthesis": right_parenthesis,
            "nan": nan_symbol,
            "equal": equal_sign,
        }

        return atoms

    def get_logging_config(self) -> dict:
        """Extract and return log configuration section"""
        logging_config = self.get("logging", {})
        return logging_config

# 示例: 创建 ParamConfig 实例并访问配置
if __name__ == "__main__":
    config = ParamConfig('/map-vepfs/kaijing/exp_mechanicalinterpretability/Opulse/opulse/config/default.yaml')
    print(config.atoms)  # 获取配置项，默认值为 INFO
