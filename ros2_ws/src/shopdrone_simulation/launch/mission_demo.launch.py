import os
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    flight_controller_node = Node(
        package='shopdrone_simulation',
        executable='flight_controller',
        output='screen'
    )

    cargo_lock_node = Node(
        package='shopdrone_simulation',
        executable='cargo_lock',
        output='screen'
    )

    battery_monitor_node = Node(
        package='shopdrone_simulation',
        executable='battery_monitor',
        output='screen'
    )

    obstacle_monitor_node = Node(
        package='shopdrone_simulation',
        executable='obstacle_monitor',
        output='screen'
    )

    telemetry_node = Node(
        package='shopdrone_simulation',
        executable='telemetry_publisher',
        output='screen'
    )

    mission_runner_node = Node(
        package='shopdrone_simulation',
        executable='mission_runner',
        output='screen',
        emulate_tty=True
    )

    return LaunchDescription([
        flight_controller_node,
        cargo_lock_node,
        battery_monitor_node,
        obstacle_monitor_node,
        telemetry_node,
        mission_runner_node
    ])
