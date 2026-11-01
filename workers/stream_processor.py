# stream_processor.py
import signal
import logging
import time
from typing import List, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    max_retries: int = 3
    retry_delay_ms: int = 1000
    exponential_backoff: bool = True
    max_delay_ms: int = 30000

class StreamProcessor:
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.running = True
        self.shutdown_requested = False
        self.cleanup_handlers: List[Callable] = []
        self.retry_config = retry_config or RetryConfig()
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        # Ignore SIGPIPE to prevent broken pipe errors
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle termination signals gracefully."""
        if self.shutdown_requested:
            # Second interrupt - force immediate exit
            logger.error("Forceful shutdown initiated")
            raise SystemExit(1)
        
        self.shutdown_requested = True
        self.running = False
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received {signal_name}, starting graceful shutdown...")
    
    def add_cleanup_handler(self, handler: Callable) -> None:
        """Add a cleanup function to be called during shutdown."""
        self.cleanup_handlers.append(handler)
    
    def execute_cleanup(self) -> None:
        """Execute all cleanup handlers in reverse order."""
        for handler in reversed(self.cleanup_handlers):
            try:
                handler()
            except Exception as e:
                logger.error(f"Cleanup handler failed: {e}")
    
    def should_continue(self) -> bool:
        """Check if shutdown has been requested."""
        return self.running and not self.shutdown_requested
    
    def calculate_retry_delay(self, retry_count: int) -> int:
        """Calculate delay for retry with exponential backoff."""
        if not self.retry_config.exponential_backoff:
            return self.retry_config.retry_delay_ms
        
        delay = self.retry_config.retry_delay_ms * (2 ** (retry_count - 1))
        return min(delay, self.retry_config.max_delay_ms)