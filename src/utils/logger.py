import logging
import os
from logging.handlers import RotatingFileHandler

class LoggerSingleton:
    _instance = None
    _stock_loggers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerSingleton, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger('fcfs')
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            # Use logs/app/ directory (unified logging directory)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_dir = os.path.join(project_root, 'logs', 'app')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'fcfs.log')

            # Clear log file at the start of each run
            try:
                if os.path.exists(log_file):
                    with open(log_file, 'w'):
                        pass
            except Exception as e:
                print(f"Warning: Could not clear log file: {e}")

            formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s (Line: %(lineno)d) - %(levelname)s - %(message)s')

            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

            logging.getLogger('vnstock').setLevel(logging.ERROR)
            logging.getLogger('vnstock').handlers = []
            logging.getLogger('vnstock').addHandler(file_handler)
            logging.getLogger('urllib3').setLevel(logging.WARNING)
            logging.getLogger('requests').setLevel(logging.WARNING)
    
    def get_logger(self):
        return self.logger
    
    def get_stock_logger(self, stock_name):
        """
        Get a stock-specific logger (creates new logger for each stock)
        Format: dcf_{stock_name}.log
        """
        stock_name_lower = stock_name.lower()
        
        if stock_name_lower in self._stock_loggers:
            return self._stock_loggers[stock_name_lower]
        
        # Create new logger for this stock
        logger = logging.getLogger(f'dcf_{stock_name_lower}')
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers = []
        
        # Create log file for this stock
        # Use logs/app/ directory (unified logging directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, 'logs', 'app')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'dcf_{stock_name_lower}.log')
        
        # Clear log file at the start
        try:
            if os.path.exists(log_file):
                with open(log_file, 'w'):
                    pass
        except Exception as e:
            print(f"Warning: Could not clear log file: {e}")
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s (Line: %(lineno)d) - %(levelname)s - %(message)s')
        
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self._stock_loggers[stock_name_lower] = logger
        return logger

def get_logger():
    return LoggerSingleton().get_logger()

def get_stock_logger(stock_name):
    """Get a stock-specific logger"""
    return LoggerSingleton().get_stock_logger(stock_name)
