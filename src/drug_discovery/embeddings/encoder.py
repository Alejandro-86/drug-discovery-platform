"""Abstract encoder interface and sentence-transformers implementation.

Uses the all-MiniLM-L6-v2 model locally — no API calls, no cost per query.
Model is downloaded once and cached in models_cache/ (gitignored).

Output dimension: 384 floats (cosine similarity in Qdrant).
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

VECTOR_DIM = 384
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class AbstractEncoder(ABC):
    """Interface for text-to-vector encoders."""

    @abstractmethod
    def encode(self, text: str) -> list[float]:
        """Encode a single text string into a float vector.

        Args:
            text: Input text (e.g. paper abstract).

        Returns:
            Float vector of length VECTOR_DIM.
        """

    @abstractmethod
    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts.

        Args:
            texts: List of input strings.

        Returns:
            List of float vectors, one per input text.
        """


class SentenceTransformerEncoder(AbstractEncoder):
    """Encoder backed by sentence-transformers all-MiniLM-L6-v2.

    Model is loaded once on first use and cached in the models_cache directory.
    Suitable for local/offline use — no API key required.

    Args:
        model_name: HuggingFace model identifier.
        cache_dir: Directory to cache downloaded model weights.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        cache_dir: str = "models_cache",
    ) -> None:
        self._model_name = model_name
        self._cache_dir = cache_dir
        self._model: SentenceTransformer | None = None

    def _load(self) -> "SentenceTransformer":
        """Lazy-load the model on first encode call."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            os.makedirs(self._cache_dir, exist_ok=True)
            logger.info("loading embedding model '%s'", self._model_name)
            self._model = SentenceTransformer(
                self._model_name,
                cache_folder=self._cache_dir,
            )
        return self._model

    def encode(self, text: str) -> list[float]:
        """Encode a single text string.

        Args:
            text: Input text.

        Returns:
            384-dimensional float vector.
        """
        model = self._load()
        vector = model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of texts.

        Batching is more efficient than encoding one-by-one for large inputs.

        Args:
            texts: List of input strings.

        Returns:
            List of 384-dimensional float vectors.
        """
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(texts, convert_to_numpy=True, batch_size=32)
        return [v.tolist() for v in vectors]
