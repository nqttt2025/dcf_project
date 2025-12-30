"""
Service-specific logger with rotation and performance optimization
"""
import logging
import os
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict
import queue
import atexit

# Thread-safe queue for async logging (maxsize để tránh memory leak)
_log_queue = queue.Queue(maxsize=1000)
_log_thread = None
_log_thread_running = False

class LineLimitedRotatingFileHandler(RotatingFileHandler):
    """
    RotatingFileHandler với giới hạn số dòng log (10k lines)
    """
    def __init__(self, filename, max_lines=10000, max_bytes=5*1024*1024, backup_count=5, **kwargs):
        # Remove backup_count from kwargs nếu có để tránh duplicate
        kwargs.pop('backupCount', None)
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count, **kwargs)
        self.max_lines = max_lines
        self.current_lines = 0
        self._lock = threading.Lock()
        
        # Đếm số dòng hiện tại trong file
        self._count_lines()
    
    def _count_lines(self):
        """Đếm số dòng trong file hiện tại"""
        try:
            if os.path.exists(self.baseFilename):
                with open(self.baseFilename, 'r', encoding='utf-8', errors='ignore') as f:
                    self.current_lines = sum(1 for _ in f)
        except Exception:
            self.current_lines = 0
    
    def emit(self, record):
        """Ghi log với kiểm tra số dòng"""
        with self._lock:
            if self.current_lines >= self.max_lines:
                # Rotate log file
                self.doRollover()
                self.current_lines = 0
            
            super().emit(record)
            self.current_lines += 1

