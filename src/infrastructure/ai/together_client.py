import json
import urllib.request


class TogetherAIClient:
    """Lightweight Together AI client prepared for future metadata enrichment."""

    API_URL = "https://api.together.xyz/v1/chat/completions"

    def __init__(
        self, api_key: str, model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    ) -> None:
        if not api_key:
            raise ValueError("TOGETHER_API_KEY is required to initialize TogetherAIClient.")
        self._api_key = api_key
        self._model = model

    def extract_track_metadata(
        self,
        file_name: str,
        caption: str | None = None,
    ) -> dict[str, str]:
        """Use Together AI chat completions to normalize artist/album/title from raw text."""
        prompt = (
            "Extract JSON with keys 'artist', 'album', 'title', 'genre' from this audio info. "
            f"Filename: {file_name}. Caption: {caption or 'N/A'}. Respond with valid JSON only."
        )
        payload = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            self.API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
