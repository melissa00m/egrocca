#!/usr/bin/env python3
"""
ShopDroid Node-RED ↔ ROS 2 HTTP Bridge
========================================
Accepts HTTP POST requests from Node-RED test flows and publishes
the payloads to the corresponding ROS 2 topics using rclpy.

Run on Ubuntu 24.04 with ROS 2 Jazzy sourced:
    source /opt/ros/jazzy/setup.bash
    source ros2_ws/install/setup.bash
    pip install flask
    python3 nodered/ros2_http_bridge.py

Endpoints accepted (all POST, JSON body):
    POST /ros/lidar           → /shopdroid/lidar        (sensor_msgs/LaserScan)
    POST /ros/odom            → /odom                   (nav_msgs/Odometry)
    POST /ros/gps             → /shopdroid/gps          (sensor_msgs/NavSatFix)
    POST /ros/obstacle_alert  → /shopdroid/obstacle_alert (std_msgs/String JSON)
    POST /ros/battery         → /shopdroid/battery       (std_msgs/String JSON)
    POST /ros/camera          → /shopdroid/camera/image_raw (std_msgs/String JSON)
    GET  /health              → bridge health check
"""

import json
import threading
import logging

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, NavSatFix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Quaternion, Vector3, Twist
from std_msgs.msg import String, Header
from builtin_interfaces.msg import Time

from flask import Flask, request, jsonify

# ── Flask app ──────────────────────────────────────────────────────────────
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)   # Suppress per-request Flask logs

# Global ROS 2 node (set in __main__)
bridge_node: 'ShopDroidBridge | None' = None


# ── ROS 2 bridge node ──────────────────────────────────────────────────────
class ShopDroidBridge(Node):
    """Thin ROS 2 node that exposes publisher handles to Flask handlers."""

    def __init__(self):
        super().__init__('nodered_http_bridge')
        qos = 10  # Keep-last depth

        self.lidar_pub    = self.create_publisher(LaserScan,  '/shopdroid/lidar',              qos)
        self.odom_pub     = self.create_publisher(Odometry,   '/odom',                         qos)
        self.gps_pub      = self.create_publisher(NavSatFix,  '/shopdroid/gps',                qos)
        self.obstacle_pub = self.create_publisher(String,     '/shopdroid/obstacle_alert',     qos)
        self.battery_pub  = self.create_publisher(String,     '/shopdroid/battery',            qos)
        self.camera_pub   = self.create_publisher(String,     '/shopdroid/camera/image_raw',   qos)

        self.get_logger().info('✅ ShopDroid Node-RED HTTP Bridge started — listening on :5000')


# ── Helpers ────────────────────────────────────────────────────────────────
def _make_time(stamp: dict) -> Time:
    t = Time()
    t.sec     = int(stamp.get('sec',     0))
    t.nanosec = int(stamp.get('nanosec', 0))
    return t


def _make_header(hdr: dict) -> Header:
    h = Header()
    h.stamp    = _make_time(hdr.get('stamp', {}))
    h.frame_id = hdr.get('frame_id', '')
    return h


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.route('/ros/lidar', methods=['POST'])
def ros_lidar():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg = LaserScan()
        msg.header          = _make_header(data.get('header', {}))
        msg.angle_min       = float(data.get('angle_min',       -3.14159))
        msg.angle_max       = float(data.get('angle_max',        3.14159))
        msg.angle_increment = float(data.get('angle_increment',  0.01745))
        msg.time_increment  = float(data.get('time_increment',   0.0))
        msg.scan_time       = float(data.get('scan_time',        0.05))
        msg.range_min       = float(data.get('range_min',        0.1))
        msg.range_max       = float(data.get('range_max',        25.0))
        msg.ranges          = [float(r) for r in data.get('ranges', [])]
        msg.intensities     = [float(i) for i in data.get('intensities', [])]
        bridge_node.lidar_pub.publish(msg)
        bridge_node.get_logger().debug(f'LiDAR: {len(msg.ranges)} rays published')
    return jsonify({'status': 'ok', 'topic': '/shopdroid/lidar'})


