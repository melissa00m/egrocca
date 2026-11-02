#!/usr/bin/env python3
"""Send obstacle and sensor updates to the ShopDroid Node-RED dashboard."""

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_json(url, payload, timeout=5):
    """POST a JSON object and return the decoded JSON response."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")

    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Node-RED returned HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Could not reach Node-RED at {url}: {error.reason}"
        ) from error

    if not isinstance(result, dict):
        raise RuntimeError("Node-RED returned a non-object JSON response")
    return result


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default="http://localhost:1880",
        help="Node-RED base URL (default: http://localhost:1880)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    alert = commands.add_parser(
        "alert", help="send an obstacle alert or clear event"
    )
    alert.add_argument("--state", choices=("detected", "clear"), required=True)
    alert.add_argument("--distance-m", type=float)
    alert.add_argument("--message")

    sensors = commands.add_parser(
        "sensors", help="update camera and LiDAR status"
    )
    sensors.add_argument("--camera", choices=("online", "offline"))
    sensors.add_argument("--lidar", choices=("online", "offline"))
    sensors.add_argument("--camera-stream-url")
    return parser


def main():
    args = _build_parser().parse_args()
    if args.command == "alert":
        payload = {"obstacle_detected": args.state == "detected"}
        if args.distance_m is not None:
            payload["distance_m"] = args.distance_m
        if args.message is not None:
            payload["message"] = args.message
        endpoint = "/api/alert"
    else:
        payload = {}
        if args.camera is not None:
            payload["camera_online"] = args.camera == "online"
        if args.lidar is not None:
            payload["lidar_online"] = args.lidar == "online"
        if args.camera_stream_url is not None:
            payload["camera_stream_url"] = args.camera_stream_url
        if not payload:
            raise SystemExit("Provide --camera, --lidar, or --camera-stream-url")
        endpoint = "/api/sensors"

    response = post_json(args.base_url.rstrip("/") + endpoint, payload)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
