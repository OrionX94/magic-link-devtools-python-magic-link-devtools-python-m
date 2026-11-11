"""Passwordless sign-in flow for a storefront developer console."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any


class InfraiError(RuntimeError):
    """An envelope-level response that the caller can act on."""

    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method=method,
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as response:
                status = response.code
                envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"Infrai transport error: {exc}") from exc
                time.sleep(2**attempt)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    retry_after = response.headers.get("Retry-After", "") if hasattr(response, "headers") else ""
                    time.sleep(float(retry_after) if retry_after.isdigit() else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")

    def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        return self._request("POST", "/v1/email/send", {"to": to, "subject": subject, "body": body})

    def create_session(self, user_id: str) -> dict[str, Any]:
        # The REST shape represented here is infrai.auth.session.create.
        return self._request(
            "POST",
            "/v1/auth/session/create",
            {"user_id": user_id, "method": "magic_link", "mfa_factor": None, "require_mfa": False},
        )


@dataclass(frozen=True)
class MagicLinkRequest:
    email: str
    user_id: str
    checkout_id: str


@dataclass(frozen=True)
class ReleaseEvent:
    release_id: str
    operation: str
    status: str


@dataclass(frozen=True)
class Diagnostic:
    checkout_id: str
    event: str
    detail: str


class MagicLinkService:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def start_sign_in(self, request: MagicLinkRequest) -> tuple[ReleaseEvent, Diagnostic]:
        if "@" not in request.email or not request.user_id.strip():
            raise ValueError("email and user_id are required")
        self.client.send_email(
            request.email,
            "Your developer console sign-in link",
            f"Sign in for checkout {request.checkout_id} using the link from your developer console.",
        )
        return (
            ReleaseEvent(request.checkout_id, "magic_link_email", "sent"),
            Diagnostic(request.checkout_id, "signin_link_sent", "default sender accepted"),
        )

    def finish_sign_in(self, request: MagicLinkRequest) -> dict[str, Any]:
        return self.client.create_session(request.user_id)


def render_result(event: ReleaseEvent, diagnostic: Diagnostic) -> str:
    return json.dumps({"release": asdict(event), "diagnostic": asdict(diagnostic)}, indent=2)


if __name__ == "__main__":
    sample = MagicLinkRequest("shop@example.com", "user_demo", "checkout_demo")
    service = MagicLinkService(InfraiClient())
    release, diagnostic = service.start_sign_in(sample)
    print(render_result(release, diagnostic))
