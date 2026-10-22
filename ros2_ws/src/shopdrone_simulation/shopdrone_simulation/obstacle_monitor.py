#!/usr/bin/env python3
"""
ShopDrone Obstacle Monitoring Node
Conforms to SRS Section 4.6 (Obstacle avoidance) and Section 5.1 (3-second reaction time).
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32, String


class ObstacleMonitorNode(Node):
    def __init__(self):
        super().__init__('shopdrone_obstacle_monitor')

        # Parameters
        self.declare_parameter('safe_distance_threshold', 3.0) # meters
        self.safe_distance = float(self.get_parameter('safe_distance_threshold').value)

        # Publishers
        self.obstacle_detected_pub = self.create_publisher(Bool, '/shopdrone/obstacle_detected', 10)
        self.min_distance_pub = self.create_publisher(Float32, '/shopdrone/min_obstacle_distance', 10)
        self.alert_pub = self.create_publisher(String, '/shopdrone/alerts', 10)

        # Subscribers
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.create_subscription(LaserScan, '/shopdrone/lidar', self.on_scan, 10)

        self.last_state_was_blocked = False
        self.get_logger().info(f'ShopDrone Obstacle Monitor active. Safe margin: {self.safe_distance} m')

    def on_scan(self, msg: LaserScan):
        # Filter valid ranges
        valid_ranges = [r for r in msg.ranges if msg.range_min < r < msg.range_max]
        if not valid_ranges:
            return

        min_dist = min(valid_ranges)
        self.min_distance_pub.publish(Float32(data=float(min_dist)))

        is_blocked = min_dist < self.safe_distance

        if is_blocked:
            self.obstacle_detected_pub.publish(Bool(data=True))
            if not self.last_state_was_blocked:
                self.last_state_was_blocked = True
                alert_text = f'OBSTACLE DETECTED at {min_dist:.2f}m! Initiating safe hover/avoidance (SRS 4.6).'
                self.get_logger().warn(alert_text)
                self.alert_pub.publish(String(data=alert_text))
        else:
            self.obstacle_detected_pub.publish(Bool(data=False))
            if self.last_state_was_blocked:
                self.last_state_was_blocked = False
                self.get_logger().info('Flight corridor clear. Resuming normal navigation path.')


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
