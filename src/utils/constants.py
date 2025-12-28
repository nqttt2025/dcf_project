import os
from enum import StrEnum

import git

REPO_ROOT = git.Repo(".", search_parent_directories=True).working_tree_dir
DATA_DIR = os.path.join(REPO_ROOT, "data")
CONFIG_DIR = os.path.join(REPO_ROOT, "config")
UTILS_DIR = os.path.join(REPO_ROOT, "utils")
DATABASE_DIR = os.path.join(REPO_ROOT, "database")
COMPANY_DIR = os.path.join(REPO_ROOT, "company")
LOG_DIR = os.path.join(REPO_ROOT, "logs", "app")
DOCKER_LOG_DIR = os.path.join(REPO_ROOT, "logs", "docker")
TEST_DIR = os.path.join(REPO_ROOT, "tests")