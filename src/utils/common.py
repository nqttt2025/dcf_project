import constants
from configparser import ConfigParser, ExtendedInterpolation

class ConfigHandler(ConfigParser):
    """This class is only responsible for parsing config from path and act as handler"""

    def __init__(self, path, *args, **kargs):
        super().__init__(*args, interpolation=ExtendedInterpolation(), **kargs)
        if path not in self.read(path):
            raise RuntimeError(f"Failed to parse config: {path}")
        
