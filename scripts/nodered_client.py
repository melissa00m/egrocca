#!/usr/bin/env python3
"""Send obstacle alerts and sensor status to the Egrocca Node-RED flow."""

import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


def post_json(endpoint: str, payload: dict) -> dict:
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        result = json.loads(response.read().decode("utf-8"))
        if response.status >= 400:
            raise RuntimeError(f"Node-RED rejected the request: {result}")
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default="http://localhost:1880",
        help="Node-RED base URL (default: http://localhost:1880)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    alert = commands.add_parser("alert", help="send an obstacle alert")
    alert.add_argument("--state", choices=("detected", "clear"), required=True)
    alert.add_argument("--distance-m", type=float)
    alert.add_argument("--message")

    sensors = commands.add_parser("sensors", help="update sensor status")
    sensors.add_argument("--camera", choices=("online", "offline"))
    sensors.add_argument("--lidar", choices=("online", "offline"))
    sensors.add_argument("--camera-stream-url")

    args = parser.parse_args()
    if args.command == "alert":
        payload = {"obstacle_detected": args.state == "detected"}
        if args.distance_m is not None:
            payload["distance_m"] = args.distance_m
        if args.message:
            payload["message"] = args.message
        endpoint = args.url.rstrip("/") + "/api/alert"
    else:
        payload = {}
        if args.camera is not None:
            payload["camera_online"] = args.camera == "online"
        if args.lidar is not None:
            payload["lidar_online"] = args.lidar == "online"
        if args.camera_stream_url is not None:
            payload["camera_stream_url"] = args.camera_stream_url
        if not payload:
            parser.error("sensors requires --camera, --lidar, or --camera-stream-url")
        endpoint = args.url.rstrip("/") + "/api/sensors"

    try:
        response = post_json(endpoint, payload)
    except (URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Node-RED request failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
