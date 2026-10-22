#!/usr/bin/env python3
"""
ShopDrone End-to-End Mission Demo Runner
Displays a live terminal dashboard showing the full automated delivery cycle.
"""

import sys
import time
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from sensor_msgs.msg import BatteryState


class MissionRunnerNode(Node):
    def __init__(self):
        super().__init__('shopdrone_mission_runner')

        self.current_state = 'INITIALIZING'
        self.battery_pct = 100.0
        self.cargo_locked = True
        self.drone_lat = -20.553200
        self.drone_lon = 28.514000
        self.altitude = 0.0
        self.latest_alert = 'All systems nominal.'

        # Publishers
        self.dispatch_pub = self.create_publisher(String, '/shopdrone/dispatch_order', 10)
        self.keypad_pub = self.create_publisher(String, '/shopdrone/keypad_input', 10)

        # Subscribers
        self.create_subscription(String, '/shopdrone/flight_state', self.on_state, 10)
        self.create_subscription(String, '/shopdrone/telemetry', self.on_telemetry, 10)
        self.create_subscription(String, '/shopdrone/alerts', self.on_alert, 10)
        self.create_subscription(Bool, '/shopdrone/cargo_lock_status', self.on_lock, 10)

        self.otp_sent = False
        self.order_dispatched = False

        # Periodic UI update and mission sequencer (2 Hz)
        self.timer = self.create_timer(0.5, self.update_dashboard)
        self.seq_timer = self.create_timer(1.0, self.mission_sequence_step)

    def on_state(self, msg: String):
        self.current_state = msg.data

    def on_telemetry(self, msg: String):
        try:
            data = json.loads(msg.data)
            self.battery_pct = data.get('battery_percent', 100.0)
            self.drone_lat = data.get('gps', {}).get('latitude', -20.5532)
            self.drone_lon = data.get('gps', {}).get('longitude', 28.5140)
            self.altitude = data.get('gps', {}).get('altitude_m', 0.0)
        except Exception:
            pass

    def on_alert(self, msg: String):
        self.latest_alert = msg.data

    def on_lock(self, msg: Bool):
        self.cargo_locked = msg.data

    def mission_sequence_step(self):
        if not self.order_dispatched:
            self.order_dispatched = True
            time.sleep(1.0)
            order_msg = String()
            order_msg.data = "ORDER #1042: 2 SUGAR, 1 SOAP to Matobo Ward 4 (Customer: Hopewell Ndlovu)"
            self.dispatch_pub.publish(order_msg)

        # When drone lands at customer address, simulate customer typing OTP
        if self.current_state == 'AWAITING_OTP' and not self.otp_sent:
            self.otp_sent = True
            self.get_logger().info('Simulating customer OTP input: "4921" via drone keypad...')
            # Wait 2 seconds for visual effect
            time.sleep(2.0)
            self.keypad_pub.publish(String(data='4921'))

    def update_dashboard(self):
        # ANSI Clear screen and redraw
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.write("\033[1;36m===================================================================================\033[0m\n")
        sys.stdout.write("\033[1;32m      SHOPDRONE AUTONOMOUS MISSION SIMULATION - NUST COMPUTER SCIENCE GROUP        \033[0m\n")
        sys.stdout.write("\033[1;36m===================================================================================\033[0m\n")
        sys.stdout.write(f"  \033[1mOrder:\033[0m #1042 (2x Sugar, 1x Sunlight Soap, 1x Paracetamol)\n")
        sys.stdout.write(f"  \033[1mTarget Destination:\033[0m Matobo Ward 4, Zimbabwe (-20.553200, 28.514000)\n")
        sys.stdout.write("-----------------------------------------------------------------------------------\n")

        # Color-coded state badge
        state_color = "\033[1;33m"
        if self.current_state in ['EN_ROUTE', 'TAKEOFF']:
            state_color = "\033[1;34m"
        elif self.current_state in ['DELIVERY_COMPLETE', 'LANDED_AT_HUB']:
            state_color = "\033[1;32m"
        elif self.current_state in ['EMERGENCY_STOP', 'HOVER_OBSTACLE']:
            state_color = "\033[1;31m"

        sys.stdout.write(f"  \033[1mCurrent Flight State:\033[0m  {state_color}[ {self.current_state} ]\033[0m\n")
        sys.stdout.write(f"  \033[1mAltitude (AGL):\033[0m        \033[1;37m{self.altitude:.1f} meters\033[0m\n")
        sys.stdout.write(f"  \033[1mDrone GPS Location:\033[0m    Lat: {self.drone_lat:.6f}, Lon: {self.drone_lon:.6f}\n")

        # Battery gauge
        bat_color = "\033[1;32m" if self.battery_pct > 30 else "\033[1;31m"
        bar_len = int(self.battery_pct / 5)
        bar_str = "[" + "=" * bar_len + " " * (20 - bar_len) + "]"
        sys.stdout.write(f"  \033[1mBattery State:\033[0m         {bat_color}{bar_str} {self.battery_pct:.1f}%\033[0m\n")

        # Cargo lock status
        lock_str = "\033[1;31m[ LOCKED (Secure) ]\033[0m" if self.cargo_locked else "\033[1;32m[ UNLOCKED (Goods Accessible) ]\033[0m"
        sys.stdout.write(f"  \033[1mCargo Box Lock:\033[0m        {lock_str}\n")
        sys.stdout.write("-----------------------------------------------------------------------------------\n")
        sys.stdout.write(f"  \033[1;33mLatest System Alert:\033[0m   {self.latest_alert}\n")
        sys.stdout.write("\033[1;36m===================================================================================\033[0m\n")
        sys.stdout.write("  Press Ctrl+C to terminate the mission runner.\n")
        sys.stdout.flush()


def main(args=None):
    rclpy.init(args=args)
    node = MissionRunnerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
