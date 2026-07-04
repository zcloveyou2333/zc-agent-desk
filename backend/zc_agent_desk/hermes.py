from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx


class HermesUnavailable(RuntimeError):
    """A sanitized sidecar connectivity or protocol error."""


class HermesClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        http: httpx.AsyncClient | None = None,
        timeout: float = 180.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._http = http
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _client(self) -> httpx.AsyncClient:
        if self._http is not None:
            return self._http
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        owned = self._http is None
        client = self._client()
        try:
            response = await client.request(method, path, headers=self._headers(), **kwargs)
        except httpx.HTTPError as exc:
            raise HermesUnavailable("Hermes is unavailable") from exc
        finally:
            if owned:
                await client.aclose()
        if not response.is_success:
            raise HermesUnavailable(f"Hermes returned HTTP {response.status_code}")
        return response

    async def start_run(
        self,
        message: str,
        *,
        session_id: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        body: dict[str, Any] = {"input": message, "session_id": session_id}
        if conversation_history:
            body["conversation_history"] = conversation_history
        response = await self._request("POST", "/v1/runs", json=body)
        run_id = response.json().get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise HermesUnavailable("Hermes returned an invalid run identifier")
        return run_id

    async def events(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        owned = self._http is None
        client = self._client()
        try:
            try:
                context = client.stream(
                    "GET",
                    f"/v1/runs/{run_id}/events",
                    headers=self._headers(),
                    timeout=self.timeout,
                )
                async with context as response:
                    if not response.is_success:
                        raise HermesUnavailable(f"Hermes returned HTTP {response.status_code}")
                    data_lines: list[str] = []
                    async for line in response.aiter_lines():
                        if not line:
                            if data_lines:
                                try:
                                    event = json.loads("\n".join(data_lines))
                                except json.JSONDecodeError as exc:
                                    raise HermesUnavailable("Hermes returned malformed SSE data") from exc
                                if isinstance(event, dict):
                                    yield event
                                data_lines.clear()
                            continue
                        if line.startswith("data:"):
                            data_lines.append(line[5:].lstrip())
            except httpx.HTTPError as exc:
                raise HermesUnavailable("Hermes event stream disconnected") from exc
        finally:
            if owned:
                await client.aclose()

    async def approve(self, run_id: str, decision: str) -> None:
        choice = "once" if decision == "approve" else "deny"
        await self._request("POST", f"/v1/runs/{run_id}/approval", json={"choice": choice})

    async def cancel(self, run_id: str) -> None:
        await self._request("POST", f"/v1/runs/{run_id}/stop", json={})
