"""
Container Builder Utilities
Builds containers before testing to ensure latest code is used
"""
import subprocess
import os
import sys
import logging

logger = logging.getLogger(__name__)


class ContainerBuilder:
    """Builds Docker containers before testing"""
    
    def __init__(self, project_root=None):
        """Initialize container builder"""
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.project_root = project_root
    
    def build_containers(self, services=None, no_cache=False):
        """
        Build Docker containers
        
        Args:
            services: List of service names to build (None = all)
            no_cache: Whether to build without cache
        
        Returns:
            bool: True if build successful, False otherwise
        """
        logger.info("Building Docker containers...")
        
        os.chdir(self.project_root)
        
        # Get version from git tag
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                timeout=10
            )
            version = result.stdout.strip() if result.returncode == 0 else "latest"
        except Exception:
            version = "latest"
        
        # Remove -dirty suffix if present
        version = version.replace("-dirty", "")
        
        # Build command
        cmd = ["docker-compose", "build"]
        
        if no_cache:
            cmd.append("--no-cache")
        
        if services:
            cmd.extend(services)
        
        # Set version environment variable
        env = os.environ.copy()
        env["VERSION"] = version
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Containers built successfully")
                return True
            else:
                logger.error(f"Build failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Build timeout")
            return False
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def build_base_image(self, no_cache=False):
        """Build base image"""
        logger.info("Building base image...")
        
        os.chdir(self.project_root)
        
        # Get base version from docker-versions.json
        import json
        versions_file = os.path.join(self.project_root, "docker-versions.json")
        base_version = "latest"
        
        if os.path.exists(versions_file):
            try:
                with open(versions_file, 'r') as f:
                    versions = json.load(f)
                    base_version = versions.get('base', {}).get('current', 'latest')
            except Exception:
                pass
        
        cmd = ["docker", "build"]
        if no_cache:
            cmd.append("--no-cache")
        cmd.extend([
            "-f", "services/common/Dockerfile.base",
            "--build-arg", f"BASE_VERSION={base_version}",
            "-t", f"dcf-project-base:{base_version}",
            "."
        ])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                logger.info("Base image built successfully")
                return True
            else:
                logger.error(f"Base image build failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Base image build error: {e}")
            return False


# Singleton instance
_container_builder = None


def get_container_builder(project_root=None):
    """Get singleton instance of ContainerBuilder"""
    global _container_builder
    if _container_builder is None:
        _container_builder = ContainerBuilder(project_root)
    return _container_builder

