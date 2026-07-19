"""Safe command-line entry point for the OrientAI voice API."""

from __future__ import annotations

import argparse
import json
import os
import socket
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def _configured_port() -> int:
    raw_port = os.getenv("VOICE_API_PORT", str(DEFAULT_PORT))
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise SystemExit("VOICE_API_PORT must be an integer") from exc

    if not 1 <= port <= 65535:
        raise SystemExit("VOICE_API_PORT must be between 1 and 65535")
    return port


def _connect_host(host: str) -> str:
    if host in {"0.0.0.0", "::"}:
        return "127.0.0.1"
    return host


def _port_is_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((_connect_host(host), port), timeout=0.4):
            return True
    except OSError:
        return False


def _orientai_is_running(host: str, port: int) -> bool:
    health_url = f"http://{_connect_host(host)}:{port}/health"
    try:
        with urlopen(health_url, timeout=0.8) as response:  # noqa: S310
            payload = json.load(response)
            response_status = response.status
    except (OSError, URLError, ValueError, json.JSONDecodeError):
        return False

    return (
        isinstance(payload, dict)
        and response_status == 200
        and payload.get("status") == "ok"
        and payload.get("service") == "voice-input"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the OrientAI voice API")
    parser.add_argument(
        "--host",
        default=os.getenv("VOICE_API_HOST", DEFAULT_HOST),
        help="Address to listen on (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=_configured_port(),
        help="TCP port to listen on (default: %(default)s)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Restart automatically after Python source changes",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("Port must be between 1 and 65535")

    if _port_is_in_use(args.host, args.port):
        if _orientai_is_running(args.host, args.port):
            print(
                f"OrientAI voice API is already running at "
                f"http://{_connect_host(args.host)}:{args.port}"
            )
            return
        raise SystemExit(
            f"Port {args.port} is already being used by another application. "
            "Stop that application or choose another port with --port."
        )

    uvicorn.run(
        "service.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
