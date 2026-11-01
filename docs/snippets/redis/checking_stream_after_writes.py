

import logging
import os
import signal
from typing import Dict
from infrastructure.cache import redis_client
#from workers.sync_worker import _process_and_ack  # infrastructure/cache.py alias
logger = logging.getLogger(__name__)


STREAM = os.getenv("NOTES_STREAM", "notes:events")
DLQ_STREAM = f"{STREAM}:dlq"  # dead-letter stream for failed events
BLOCK_MS = int(os.getenv("STREAM_BLOCK_MS", "2000"))
BATCH = int(os.getenv("STREAM_BATCH", "100"))
GROUP = os.getenv("STREAM_GROUP", "sync-workers")
CONSUMER = os.getenv("STREAM_CONSUMER", f"worker-{os.getpid()}")


class Stream_redis():
    def __init__(self, stream_name: str):
        self.stream_name = stream_name
        self.running = True
    """
    signum is the signal number.
    signal number is used to identify the specific signal that was received.
    example: signal.SIGTERM is used to terminate the process.
    frame is the current stack frame.
    """
    def _handle_sigterm(self, signum, frame):
        """Graceful shutdown handler."""
        self.running = False

    """
    Reads entries in order (oldest → newest).
    XRANGE <stream> <start> <end>
    Use - for the minimum and + for the maximum.
    """
    def read_entries(self):
        print(f"[Stream] Reading entries from {self.stream_name}")
        entries = redis_client.xrange(self.stream_name)
        # Example: entries = r.xrange("mystream", min="-", max="+")
        for entry_id, fields in entries:
            print(entry_id, fields)


    """
    XREVRANGE — Read Reverse
    Reads entries in reverse (newest → oldest).
    Use + for the maximum and - for the minimum.
    """
    def read_entries_reverse(self):
        print(f"[Stream] Reading entries in reverse from {self.stream_name}")
        entries = redis_client.xrevrange(self.stream_name, max="+", min="-")
        for entry_id, fields in entries:
            print(entry_id, fields)

    """
    XREAD — Non-blocking Read
    from one or more streams starting at a specific ID.
    - $ means only new entries after now.
    - 0 means read from the beginning.
    """

    def read_entries_blocking(self):
        print(f"[Stream] Non-blocking Read from {self.stream_name}")
        entries = redis_client.xread({self.stream_name: "$"})
        # entries = redis_client.xread({self.stream_name: "0"})
        for stream, messages in entries:
            print(f"[Stream] New messages in {stream}:")
            for message_id, fields in messages:
                print(message_id, fields)
    
    """
    XREAD with BLOCK — Blocking Read
    Waits until new entries arrive.
    - BLOCK <ms> waits for up to N milliseconds.
    - Useful for event-driven consumers.
    """
    def read_entries_blocking(self):
        print(f"[Stream] Blocking Read from {self.stream_name}")
        entries = redis_client.xread({self.stream_name: "$"}, block=0)
        for stream, messages in entries:
            print(f"[Stream] New messages in {stream}:")
            for message_id, fields in messages:
                print(message_id, fields)
    
    """
    Ensure the consumer group exists.

    The mkstream=True argument is also very important.
    It tells Redis: "If the stream mystream doesn't exist yet,
      go ahead and create it for me."

    - Without mkstream=True, if mystream doesn't exist, 
        the XGROUP CREATE command will fail with an error.
    - With mkstream=True, the command will create 
        the empty stream and then create the group pointing to it.
    """
    def __ensure_group(self) -> None:
        try:
            
            redis_client.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
            logger.info(f"Created consumer group {GROUP} on {STREAM}")
            
        except Exception:
            # If group already exists, ignore
            logger.info(f"Consumer group {GROUP} already exists on {STREAM}")
    def process_stream(self):
        self.__ensure_group()
        self.running = True
        while self.running:
            pending = redis_client.xreadgroup(
                GROUP, CONSUMER, streams={STREAM: "0"}, count=BATCH
            )
            if not pending:
                break
        #_process_and_ack(svc, pending)       

def main():
    
    # Create a Stream_redis instance
    t_xrange = Stream_redis(STREAM)

    """
    - Setup signal handlers for graceful shutdown.
    - signal is used to handle termination signals.
    - Handling termination signals is important to ensure
        that the application can shut down gracefully.
    - Without proper handling, the application may
        terminate abruptly, leading to potential data loss.
    
    """
    signal.signal(signal.SIGINT, t_xrange._handle_sigterm)
    signal.signal(signal.SIGTERM, t_xrange._handle_sigterm)
    # Start processing the stream
    t_xrange.process_stream()

# Add this at the end of your file
if __name__ == "__main__":
    # Configure logging to see output
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    t_xrange = Stream_redis(STREAM)

    # t_xrange.read_entries()
    # t_xrange.read_entries_blocking()
    # t_xrange.read_entries_reverse()
   
    t_xrange.process_stream()