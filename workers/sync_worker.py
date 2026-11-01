from utils import logging_config  # applies logging
import logging

logger = logging.getLogger("my_app.sync_worker")


from .worker_stream import SyncWorker
# -------------------------------------
# Main function
# -------------------------------------
def main():
    """Main entry point for the worker."""
    # Configure more detailed logging for production
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    worker = SyncWorker()
    worker.process_stream()

if __name__ == "__main__":
    main()