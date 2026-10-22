#!/usr/bin/env python3
"""
ShopDrone Autonomous Flight Controller Node
Implements full delivery mission state machine from SRS Section 4.6 and Appendix B.1.
"""

import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Bool


class FlightState:
    IDLE = 'IDLE'
    PRE_FLIGHT_CHECK = 'PRE_FLIGHT_CHECK'
    TAKEOFF = 'TAKEOFF'
    EN_ROUTE = 'EN_ROUTE'
    HOVER_OBSTACLE = 'HOVER_OBSTACLE'
    LANDING = 'LANDING'
    AWAITING_OTP = 'AWAITING_OTP'
    DELIVERY_COMPLETE = 'DELIVERY_COMPLETE'
    RETURN_TO_HUB = 'RETURN_TO_HUB'
    LANDED_AT_HUB = 'LANDED_AT_HUB'
    EMERGENCY_STOP = 'EMERGENCY_STOP'


class FlightControllerNode(Node):
    def __init__(self):
        super().__init__('shopdrone_flight_controller')

        self.state = FlightState.IDLE
        self.state_start_time = self.get_clock().now()

        # Altitude and progress tracking
        self.current_height = 0.0
        self.cruise_altitude = 15.0 # meters
        self.distance_traveled = 0.0
        self.target_distance = 100.0 # simulation meters to customer waypoint

        self.obstacle_active = False
        self.emergency_stopped = False

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.state_pub = self.create_publisher(String, '/shopdrone/flight_state', 10)
        self.alert_pub = self.create_publisher(String, '/shopdrone/alerts', 10)

        # Subscribers
        self.create_subscription(String, '/shopdrone/dispatch_order', self.on_dispatch, 10)
        self.create_subscription(Bool, '/shopdrone/emergency_stop', self.on_emergency_stop, 10)
        self.create_subscription(Bool, '/shopdrone/obstacle_detected', self.on_obstacle, 10)
        self.create_subscription(Bool, '/shopdrone/delivery_confirmed', self.on_delivery_confirmed, 10)
        self.create_subscription(Bool, '/shopdrone/failsafe_rth', self.on_failsafe_rth, 10)

        # Main control loop at 10 Hz
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('ShopDrone Autonomous Flight Controller started. Status: IDLE at Shop Hub.')

    def set_state(self, new_state: str):
        if self.state != new_state:
            self.get_logger().info(f'Flight State Transition: [{self.state}] -> [{new_state}]')
            self.state = new_state
            self.state_start_time = self.get_clock().now()
            self.state_pub.publish(String(data=self.state))

    def on_dispatch(self, msg: String):
        if self.state == FlightState.IDLE:
            self.get_logger().info(f'Received order dispatch: "{msg.data}". Initiating Pre-Flight Checks.')
            self.set_state(FlightState.PRE_FLIGHT_CHECK)

    def on_emergency_stop(self, msg: Bool):
        if msg.data:
            self.emergency_stopped = True
            self.set_state(FlightState.EMERGENCY_STOP)
            self.get_logger().error('EMERGENCY STOP ACTIVATED! Cutting motor throttle immediately (SRS 4.6).')
            self.cmd_vel_pub.publish(Twist()) # Zero velocity

    def on_obstacle(self, msg: Bool):
        self.obstacle_active = msg.data
        if self.obstacle_active and self.state == FlightState.EN_ROUTE:
            self.set_state(FlightState.HOVER_OBSTACLE)
        elif not self.obstacle_active and self.state == FlightState.HOVER_OBSTACLE:
            self.get_logger().info('Obstacle cleared. Resuming flight path to customer.')
            self.set_state(FlightState.EN_ROUTE)

    def on_delivery_confirmed(self, msg: Bool):
        if msg.data and self.state == FlightState.AWAITING_OTP:
            self.set_state(FlightState.DELIVERY_COMPLETE)

    def on_failsafe_rth(self, msg: Bool):
        if msg.data and self.state not in [FlightState.IDLE, FlightState.LANDED_AT_HUB, FlightState.EMERGENCY_STOP]:
            self.get_logger().warn('FAILSAFE RTH: Battery or signal critical. Aborting mission, returning to Hub.')
            self.set_state(FlightState.RETURN_TO_HUB)

    def control_loop(self):
        twist = Twist()

        if self.state == FlightState.IDLE:
            pass

        elif self.state == FlightState.PRE_FLIGHT_CHECK:
            # Simulate 2-second check
            elapsed = (self.get_clock().now() - self.state_start_time).nanoseconds / 1e9
            if elapsed > 2.0:
                self.get_logger().info('Pre-flight checks passed: Battery OK, GPS Locked, Weather Clear.')
                self.set_state(FlightState.TAKEOFF)

        elif self.state == FlightState.TAKEOFF:
            # Ascend vertically to cruise altitude
            twist.linear.z = 1.5
            self.current_height += 0.15
            if self.current_height >= self.cruise_altitude:
                self.current_height = self.cruise_altitude
                self.get_logger().info(f'Cruise altitude of {self.cruise_altitude}m reached. Cruising to delivery zone.')
                self.set_state(FlightState.EN_ROUTE)

        elif self.state == FlightState.EN_ROUTE:
            # Fly forward along waypoint vector
            twist.linear.x = 4.0 # 4 m/s forward velocity
            self.distance_traveled += 0.4
            if self.distance_traveled >= self.target_distance:
                self.get_logger().info('Arrived at customer coordinates (Matobo Ward 4). Starting descent.')
                self.set_state(FlightState.LANDING)

        elif self.state == FlightState.HOVER_OBSTACLE:
            # Hover in place safely
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.linear.z = 0.0

        elif self.state == FlightState.LANDING:
            # Descend slowly to customer landing spot
            twist.linear.z = -1.0
            self.current_height = max(0.0, self.current_height - 0.1)
            if self.current_height <= 0.0:
                self.current_height = 0.0
                self.get_logger().info('ShopDrone safely landed at customer spot. SMS alert sent. Waiting for OTP unlock (SRS 4.8).')
                self.set_state(FlightState.AWAITING_OTP)

        elif self.state == FlightState.AWAITING_OTP:
            # Waiting for customer keypad input
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.linear.z = 0.0

        elif self.state == FlightState.DELIVERY_COMPLETE:
            # Wait 3 seconds for customer to take items and lid to close
            elapsed = (self.get_clock().now() - self.state_start_time).nanoseconds / 1e9
            if elapsed > 3.0:
                self.get_logger().info('Cargo box re-locked. Preparing for Return-to-Hub takeoff.')
                self.set_state(FlightState.RETURN_TO_HUB)

        elif self.state == FlightState.RETURN_TO_HUB:
            # Ascend then fly back to base
            if self.current_height < self.cruise_altitude:
                twist.linear.z = 1.5
                self.current_height += 0.15
            else:
                twist.linear.x = -4.0 # Fly backwards toward hub
                self.distance_traveled = max(0.0, self.distance_traveled - 0.4)
                if self.distance_traveled <= 0.0:
                    self.set_state(FlightState.LANDED_AT_HUB)

        elif self.state == FlightState.LANDED_AT_HUB:
            twist.linear.z = -1.0
            self.current_height = max(0.0, self.current_height - 0.1)
            if self.current_height <= 0.0:
                self.current_height = 0.0
                twist.linear.z = 0.0
                self.set_state(FlightState.IDLE)
                self.get_logger().info('>>> MISSION COMPLETE: ShopDrone safely returned to Shop Hub base. Ready for next order.')

        elif self.state == FlightState.EMERGENCY_STOP:
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.linear.z = -2.0 # Force emergency descent

        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = FlightControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
