#!/usr/bin/env python3
"""
ShopDrone Battery Monitoring Node
Conforms to SRS Section 4.6 (Failsafe battery return) and Section 4.9 (Battery monitoring).
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from std_msgs.msg import String, Bool


class BatteryMonitorNode(Node):
    def __init__(self):
        super().__init__('shopdrone_battery_monitor')

        # Parameters
        self.declare_parameter('initial_charge_percent', 100.0)
        self.declare_parameter('drain_rate_per_sec', 0.25) # % per second during active flight
        self.declare_parameter('return_home_threshold', 25.0) # SRS Section 4.6 & Appendix C.4
        self.declare_parameter('emergency_land_threshold', 10.0)

        self.battery_pct = float(self.get_parameter('initial_charge_percent').value)
        self.drain_rate = float(self.get_parameter('drain_rate_per_sec').value)
        self.rth_threshold = float(self.get_parameter('return_home_threshold').value)
        self.emergency_threshold = float(self.get_parameter('emergency_land_threshold').value)

        self.is_in_flight = False
        self.rth_triggered = False

        # Publishers
        self.battery_pub = self.create_publisher(BatteryState, '/shopdrone/battery_state', 10)
        self.alert_pub = self.create_publisher(String, '/shopdrone/alerts', 10)
        self.rth_trigger_pub = self.create_publisher(Bool, '/shopdrone/failsafe_rth', 10)

        # Subscribers
        self.create_subscription(String, '/shopdrone/flight_state', self.on_flight_state, 10)

        # Timer (1 Hz)
        self.timer = self.create_timer(1.0, self.update_battery)
        self.get_logger().info('ShopDrone Battery Monitor initialized. Starting charge: 100%')

    def on_flight_state(self, msg: String):
        state = msg.data.upper()
        # Drain faster during active motors
        self.is_in_flight = state in ['TAKEOFF', 'EN_ROUTE', 'HOVER_SCAN', 'LANDING', 'RETURN_TO_HUB']

    def update_battery(self):
        if self.is_in_flight and self.battery_pct > 0.0:
            self.battery_pct = max(0.0, self.battery_pct - self.drain_rate)

        # Publish standard BatteryState message
        bat_msg = BatteryState()
        bat_msg.header.stamp = self.get_clock().now().to_msg()
        bat_msg.percentage = float(self.battery_pct / 100.0)
        bat_msg.voltage = 22.2 * (self.battery_pct / 100.0) # 6S LiPo simulation
        bat_msg.current = 18.5 if self.is_in_flight else 1.2
        bat_msg.present = True
        self.battery_pub.publish(bat_msg)

        # Failsafe logic
        if self.battery_pct <= self.rth_threshold and not self.rth_triggered:
            self.rth_triggered = True
            alert_msg = String()
            alert_msg.data = f'LOW BATTERY ({self.battery_pct:.1f}%): Triggering autonomous Return-to-Hub failsafe (SRS 4.6)'
            self.get_logger().warn(alert_msg.data)
            self.alert_pub.publish(alert_msg)

            trigger = Bool()
            trigger.data = True
            self.rth_trigger_pub.publish(trigger)


def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
