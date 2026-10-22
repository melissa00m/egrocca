#!/usr/bin/env python3
"""
ShopDrone Cargo Lock Node
Conforms to SRS Section 4.8 (Safe Delivery Confirmation & OTP Unlock).
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool


class CargoLockNode(Node):
    def __init__(self):
        super().__init__('shopdrone_cargo_lock')

        # Parameters
        self.declare_parameter('expected_otp', '4921')
        self.expected_otp = str(self.get_parameter('expected_otp').value)

        self.is_locked = True
        self.attempts_failed = 0
        self.max_attempts = 3
        self.is_tamper_locked = False

        # Publishers
        self.lock_state_pub = self.create_publisher(Bool, '/shopdrone/cargo_lock_status', 10)
        self.alert_pub = self.create_publisher(String, '/shopdrone/alerts', 10)
        self.delivery_confirmed_pub = self.create_publisher(Bool, '/shopdrone/delivery_confirmed', 10)

        # Subscribers
        self.create_subscription(String, '/shopdrone/keypad_input', self.on_keypad_input, 10)
        self.create_subscription(String, '/shopdrone/new_order_otp', self.on_new_otp, 10)

        # Heartbeat timer for lock status
        self.create_timer(1.0, self.publish_status)
        self.get_logger().info(f'ShopDrone Electronic Cargo Box ready. Expected OTP: {self.expected_otp}')

    def on_new_otp(self, msg: String):
        new_otp = msg.data.strip()
        if len(new_otp) >= 4:
            self.expected_otp = new_otp
            self.attempts_failed = 0
            self.is_tamper_locked = False
            self.is_locked = True
            self.get_logger().info(f'New customer order OTP programmed: {self.expected_otp}')

    def on_keypad_input(self, msg: String):
        entered_code = msg.data.strip()
        self.get_logger().info(f'Keypad entered code: [{entered_code}]')

        if self.is_tamper_locked:
            self.alert_pub.publish(String(data='ALERT: Tamper lockout active! 3 failed OTP attempts recorded.'))
            self.get_logger().error('Tamper lockout active. Cargo box cannot be opened.')
            return

        if entered_code == self.expected_otp:
            self.is_locked = False
            self.attempts_failed = 0
            self.get_logger().info('>>> SUCCESS: Correct OTP entered! Cargo box UNLOCKED. Goods handed to customer.')
            self.publish_status()

            # Confirm delivery
            confirmed = Bool()
            confirmed.data = True
            self.delivery_confirmed_pub.publish(confirmed)

            alert = String()
            alert.data = 'DELIVERY CONFIRMED: Cargo box opened successfully at customer location (SRS 4.8).'
            self.alert_pub.publish(alert)
        else:
            self.attempts_failed += 1
            remaining = self.max_attempts - self.attempts_failed
            self.get_logger().warn(f'Incorrect OTP entered! Attempt {self.attempts_failed}/{self.max_attempts}')

            if self.attempts_failed >= self.max_attempts:
                self.is_tamper_locked = True
                alert = String()
                alert.data = 'SECURITY ALERT: 3 wrong OTP attempts! Cargo box locked down. Shop notified.'
                self.alert_pub.publish(alert)
                self.get_logger().error(alert.data)

    def publish_status(self):
        msg = Bool()
        msg.data = self.is_locked
        self.lock_state_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = CargoLockNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
