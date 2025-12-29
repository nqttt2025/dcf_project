"""
Common utilities for configuration handling and path resolution
"""
import os
from pathlib import Path
from configparser import ConfigParser, ExtendedInterpolation


def get_project_root() -> Path:
    """
    Get project root directory.
    Works from any file in the project by going up from src/utils/.
    
    Returns:
        Path: Project root directory
    """
    # Get the directory of this file (src/utils/)
    utils_dir = Path(__file__).parent
    # Go up 2 levels to get project root
    return utils_dir.parent.parent


def get_project_root_str() -> str:
    """
    Get project root directory as string.
    
    Returns:
        str: Project root directory path
    """
    return str(get_project_root())


class ConfigHandler(ConfigParser):
    """This class is only responsible for parsing config from path and act as handler"""

    def __init__(self, path, *args, **kargs):
        super().__init__(*args, interpolation=ExtendedInterpolation(), **kargs)
        if path not in self.read(path):
            raise RuntimeError(f"Failed to parse config: {path}")

