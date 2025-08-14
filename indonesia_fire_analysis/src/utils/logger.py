"""Logging configuration for Indonesia fire analysis."""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"fire_analysis_{timestamp}.log"
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")


class ProgressLogger:
    """Custom progress logger for long-running operations."""
    
    def __init__(self, total_items: int, operation_name: str):
        """
        Initialize progress logger.
        
        Args:
            total_items: Total number of items to process
            operation_name: Name of the operation being performed
        """
        self.total_items = total_items
        self.operation_name = operation_name
        self.processed_items = 0
        self.logger = logging.getLogger(__name__)
        
    def update(self, items_processed: int = 1) -> None:
        """
        Update progress counter.
        
        Args:
            items_processed: Number of items processed in this update
        """
        self.processed_items += items_processed
        progress_pct = (self.processed_items / self.total_items) * 100
        
        if self.processed_items % max(1, self.total_items // 10) == 0:
            self.logger.info(
                f"{self.operation_name}: {self.processed_items}/{self.total_items} "
                f"({progress_pct:.1f}%) completed"
            )
    
    def complete(self) -> None:
        """Log completion message."""
        self.logger.info(f"{self.operation_name}: Completed processing {self.total_items} items")