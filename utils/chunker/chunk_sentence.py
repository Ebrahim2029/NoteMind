"""
Multilingual chunker for splitting notes into chunks by sentence boundaries.
Uses NLTK for sentence segmentation and tiktoken for token counting.
"""

from email.mime import text
from typing import List
import nltk
import tiktoken

# OpenAI tokenizer
_enc = tiktoken.get_encoding("cl100k_base")


def split_words(text: str) -> List[str]:
    wordsArray = nltk.word_tokenize(text)
    return wordsArray

def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 10,
) -> List[tuple[int, str]]:
    """
    Split text into chunks by sentences, preserving meaning.
    Returns list of (chunk_index, chunk_text).
    """

    sentences = split_words(text)


    chunks = []
    current_chunk = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = len(_enc.encode(sent))

        if current_tokens + sent_tokens > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))

            # Overlap
            overlap_sents = current_chunk[-overlap:] if overlap else []
            current_chunk = overlap_sents + [sent]
            current_tokens = sum(len(_enc.encode(s)) for s in current_chunk)
        else:
            current_chunk.append(sent)
            current_tokens += sent_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Number the chunks
    return list(enumerate(chunks)) or [(0, text)]
