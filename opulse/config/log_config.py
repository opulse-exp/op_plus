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
        save_file = config.get('save_file', True)  

        print(f"Log level: {log_level}")
        print(f"Log directory: {log_dir}")
        print(f"Log file: {log_file}")
        print(f"Save to file: {save_file}")
        
        os.makedirs(log_dir, exist_ok=True)
        
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger = logging.getLogger()
        logger.setLevel(log_level)
        logger.addHandler(console_handler)

        if save_file:
            log_path = os.path.join(log_dir, log_file)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def get_logger(self) -> logging.Logger:
        """Get the logger"""
        return self.logger

# config = {
#     'logging': {
#         'level': 'DEBUG',  
#         'log_dir': 'logs',  
#         'log_file': 'app.log', 
#         'save_file': True
#     }
# }

# if __name__ == "__main__":
#     log_config = LogConfig(config)
#     logger = log_config.get_logger()

#     logger.debug("Debug message")
#     logger.info("Info message")
#     logger.error("Error message")
