from typing import Protocol


class AIEnrichmentPort(Protocol):
    """Optional port for future AI-based metadata enrichment (e.g., Together AI or Ollama)."""

    def extract_track_metadata(
        self,
        file_name: str,
        caption: str | None = None,
    ) -> dict[str, str]:
        """Infer structured metadata (artist, album, title, genre) from raw text."""
        ...
