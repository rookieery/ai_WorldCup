"""Bridge script: consume Feishu CLI events and forward to local webhook.

Usage:
    python scripts/feishu_event_bridge.py

Reads NDJSON events from ``lark-cli event consume im.message.receive_v1``,
converts the flat CLI output format into the standard Feishu webhook callback
format, and POSTs each event to ``http://localhost:8000/api/feishu/webhook``.

Requires the backend server to be running.
"""

import json
import subprocess
import sys
import urllib.request

WEBHOOK_URL = "http://localhost:8000/api/feishu/webhook"


def _cli_to_webhook(cli_event: dict) -> dict:
    """Convert a flat CLI event into the standard Feishu webhook envelope.

    CLI format (flat):
        {"message_id": "om_xxx", "content": "...", "chat_id": "oc_xxx", ...}

    Webhook format (nested):
        {"schema": "2.0", "header": {...}, "event": {"sender": {...}, "message": {...}}}
    """
    return {
        "schema": "2.0",
        "header": {
            "event_id": cli_event.get("event_id", ""),
            "event_type": cli_event.get("type", "im.message.receive_v1"),
            "create_time": cli_event.get("timestamp", ""),
            "token": "",
            "app_id": "",
            "tenant_key": "",
        },
        "event": {
            "sender": {
                "sender_id": {
                    "open_id": cli_event.get("sender_id", ""),
                },
                "sender_type": "user",
                "tenant_key": "",
            },
            "message": {
                "message_id": cli_event.get("message_id", ""),
                "root_id": "",
                "parent_id": "",
                "create_time": cli_event.get("create_time", ""),
                "update_time": "",
                "chat_id": cli_event.get("chat_id", ""),
                "chat_type": cli_event.get("chat_type", ""),
                "message_type": cli_event.get("message_type", ""),
                "content": cli_event.get("content", ""),
            },
        },
    }


def main() -> None:
    print(f"Starting event bridge: lark-cli -> {WEBHOOK_URL}")
    print("Subscribing to im.message.receive_v1 ...")
    print("Press Ctrl+C to stop.\n")

    proc = subprocess.Popen(
        ["lark-cli", "event", "consume", "im.message.receive_v1", "--quiet", "--as", "bot"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=True,
    )

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            # Try to parse as JSON (skip non-JSON informational lines)
            try:
                cli_event = json.loads(line)
            except json.JSONDecodeError:
                print(f"  [skip] {line[:120]}")
                continue

            # Convert CLI format to webhook format
            webhook_event = _cli_to_webhook(cli_event)

            # Forward to local webhook
            try:
                payload = json.dumps(webhook_event, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    WEBHOOK_URL,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    status = resp.status
                msg_text = cli_event.get("content", "")[:50]
                print(f"  -> forwarded (HTTP {status}) content={msg_text!r}")
            except Exception as e:
                print(f"  -> forward failed: {e}")

    except KeyboardInterrupt:
        print("\nStopping event bridge...")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Event bridge stopped.")


if __name__ == "__main__":
    main()
