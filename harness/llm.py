"""Local model client.

The harness talks to Ollama's local HTTP API (http://127.0.0.1:11434 by default).
Nothing here calls a hosted service: if Ollama is not running, calls fail with a
clear error instead of falling back to the cloud.

A 'fake' backend (WIKI_BACKEND=fake) exists only for the unit tests in tests/,
so the plumbing can be checked on a machine without a model. It is never used
for submitted evidence; every evidence record stores which backend produced it.
"""
import json
import re
import time
import urllib.error
import urllib.request


class ModelUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, cfg):
        self.url = cfg["ollama_url"].rstrip("/")
        self.model = cfg["model"]
        self.num_ctx = cfg["num_ctx"]
        self.timeout = cfg["request_timeout_s"]
        self.backend = "ollama"

    def _post(self, path, payload):
        req = urllib.request.Request(
            self.url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 404 and "not found" in body.lower():
                raise ModelUnavailable(
                    f"Model '{self.model}' is not downloaded. While online run: ollama pull {self.model}"
                ) from None
            raise ModelUnavailable(f"Ollama returned HTTP {e.code}: {body[:300]}") from None
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            raise ModelUnavailable(
                f"Cannot reach the local Ollama server at {self.url} ({e}). "
                "Start it with 'ollama serve' (or open the Ollama app) and retry."
            ) from None

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.url + path, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - reported to the user as unavailable
            raise ModelUnavailable(f"Cannot reach the local Ollama server at {self.url} ({e}).") from None

    def chat(self, messages, temperature=0.0):
        """Send a list of {role, content} messages; return (text, stats)."""
        t0 = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            # Gemma 4 can emit a thinking block; keep answers direct for this CLI.
            "think": False,
            "options": {"temperature": temperature, "num_ctx": self.num_ctx, "seed": 42},
        }
        try:
            data = self._post("/api/chat", payload)
        except ModelUnavailable as e:
            if "think" not in str(e).lower():
                raise
            payload.pop("think")  # runtime/model without a thinking switch
            data = self._post("/api/chat", payload)
        wall = time.perf_counter() - t0
        text = (data.get("message") or {}).get("content", "").strip()
        stats = {
            "backend": "ollama",
            "model": data.get("model", self.model),
            "wall_seconds": round(wall, 2),
            "prompt_tokens": data.get("prompt_eval_count"),
            "output_tokens": data.get("eval_count"),
            "load_seconds": _ns(data.get("load_duration")),
            "total_seconds": _ns(data.get("total_duration")),
        }
        if stats["output_tokens"] and data.get("eval_duration"):
            stats["tokens_per_second"] = round(stats["output_tokens"] / (data["eval_duration"] / 1e9), 1)
        return text, stats

    def info(self):
        """Model identity and memory as reported by the local runtime."""
        out = {"backend": "ollama", "url": self.url, "model": self.model}
        out["ollama_version"] = self._get("/api/version").get("version")
        tags = self._get("/api/tags").get("models", [])
        match = [m for m in tags if m.get("name") == self.model or m.get("model") == self.model]
        if match:
            m = match[0]
            out["digest"] = m.get("digest")
            out["file_size_gb"] = round(m.get("size", 0) / 1e9, 2)
            out["details"] = m.get("details")
        out["installed_models"] = [m.get("name") for m in tags]
        loaded = self._get("/api/ps").get("models", [])
        for m in loaded:
            if m.get("name") == self.model or m.get("model") == self.model:
                out["loaded_memory_gb"] = round(m.get("size", 0) / 1e9, 2)
                out["loaded_vram_gb"] = round(m.get("size_vram", 0) / 1e9, 2)
                out["context_length"] = m.get("context_length")
        return out


def _ns(v):
    return round(v / 1e9, 2) if v else None


class FakeClient:
    """Deterministic stand-in used only by tests/. Never used for evidence."""

    def __init__(self, cfg):
        self.model = "fake-test-backend"
        self.backend = "fake"

    def chat(self, messages, temperature=0.0):
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        user = messages[-1]["content"]
        if "INSUFFICIENT EVIDENCE" in system:  # ask mode
            m = re.search(r"\[(S\d+)\][^\n]*\n(.+)", user)
            if not m or "zzz-unknowable" in user:
                text = "INSUFFICIENT EVIDENCE: the passages do not answer this question."
            else:
                text = f"{m.group(2).strip()[:160]} [{m.group(1)}]"
        elif "## Summary" in system:  # ingest
            text = "## Summary\nA test summary.\n\n## Key details\n- A detail from the source."
        else:
            text = f"(fake chat reply to: {user[-80:]})"
        return text, {"backend": "fake", "model": self.model, "wall_seconds": 0.0}

    def info(self):
        return {"backend": "fake", "model": self.model}


def make_client(cfg):
    return FakeClient(cfg) if cfg.get("backend") == "fake" else OllamaClient(cfg)
