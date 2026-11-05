#!/usr/bin/env python3
"""Forward ROS obstacle and sensor status to the Node-RED dashboard."""

import json
import math
import time
from collections import deque
from urllib.error import URLError
from urllib.request import Request, urlopen

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import Bool, Float32


class NodeRedBridgeNode(Node):
    def __init__(self):
        super().__init__('shopdroid_nodered_bridge')
        self.declare_parameter('dashboard_url', 'http://localhost:1880')
        self.declare_parameter('camera_stream_url', '')
        self.declare_parameter('sensor_timeout_seconds', 3.0)

        base_url = str(self.get_parameter('dashboard_url').value).rstrip('/')
        self.alert_url = base_url + '/api/alert'
        self.sensors_url = base_url + '/api/sensors'
        self.camera_stream_url = str(
            self.get_parameter('camera_stream_url').value
        )
        self.sensor_timeout = float(
            self.get_parameter('sensor_timeout_seconds').value
        )
        if self.sensor_timeout <= 0:
            raise ValueError('sensor_timeout_seconds must be positive')

        self.distance_m = None
        self.last_obstacle_state = None
        self.pending_alerts = deque()
        self.last_lidar_seen = None
        self.last_camera_seen = None
        self.connection_warning_active = False

        self.create_subscription(
            Bool, '/shopdrone/obstacle_detected', self.on_obstacle, 10
        )
        self.create_subscription(
            Float32, '/shopdrone/min_obstacle_distance', self.on_distance, 10
        )
        self.create_subscription(LaserScan, '/shopdroid/lidar', self.on_lidar, 10)
        self.create_subscription(
            Image, '/shopdroid/camera/image_raw', self.on_camera, 10
        )
        self.create_timer(0.2, self.flush_alert)
        self.create_timer(1.0, self.publish_sensor_status)
        self.get_logger().info(
            f'Node-RED bridge sending dashboard updates to {base_url}'
        )

    def on_distance(self, msg):
        if math.isfinite(msg.data) and msg.data >= 0:
            self.distance_m = float(msg.data)

    def on_obstacle(self, msg):
        if msg.data == self.last_obstacle_state:
            return
        self.last_obstacle_state = msg.data
        alert = {
            'obstacle_detected': msg.data,
            'message': (
                'Obstacle detected' if msg.data else 'Path clear'
            ),
        }
        if self.distance_m is not None:
            alert['distance_m'] = self.distance_m
        self.pending_alerts.append(alert)

    def on_lidar(self, _msg):
        self.last_lidar_seen = time.monotonic()

    def on_camera(self, _msg):
        self.last_camera_seen = time.monotonic()

    def post_json(self, url, payload):
        request = Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        try:
            with urlopen(request, timeout=1.0) as response:
                response.read()
        except URLError as error:
            if not self.connection_warning_active:
                self.get_logger().warning(
                    f'Cannot reach Node-RED at {url}: {error}'
                )
                self.connection_warning_active = True
            return False

        if self.connection_warning_active:
            self.get_logger().info('Node-RED connection restored')
            self.connection_warning_active = False
        return True

    def flush_alert(self):
        if not self.pending_alerts:
            return
        alert = self.pending_alerts.popleft()
        if not self.post_json(self.alert_url, alert):
            self.pending_alerts.appendleft(alert)

    def publish_sensor_status(self):
        now = time.monotonic()
        status = {
            'camera_online': (
                self.last_camera_seen is not None
                and now - self.last_camera_seen < self.sensor_timeout
            ),
            'lidar_online': (
                self.last_lidar_seen is not None
                and now - self.last_lidar_seen < self.sensor_timeout
            ),
        }
        if self.camera_stream_url:
            status['camera_stream_url'] = self.camera_stream_url
        self.post_json(self.sensors_url, status)


def main(args=None):
    rclpy.init(args=args)
    node = NodeRedBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
