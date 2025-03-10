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
            config = yaml.safe_load(file)  
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
        self.max_base = self.get("max_base", 36) #Default maximal base is 36.
        self.custom_digits = self.get("custom_digits", "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        variable_atoms = self.get("variable_atoms", [])
        left_operand = variable_atoms[0]["left_operand"] if len(variable_atoms) > 0 else "a"
        right_operand = variable_atoms[1]["right_operand"] if len(variable_atoms) > 1 else "b"

        # Generate numeric atoms from 0 to max_base - 1 and map them using custom_digits.
        numeric_atoms = [self.custom_digits[i] for i in range(self.max_base)]


        left_parenthesis = self.get("other_symbols_atoms", {}).get("left_parenthesis", "(")
        right_parenthesis = self.get("other_symbols_atoms", {}).get("right_parenthesis", ")")
        nan_symbol = self.get("other_symbols_atoms", {}).get("nan_symbol", "NaN")
        equal_sign = self.get("other_symbols_atoms", {}).get("equal_sign", "=")

        atoms = {
            "left_operand": left_operand,  
            "right_operand": right_operand,  
            "numeric_atoms": numeric_atoms,  
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


