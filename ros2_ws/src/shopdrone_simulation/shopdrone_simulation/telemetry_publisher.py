#!/usr/bin/env python3
"""
ShopDrone Telemetry Publisher Node
Conforms to SRS Section 4.7 (Tracking & Statuses) and Section 4.9 (Admin & Shop Telemetry).
"""

import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, NavSatFix
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist


class TelemetryPublisherNode(Node):
    def __init__(self):
        super().__init__('shopdrone_telemetry_publisher')

        # Base GPS: Rural Matobo Hub, Zimbabwe
        self.hub_lat = -20.553200
        self.hub_lon = 28.514000

        self.current_lat = self.hub_lat
        self.current_lon = self.hub_lon
        self.current_altitude = 0.0 # meters AGL
        self.battery_level = 100.0
        self.flight_state = 'IDLE'
        self.cargo_locked = True
        self.speed_mps = 0.0

        # Publishers
        self.telemetry_pub = self.create_publisher(String, '/shopdrone/telemetry', 10)
        self.gps_pub = self.create_publisher(NavSatFix, '/shopdrone/gps/fix', 10)

        # Subscribers
        self.create_subscription(String, '/shopdrone/flight_state', self.on_state, 10)
        self.create_subscription(BatteryState, '/shopdrone/battery_state', self.on_battery, 10)
        self.create_subscription(Bool, '/shopdrone/cargo_lock_status', self.on_cargo_lock, 10)
        self.create_subscription(Twist, '/cmd_vel', self.on_cmd_vel, 10)

        # Broadcast telemetry at 2 Hz
        self.create_timer(0.5, self.publish_telemetry)
        self.get_logger().info('ShopDrone Telemetry stream active for Shop & Customer apps.')

    def on_state(self, msg: String):
        self.flight_state = msg.data

    def on_battery(self, msg: BatteryState):
        self.battery_level = msg.percentage * 100.0

    def on_cargo_lock(self, msg: Bool):
        self.cargo_locked = msg.data

    def on_cmd_vel(self, msg: Twist):
        # Calculate velocity magnitude
        self.speed_mps = (msg.linear.x**2 + msg.linear.y**2 + msg.linear.z**2)**0.5

    def publish_telemetry(self):
        # Update simulated coordinates based on state
        if self.flight_state in ['TAKEOFF', 'HOVER_SCAN']:
            self.current_altitude = min(20.0, self.current_altitude + 1.0)
        elif self.flight_state == 'EN_ROUTE':
            self.current_altitude = 20.0
            self.current_lat += 0.00005
            self.current_lon += 0.00005
        elif self.flight_state == 'LANDING':
            self.current_altitude = max(0.0, self.current_altitude - 1.0)
        elif self.flight_state in ['DELIVERED', 'IDLE']:
            self.current_altitude = 0.0
        elif self.flight_state == 'RETURN_TO_HUB':
            self.current_altitude = 20.0
            self.current_lat = max(self.hub_lat, self.current_lat - 0.00005)
            self.current_lon = max(self.hub_lon, self.current_lon - 0.00005)

        # Publish standard NavSatFix
        nav_msg = NavSatFix()
        nav_msg.header.stamp = self.get_clock().now().to_msg()
        nav_msg.latitude = float(self.current_lat)
        nav_msg.longitude = float(self.current_lon)
        nav_msg.altitude = float(self.current_altitude)
        self.gps_pub.publish(nav_msg)

        # JSON payload for Customer & Shop web/SMS dashboard
        payload = {
            "drone_id": "SHOPDRONE-ZW-01",
            "status": self.flight_state,
            "gps": {
                "latitude": round(self.current_lat, 6),
                "longitude": round(self.current_lon, 6),
                "altitude_m": round(self.current_altitude, 1)
            },
            "speed_kmh": round(self.speed_mps * 3.6, 1),
            "battery_percent": round(self.battery_level, 1),
            "cargo_box_locked": self.cargo_locked,
            "region": "Matobo Ward 4, Zimbabwe"
        }

        msg = String()
        msg.data = json.dumps(payload)
        self.telemetry_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TelemetryPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
