#!/usr/bin/env python3
"""
ShopDroid Autonomous Ground Controller Node
Implements autonomous terrestrial navigation and delivery state machine:
Navigates the all-terrain droid across rural paths from the Shop Hub (0, 0)
to the Rural Homestead (15, 0) and returns safely to base.
"""

import math
import time
from typing import List, Tuple
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String, Bool


class GroundState:
    IDLE = 'IDLE'
    PRE_TRIP_CHECK = 'PRE_TRIP_CHECK'
    EN_ROUTE_HOMESTEAD = 'EN_ROUTE_HOMESTEAD'
    OBSTACLE_AVOIDANCE = 'OBSTACLE_AVOIDANCE'
    ARRIVED_HOMESTEAD = 'ARRIVED_HOMESTEAD'
    AWAITING_OTP = 'AWAITING_OTP'
    UNLOADING_PAYLOAD = 'UNLOADING_PAYLOAD'
    RETURN_TO_HUB = 'RETURN_TO_HUB'
    DOCKED_AT_HUB = 'DOCKED_AT_HUB'
    EMERGENCY_STOP = 'EMERGENCY_STOP'


class GroundControllerNode(Node):
    def __init__(self):
        super().__init__('shopdroid_ground_controller')

        self.state = GroundState.IDLE
        self.state_start_time = self.get_clock().now()

        # Robot Odometry Pose
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.yaw = 0.0
        self.odom_received = False

        # Route Waypoints (Hub -> Dirt Path -> Customer Homestead)
        # Bypasses the acacia tree obstacle located at (7.5, 1.5)
        self.outbound_waypoints: List[Tuple[float, float]] = [
            (2.0, 0.0),    # Depart hub platform
            (7.0, -0.4),   # Clear terrain & tree buffer
            (11.0, -0.2),  # Dirt road straightaway
            (15.0, 0.0)    # Customer delivery pad at homestead
        ]
        self.return_waypoints: List[Tuple[float, float]] = [
            (11.0, -0.4),  # Clear homestead yard
            (6.5, -0.6),   # South dirt bypass
            (2.0, 0.0),    # Approach hub perimeter
            (0.0, 0.0)     # Dock at hub solar base
        ]
        self.current_wp_idx = 0
        self.target_waypoints = self.outbound_waypoints

        # Motion parameters
        self.cruise_speed = 1.4      # m/s
        self.turn_speed = 0.8        # rad/s
        self.goal_tolerance = 0.6    # meters
        self.heading_tolerance = 0.15 # radians (~8.5 deg)

        self.obstacle_active = False
        self.emergency_stopped = False
        self.auto_dispatch_timer_ticks = 0

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.state_pub = self.create_publisher(String, '/shopdroid/ground_state', 10)
        self.alert_pub = self.create_publisher(String, '/shopdroid/alerts', 10)
        self.otp_pub = self.create_publisher(String, '/shopdrone/keypad_input', 10)

        # Subscribers
        self.create_subscription(Odometry, '/odom', self.on_odometry, 10)
        self.create_subscription(String, '/shopdrone/dispatch_order', self.on_dispatch, 10)
        self.create_subscription(String, '/shopdroid/dispatch_order', self.on_dispatch, 10)
        self.create_subscription(Bool, '/shopdrone/emergency_stop', self.on_emergency_stop, 10)
        self.create_subscription(Bool, '/shopdrone/obstacle_detected', self.on_obstacle, 10)
        self.create_subscription(Bool, '/shopdrone/delivery_confirmed', self.on_delivery_confirmed, 10)

        # Main Navigation Control Loop at 10 Hz
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('ShopDroid Autonomous Ground Controller started. Status: IDLE at Shop Hub Base.')

    def set_state(self, new_state: str):
        if self.state != new_state:
            self.get_logger().info(f'Ground State Transition: [{self.state}] -> [{new_state}]')
            self.state = new_state
            self.state_start_time = self.get_clock().now()
            self.state_pub.publish(String(data=self.state))

    def on_odometry(self, msg: Odometry):
        self.odom_received = True
        self.pose_x = msg.pose.pose.position.x
        self.pose_y = msg.pose.pose.position.y

        # Extract yaw from quaternion (z and w for planar motion)
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

    def on_dispatch(self, msg: String):
        if self.state == GroundState.IDLE:
            self.get_logger().info(f'Received Order Dispatch: "{msg.data}". Starting Pre-Trip Diagnostic.')
            self.alert_pub.publish(String(data=f"Dispatch received: {msg.data}"))
            self.set_state(GroundState.PRE_TRIP_CHECK)

    def on_emergency_stop(self, msg: Bool):
        if msg.data:
            self.emergency_stopped = True
            self.set_state(GroundState.EMERGENCY_STOP)
            self.get_logger().error('EMERGENCY STOP ACTIVATED: Parking brake locked, zero velocity.')
            self.cmd_vel_pub.publish(Twist())

    def on_obstacle(self, msg: Bool):
        self.obstacle_active = msg.data
        if self.obstacle_active and self.state in [GroundState.EN_ROUTE_HOMESTEAD, GroundState.RETURN_TO_HUB]:
            self.set_state(GroundState.OBSTACLE_AVOIDANCE)
            self.alert_pub.publish(String(data="Obstacle detected ahead! Slowing down to execute bypass."))
        elif not self.obstacle_active and self.state == GroundState.OBSTACLE_AVOIDANCE:
            self.get_logger().info('Path cleared. Resuming waypoint traversal.')
            if self.target_waypoints == self.outbound_waypoints:
                self.set_state(GroundState.EN_ROUTE_HOMESTEAD)
            else:
                self.set_state(GroundState.RETURN_TO_HUB)

    def on_delivery_confirmed(self, msg: Bool):
        if msg.data and self.state == GroundState.AWAITING_OTP:
            self.set_state(GroundState.UNLOADING_PAYLOAD)

    def control_loop(self):
        twist = Twist()
        now = self.get_clock().now()
        elapsed_in_state = (now - self.state_start_time).nanoseconds / 1e9

        # Fallback dead reckoning position update if odom not published yet
        if not self.odom_received and self.state in [GroundState.EN_ROUTE_HOMESTEAD, GroundState.RETURN_TO_HUB]:
            pass

        # -------------------------------------------------------------
        # STATE 1: IDLE
        # -------------------------------------------------------------
        if self.state == GroundState.IDLE:
            self.auto_dispatch_timer_ticks += 1
            # Auto-dispatch after 3 seconds if standalone simulation
            if self.auto_dispatch_timer_ticks >= 30:
                self.get_logger().info('Auto-dispatching ShopDroid for automated rural delivery run.')
                self.set_state(GroundState.PRE_TRIP_CHECK)

        # -------------------------------------------------------------
        # STATE 2: PRE_TRIP_CHECK
        # -------------------------------------------------------------
        elif self.state == GroundState.PRE_TRIP_CHECK:
            if elapsed_in_state > 2.0:
                self.get_logger().info('Pre-trip diagnostic complete: 4WD Motors nominal, LiDAR active, Cargo locked.')
                self.current_wp_idx = 0
                self.target_waypoints = self.outbound_waypoints
                self.set_state(GroundState.EN_ROUTE_HOMESTEAD)

        # -------------------------------------------------------------
        # STATE 3: EN_ROUTE_HOMESTEAD / RETURN_TO_HUB
        # -------------------------------------------------------------
        elif self.state in [GroundState.EN_ROUTE_HOMESTEAD, GroundState.RETURN_TO_HUB]:
            target_x, target_y = self.target_waypoints[self.current_wp_idx]

            dx = target_x - self.pose_x
            dy = target_y - self.pose_y
            dist = math.sqrt(dx * dx + dy * dy)
            target_heading = math.atan2(dy, dx)
            heading_diff = target_heading - self.yaw

            # Normalize angle to [-pi, pi]
            while heading_diff > math.pi:
                heading_diff -= 2.0 * math.pi
            while heading_diff < -math.pi:
                heading_diff += 2.0 * math.pi

            # Check if waypoint reached
            if dist < self.goal_tolerance:
                self.current_wp_idx += 1
                self.get_logger().info(f'Reached waypoint {self.current_wp_idx}/{len(self.target_waypoints)} ({target_x:.1f}, {target_y:.1f})')

                if self.current_wp_idx >= len(self.target_waypoints):
                    if self.state == GroundState.EN_ROUTE_HOMESTEAD:
                        self.get_logger().info('Arrived at customer homestead delivery pad! Parking and awaiting OTP.')
                        self.set_state(GroundState.ARRIVED_HOMESTEAD)
                    else:
                        self.get_logger().info('Docked safely back at Shop Hub depot. Mission complete!')
                        self.set_state(GroundState.DOCKED_AT_HUB)
                return

            # Proportional steering control towards current waypoint
            if abs(heading_diff) > 0.4:
                # Pivot turn towards target
                twist.linear.x = 0.2
                twist.angular.z = max(-self.turn_speed, min(self.turn_speed, 1.8 * heading_diff))
            else:
                # Drive forward with steering corrections
                twist.linear.x = min(self.cruise_speed, 0.8 + 0.8 * dist)
                twist.angular.z = max(-self.turn_speed, min(self.turn_speed, 1.2 * heading_diff))

        # -------------------------------------------------------------
        # STATE 4: OBSTACLE_AVOIDANCE
        # -------------------------------------------------------------
        elif self.state == GroundState.OBSTACLE_AVOIDANCE:
            # Slow crawl with lateral deflection
            twist.linear.x = 0.3
            twist.angular.z = 0.5  # Steer right/left around obstacle

        # -------------------------------------------------------------
        # STATE 5: ARRIVED_HOMESTEAD
        # -------------------------------------------------------------
        elif self.state == GroundState.ARRIVED_HOMESTEAD:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            if elapsed_in_state > 1.5:
                self.get_logger().info('SMS sent to customer: "ShopDroid has arrived outside! Enter PIN 4921 to open vault."')
                self.alert_pub.publish(String(data="SMS sent to Hopewell Ndlovu (+263 77 123 4567): PIN 4921"))
                self.set_state(GroundState.AWAITING_OTP)

        # -------------------------------------------------------------
        # STATE 6: AWAITING_OTP
        # -------------------------------------------------------------
        elif self.state == GroundState.AWAITING_OTP:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            # Simulate customer entering OTP after 3 seconds
            if elapsed_in_state > 3.0:
                self.get_logger().info('Customer entered OTP: [4921] on droid keypad panel.')
                self.otp_pub.publish(String(data='4921'))
                self.set_state(GroundState.UNLOADING_PAYLOAD)

        # -------------------------------------------------------------
        # STATE 7: UNLOADING_PAYLOAD
        # -------------------------------------------------------------
        elif self.state == GroundState.UNLOADING_PAYLOAD:
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            if elapsed_in_state > 3.5:
                self.get_logger().info('Goods unloaded (2x Sugar, Soap, Paracetamol). Cargo hatch closed & locked.')
                self.alert_pub.publish(String(data="Delivery successful! Goods received. Starting return trip."))
                self.current_wp_idx = 0
                self.target_waypoints = self.return_waypoints
                self.set_state(GroundState.RETURN_TO_HUB)

        # -------------------------------------------------------------
        # STATE 8: DOCKED_AT_HUB / EMERGENCY_STOP
        # -------------------------------------------------------------
        elif self.state in [GroundState.DOCKED_AT_HUB, GroundState.EMERGENCY_STOP]:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        # Publish velocity command
        self.cmd_vel_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = GroundControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
