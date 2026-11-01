import logging

logger = logging.getLogger("my_app.chunker.download_data")

import os
import nltk

def ensure_punkt():
    # Put NLTK data inside your project folder: assets/nltk
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    nltk_data_dir = os.path.join(base_dir, "assets", "nltk")
    os.makedirs(nltk_data_dir, exist_ok=True)

    nltk.data.path.append(nltk_data_dir)
    logger.info(f"Downloading NLTK punkt resources to {nltk_data_dir}.")
    resource = "punkt_tab"
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource, download_dir=nltk_data_dir)



ensure_punkt()
