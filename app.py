#!/usr/bin/env python3

import base64
import json
import os
import time
import hmac
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.environ["LISTEN_PORT"])

NEXTCLOUD_URL = os.environ["NEXTCLOUD_URL"].rstrip("/")
NEXTCLOUD_USER = os.environ["NEXTCLOUD_USER"]
NEXTCLOUD_APP_PASSWORD = os.environ["NEXTCLOUD_APP_PASSWORD"]
NEXTCLOUD_TLS_VERIFY = os.environ["NEXTCLOUD_TLS_VERIFY"].lower() in ("1", "true", "yes")
TALK_TOKEN = os.environ["TALK_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]


# TLS certificate verification for the Nextcloud connection
if NEXTCLOUD_TLS_VERIFY:
    SSL_CONTEXT = ssl.create_default_context()
else:
    # Disable TLS verification for Nextcloud certificate
    SSL_CONTEXT = ssl._create_unverified_context()


def send_to_talk(message):
    url = (
        f"{NEXTCLOUD_URL}"
        f"/ocs/v2.php/apps/spreed/api/v1/chat/{TALK_TOKEN}"
    )

    payload = json.dumps({
        "message": message
    }).encode("utf-8")

    credentials = (
        f"{NEXTCLOUD_USER}:{NEXTCLOUD_APP_PASSWORD}"
    ).encode("utf-8")

    auth = base64.b64encode(credentials).decode("ascii")

    request = Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "OCS-APIRequest": "true",
        },
    )

    with urlopen(
        request,
        timeout=15,
        context=SSL_CONTEXT
    ) as response:

        body = response.read().decode(
            "utf-8",
            errors="replace"
        )

        print(
            f"Nextcloud: HTTP {response.status}: {body}",
            flush=True
        )

        if response.status not in (200, 201):
            raise RuntimeError(
                f"Nextcloud returned HTTP {response.status}"
            )


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(
            f"{self.client_address[0]} - "
            f"{fmt % args}",
            flush=True
        )

    def send_json(self, status, data):

        payload = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        self.end_headers()

        self.wfile.write(payload)

    def do_GET(self):

        if self.path == "/health":

            self.send_json(
                200,
                {
                    "status": "ok"
                }
            )

            return

        self.send_json(
            404,
            {
                "error": "not found"
            }
        )

    def do_POST(self):

        parsed = urlparse(self.path)

        if parsed.path != "/synology":

            self.send_json(
                404,
                {
                    "error": "not found"
                }
            )

            return

        # --------------------------------------------------
        # Webhook secret
        # --------------------------------------------------

        supplied_secret = self.headers.get(
            "X-Synology-Webhook-Secret",
            ""
        )

        if not hmac.compare_digest(
            supplied_secret,
            WEBHOOK_SECRET
        ):

            print(
                "Rejected webhook: invalid secret",
                flush=True
            )

            self.send_json(
                401,
                {
                    "error": "unauthorized"
                }
            )

            return

        # --------------------------------------------------
        # Synology notification
        #
        # DSM sends:
        # POST /synology?text=...
        # --------------------------------------------------

        query = parse_qs(
            parsed.query,
            keep_blank_values=True
        )

        text_values = query.get("text", [])

        if not text_values:

            print(
                "Synology webhook without text parameter",
                flush=True
            )

            self.send_json(
                400,
                {
                    "error": "missing text parameter"
                }
            )

            return

        message = text_values[0].strip()

        if not message:

            self.send_json(
                400,
                {
                    "error": "empty message"
                }
            )

            return

        print(
            "Received Synology notification:",
            message,
            flush=True
        )

        # --------------------------------------------------
        # Send to Nextcloud Talk
        # --------------------------------------------------

        try:

            send_to_talk(
                message
            )

            self.send_json(
                200,
                {
                    "status": "sent"
                }
            )

        except Exception as e:

            print(
                f"Failed to send Talk message: {e}",
                flush=True
            )

            self.send_json(
                502,
                {
                    "error":
                    "failed to send to Nextcloud Talk"
                }
            )


if __name__ == "__main__":

    print(
        "Synology → Nextcloud Talk bridge "
        f"listening on {LISTEN_HOST}:{LISTEN_PORT}",
        flush=True
    )

    server = ThreadingHTTPServer(
        (LISTEN_HOST, LISTEN_PORT),
        Handler
    )

    server.serve_forever()