@app.route('/ros/odom', methods=['POST'])
def ros_odom():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg = Odometry()
        msg.header         = _make_header(data.get('header', {}))
        msg.child_frame_id = data.get('child_frame_id', 'base_link')

        pose_data = data.get('pose', {}).get('pose', {})
        pos  = pose_data.get('position',    {})
        ori  = pose_data.get('orientation', {})
        msg.pose.pose.position    = Point(x=float(pos.get('x', 0)),
                                          y=float(pos.get('y', 0)),
                                          z=float(pos.get('z', 0)))
        msg.pose.pose.orientation = Quaternion(x=float(ori.get('x', 0)),
                                               y=float(ori.get('y', 0)),
                                               z=float(ori.get('z', 0)),
                                               w=float(ori.get('w', 1)))

        twist_data = data.get('twist', {}).get('twist', {})
        lin = twist_data.get('linear',  {})
        ang = twist_data.get('angular', {})
        msg.twist.twist.linear  = Vector3(x=float(lin.get('x', 0)),
                                          y=float(lin.get('y', 0)),
                                          z=float(lin.get('z', 0)))
        msg.twist.twist.angular = Vector3(x=float(ang.get('x', 0)),
                                          y=float(ang.get('y', 0)),
                                          z=float(ang.get('z', 0)))

        bridge_node.odom_pub.publish(msg)
    return jsonify({'status': 'ok', 'topic': '/odom'})


@app.route('/ros/gps', methods=['POST'])
def ros_gps():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg = NavSatFix()
        msg.header    = _make_header(data.get('header', {}))
        msg.latitude  = float(data.get('latitude',  0.0))
        msg.longitude = float(data.get('longitude', 0.0))
        msg.altitude  = float(data.get('altitude',  0.0))
        cov = data.get('position_covariance', [0.0] * 9)
        msg.position_covariance      = [float(c) for c in cov]
        msg.position_covariance_type = int(data.get('position_covariance_type', 0))
        bridge_node.gps_pub.publish(msg)
        bridge_node.get_logger().info(
            f'GPS: ({msg.latitude:.6f}, {msg.longitude:.6f}) '
            f'step={data.get("route_step", "?")}')
    return jsonify({'status': 'ok', 'topic': '/shopdroid/gps'})


@app.route('/ros/obstacle_alert', methods=['POST'])
def ros_obstacle():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg      = String()
        msg.data = json.dumps(data)
        bridge_node.obstacle_pub.publish(msg)
        if data.get('obstacle_detected'):
            bridge_node.get_logger().warn(
                f"OBSTACLE [{data.get('test_scenario','?')}]: "
                f"{data.get('obstacle_type','?')} @ {data.get('distance_m','?')}m "
                f"→ {data.get('action_required','?')}"
            )
    return jsonify({'status': 'ok', 'topic': '/shopdroid/obstacle_alert'})


@app.route('/ros/battery', methods=['POST'])
def ros_battery():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg      = String()
        msg.data = json.dumps(data)
        bridge_node.battery_pub.publish(msg)
        pct    = data.get('percentage', '?')
        status = data.get('status', '?')
        bridge_node.get_logger().info(f'Battery: {pct}% [{status}]')
    return jsonify({'status': 'ok', 'topic': '/shopdroid/battery'})


@app.route('/ros/camera', methods=['POST'])
def ros_camera():
    data = request.get_json(force=True, silent=True)
    if bridge_node and data:
        msg      = String()
        msg.data = json.dumps({
            'frame':    data.get('frame_seq'),
            'scene':    data.get('scene_classification'),
            'checksum': data.get('checksum')
        })
        bridge_node.camera_pub.publish(msg)
    return jsonify({'status': 'ok', 'topic': '/shopdroid/camera/image_raw'})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status':  'healthy',
        'bridge':  'ShopDroid Node-RED HTTP Bridge',
        'version': '1.0.0',
        'topics': [
            '/shopdroid/lidar',
            '/odom',
            '/shopdroid/gps',
            '/shopdroid/obstacle_alert',
            '/shopdroid/battery',
            '/shopdroid/camera/image_raw'
        ]
    })


# ── Entry point ────────────────────────────────────────────────────────────
def ros_spin():
    rclpy.spin(bridge_node)


if __name__ == '__main__':
    rclpy.init()
    bridge_node = ShopDroidBridge()

    # Run ROS 2 spin in a background daemon thread
    ros_thread = threading.Thread(target=ros_spin, daemon=True)
    ros_thread.start()

    # Start Flask on all interfaces, port 5000
    print('\n🌐 ShopDroid HTTP Bridge listening on http://0.0.0.0:5000')
    print('   Import nodered/shopdroid_test_flows.json into Node-RED to start testing.\n')
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

    rclpy.shutdown()