class AsyncLogHandler(logging.Handler):
    """
    Async log handler để tối ưu hiệu năng
    """
    def __init__(self, target_handler):
        super().__init__()
        self.target_handler = target_handler
        self.queue = _log_queue
        self._start_thread()
    
    def _start_thread(self):
        """Start background thread để xử lý logs"""
        global _log_thread, _log_thread_running
        
        if _log_thread is None or not _log_thread.is_alive():
            _log_thread_running = True
            _log_thread = threading.Thread(target=self._process_logs, daemon=True)
            _log_thread.start()
            atexit.register(self._stop_thread)
    
    def _process_logs(self):
        """Process logs từ queue"""
        global _log_thread_running
        while _log_thread_running:
            try:
                record = self.queue.get(timeout=1)
                if record is None:  # Sentinel để dừng thread
                    break
                self.target_handler.emit(record)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Fallback: log trực tiếp nếu có lỗi
                try:
                    self.target_handler.emit(record)
                except:
                    pass
    
    def _stop_thread(self):
        """Stop background thread"""
        global _log_thread_running
        _log_thread_running = False
        self.queue.put(None)  # Sentinel
    
    def emit(self, record):
        """Add log record vào queue"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # Nếu queue đầy, log trực tiếp (fallback)
            try:
                self.target_handler.emit(record)
            except:
                pass
    
    def close(self):
        """Close handler"""
        self._stop_thread()
        if self.target_handler:
            self.target_handler.close()
        super().close()

class ServiceLoggerSingleton:
    """
    Singleton class để quản lý service loggers
    Đảm bảo mỗi service chỉ có một logger instance
    """
    _instance = None
    _lock = threading.Lock()
    _loggers: Dict[str, logging.Logger] = {}
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern: chỉ tạo một instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ServiceLoggerSingleton, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize singleton (chỉ chạy một lần)"""
        if self._initialized:
            return
        self._initialized = True
        self._loggers = {}
    
    def get_logger(self, service_name: str, log_dir: Optional[str] = None,
                   max_lines: int = 10000, max_bytes: int = 5*1024*1024,
                   backup_count: int = 5, use_async: bool = True,
                   level: int = logging.INFO) -> logging.Logger:
        """
        Get hoặc tạo logger cho service (Singleton pattern)
        
        Args:
            service_name: Tên service (gateway, dcf, stock, database)
            log_dir: Thư mục lưu log (default: logs/app)
            max_lines: Số dòng tối đa trong mỗi file log (default: 10000)
            max_bytes: Kích thước tối đa mỗi file log (default: 5MB)
            backup_count: Số file backup (default: 5)
            use_async: Sử dụng async logging (default: True)
            level: Log level (default: INFO)
        
        Returns:
            Configured logger instance (singleton)
        """
        # Kiểm tra xem logger đã tồn tại chưa
        if service_name in self._loggers:
            return self._loggers[service_name]
        
        # Thread-safe creation
        with self._lock:
            # Double-check sau khi acquire lock
            if service_name in self._loggers:
                return self._loggers[service_name]
            
            # Tạo logger mới
            logger = logging.getLogger(f'service.{service_name}')
            
            # Đảm bảo logger chưa có handlers (tránh duplicate)
            if logger.handlers:
                # Nếu đã có handlers, remove và tạo lại để đảm bảo consistency
                logger.handlers.clear()
            
            logger.setLevel(level)
            
            # Setup log directory
            if log_dir is None:
                from .common import get_project_root_str
                project_root = get_project_root_str()
                log_dir = os.path.join(project_root, 'logs', 'app')
            
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'{service_name}.log')
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # File handler với giới hạn số dòng
            file_handler = LineLimitedRotatingFileHandler(
                log_file,
                max_lines=max_lines,
                max_bytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            
            # Wrap với async handler nếu enabled
            if use_async:
                async_file_handler = AsyncLogHandler(file_handler)
                async_console_handler = AsyncLogHandler(console_handler)
                logger.addHandler(async_file_handler)
                logger.addHandler(async_console_handler)
            else:
                logger.addHandler(file_handler)
                logger.addHandler(console_handler)
            
            # Suppress noisy loggers (chỉ suppress một lần)
            if not hasattr(self, '_suppressed_loggers'):
                logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
                logging.getLogger('uvicorn.error').setLevel(logging.WARNING)
                logging.getLogger('httpx').setLevel(logging.WARNING)
                logging.getLogger('httpcore').setLevel(logging.WARNING)
                self._suppressed_loggers = True
            
            # Cache logger instance
            self._loggers[service_name] = logger
            
            return logger
    
    def get_all_loggers(self) -> Dict[str, logging.Logger]:
        """Get tất cả loggers đã được tạo"""
        return self._loggers.copy()
    
    def clear_logger(self, service_name: str):
        """Clear logger cho một service (dùng cho testing)"""
        with self._lock:
            if service_name in self._loggers:
                logger = self._loggers[service_name]
                # Close all handlers
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
                del self._loggers[service_name]
    
    def clear_all_loggers(self):
        """Clear tất cả loggers (dùng cho testing)"""
        with self._lock:
            for service_name, logger in list(self._loggers.items()):
                for handler in logger.handlers[:]:
                    handler.close()
                    logger.removeHandler(handler)
            self._loggers.clear()

# Global singleton instance
_service_logger_singleton = ServiceLoggerSingleton()

def setup_service_logger(service_name: str, log_dir: Optional[str] = None,
                        max_lines: int = 10000, max_bytes: int = 5*1024*1024,
                        backup_count: int = 5, use_async: bool = True,
                        level: int = logging.INFO) -> logging.Logger:
    """
    Setup logger cho service với rotation và tối ưu hiệu năng
    Sử dụng Singleton pattern để đảm bảo mỗi service chỉ có một logger instance
    
    Args:
        service_name: Tên service (gateway, dcf, stock, database)
        log_dir: Thư mục lưu log (default: logs/app)
        max_lines: Số dòng tối đa trong mỗi file log (default: 10000)
        max_bytes: Kích thước tối đa mỗi file log (default: 5MB)
        backup_count: Số file backup (default: 5)
        use_async: Sử dụng async logging (default: True)
        level: Log level (default: INFO)
    
    Returns:
        Configured logger instance (singleton)
    """
    return _service_logger_singleton.get_logger(
        service_name=service_name,
        log_dir=log_dir,
        max_lines=max_lines,
        max_bytes=max_bytes,
        backup_count=backup_count,
        use_async=use_async,
        level=level
    )

def cleanup_old_logs(log_dir: str, max_files_per_service: int = 10):
    """
    Cleanup old log files để tránh disk đầy
    
    Args:
        log_dir: Thư mục chứa logs
        max_files_per_service: Số file tối đa cho mỗi service (bao gồm backups)
    """
    try:
        if not os.path.exists(log_dir):
            return
        
        # Group files by service name
        service_files = {}
        
        for filename in os.listdir(log_dir):
            if not filename.endswith('.log'):
                continue
            
            # Extract service name (remove .log và backup numbers)
            service_name = filename.replace('.log', '').split('.')[0]
            
            if service_name not in service_files:
                service_files[service_name] = []
            
            filepath = os.path.join(log_dir, filename)
            mtime = os.path.getmtime(filepath)
            service_files[service_name].append((filepath, mtime))
        
        # Cleanup cho mỗi service
        for service_name, files in service_files.items():
            if len(files) <= max_files_per_service:
                continue
            
            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x[1])
            
            # Remove oldest files
            files_to_remove = files[:-max_files_per_service]
            for filepath, _ in files_to_remove:
                try:
                    os.remove(filepath)
                    logging.getLogger(f'service.{service_name}').info(
                        f"Removed old log file: {os.path.basename(filepath)}"
                    )
                except Exception as e:
                    logging.getLogger(f'service.{service_name}').warning(
                        f"Failed to remove log file {filepath}: {e}"
                    )
    except Exception as e:
        # Use basic logger để tránh circular dependency
        print(f"Error cleaning up logs: {e}")

