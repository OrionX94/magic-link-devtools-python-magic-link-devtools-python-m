from magic_link_service import MagicLinkRequest, MagicLinkService, render_result


class RecordingClient:
    def __init__(self) -> None:
        self.sent = []

    def send_email(self, to: str, subject: str, body: str) -> dict:
        self.sent.append((to, subject, body))
        return {"ok": True, "data": {"message_id": "msg_demo"}}


def test_checkout_sign_in_records_a_sent_link_and_diagnostic() -> None:
    client = RecordingClient()
    service = MagicLinkService(client)
    event, diagnostic = service.start_sign_in(
        MagicLinkRequest("buyer@example.com", "user_123", "checkout_456")
    )

    assert client.sent[0][0] == "buyer@example.com"
    assert event.status == "sent"
    assert diagnostic.event == "signin_link_sent"
    assert "checkout_456" in render_result(event, diagnostic)
