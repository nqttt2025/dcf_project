import configparser
import os
from logger import get_logger

logger = get_logger()


class ConfigManager:
    """
    Singleton class to manage DCF configuration from config file.
    Reads from DCF.cfg and provides configuration parameters.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(os.path.dirname(__file__), 'DCF.cfg')
        
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            logger.info(f"Loaded config from {self.config_file}")
        else:
            logger.warning(f"Config file not found at {self.config_file}, using defaults")
    
    def get_dcf_params(self):
        """Get DCF parameters (yr, dr, pr)"""
        try:
            return {
                'yr': self.config.getint('dcf', 'yr', fallback=5),
                'dr': self.config.getfloat('dcf', 'dr', fallback=10.0),
                'pr': self.config.getfloat('dcf', 'pr', fallback=2.5),
            }
        except Exception as e:
            logger.error(f"Error reading DCF parameters: {e}")
            return {'yr': 5, 'dr': 10.0, 'pr': 2.5}
    
    def get_graham_params(self):
        """Get Graham valuation parameters"""
        try:
            return {
                'base_pe': self.config.getfloat('graham', 'base_pe', fallback=8.5),
                'growth_multiplier': self.config.getfloat('graham', 'growth_multiplier', fallback=2.0),
            }
        except Exception as e:
            logger.error(f"Error reading Graham parameters: {e}")
            return {'base_pe': 8.5, 'growth_multiplier': 2.0}
    
    def get_ticker(self):
        """Get ticker to analyze"""
        try:
            return self.config.get('ticker', 'ticker', fallback='FPT')
        except Exception as e:
            logger.error(f"Error reading ticker: {e}")
            return 'FPT'
    
    def get_data_source(self):
        """Get data source"""
        try:
            return self.config.get('data_source', 'source', fallback='VCI')
        except Exception as e:
            logger.error(f"Error reading data source: {e}")
            return 'VCI'
    
    def get_all_params(self):
        """Get all parameters as a single dictionary"""
        return {
            **self.get_dcf_params(),
            **self.get_graham_params(),
            'ticker': self.get_ticker(),
            'source': self.get_data_source(),
        }
    
    def log_config(self):
        """Log current configuration"""
        params = self.get_all_params()
        logger.info("=" * 60)
        logger.info("Current Configuration:")
        logger.info("=" * 60)
        for key, value in params.items():
            logger.info(f"{key:20} = {value}")
        logger.info("=" * 60)


def get_config_manager():
    """Factory function to get or create ConfigManager singleton"""
    return ConfigManager()


if __name__ == "__main__":
    config_mgr = get_config_manager()
    config_mgr.log_config()
