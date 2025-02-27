import logging
import os

class LogConfig:
    def __init__(self, config: dict):
        self.config = config
        self.logger = self.setup_logging(config)
    
    def setup_logging(self, config: dict) -> logging.Logger:
        """Initialize the logger according to the configuration"""
        log_level = config.get('level', 'DEBUG').upper()
        log_dir = config.get('log_dir', 'logs')
        log_file = config.get('log_file', 'app.log')

        # 打印调试信息，查看读取的配置
        print(f"Log level: {log_level}")
        print(f"Log directory: {log_dir}")
        print(f"Log file: {log_file}")
        
        # 创建日志文件夹（如果不存在的话）
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)

        # 创建日志处理器
        log_path = os.path.join(log_dir, log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)

        # 创建控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # 创建并设置日志记录器
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_logger(self) -> logging.Logger:
        """Get the logger"""
        return self.logger


# 示例：配置文件字典
config = {
    'logging': {
        'level': 'DEBUG',  # 设置为 DEBUG
        'log_dir': 'logs',  # 存储日志的文件夹
        'log_file': 'app.log'  # 日志文件名
    }
}

if __name__ == "__main__":
    log_config = LogConfig(config)
    logger = log_config.get_logger()

    # 测试日志
    logger.debug("Debug message")
    logger.info("Info message")
    logger.error("Error message")
