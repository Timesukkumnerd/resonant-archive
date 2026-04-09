"""resonant-archive embedder — sentence-transformers wrapper.

Thin class wrapping a sentence-transformers model with lazy loading and
batch encoding. Kept deliberately minimal — the store talks to it via the
``embed(texts)`` method and the ``model_name`` property.

Copyright (C) 2025-2026 Codependent AI
Licensed under the Codependent AI Source-Available License. See LICENSE.
"""

from __future__ import annotations

from typing import Sequence

from sentence_transformers import SentenceTransformer

#: Default embedding model. 384-dimensional, ~90 MB, fast. Alternatives are
#: documented in the README.
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class Embedder:
    """Lazy-loading wrapper around a sentence-transformers model.

    The underlying model is only loaded on the first call to ``embed()``
    or ``model``, so constructing an ``Embedder`` is cheap.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Encode texts into L2-normalized embedding vectors.

        Returns a list of float lists, one per input. An empty input list
        returns an empty result without loading the model.
        """
        if not texts:
            return []
        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vectors.tolist()
