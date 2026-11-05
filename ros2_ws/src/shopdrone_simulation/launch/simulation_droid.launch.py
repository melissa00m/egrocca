import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_shopdrone = get_package_share_directory('shopdrone_simulation')

    world_path = os.path.join(pkg_shopdrone, 'worlds', 'rural_zimbabwe.sdf')
    rviz_config = os.path.join(pkg_shopdrone, 'rviz', 'shopdrone.rviz')

    # Configure Gazebo Harmonic resource path for all models, textures, and worlds
    resource_paths = [
        pkg_shopdrone,
        os.path.join(pkg_shopdrone, 'models'),
        os.path.join(pkg_shopdrone, 'models', 'shopdroid'),
        os.path.join(pkg_shopdrone, 'materials'),
        os.path.join(pkg_shopdrone, 'meshes'),
        os.path.join(pkg_shopdrone, 'worlds')
    ]
    current_gz_res = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    all_gz_paths = ':'.join(filter(None, [current_gz_res] + resource_paths))
    os.environ['GZ_SIM_RESOURCE_PATH'] = all_gz_paths

    gz_env = {
        'GZ_SIM_RESOURCE_PATH': all_gz_paths,
        'QT_QPA_PLATFORM': 'xcb',
        'MESA_GL_VERSION_OVERRIDE': '4.5',
        'GZ_IP': '127.0.0.1',
        'GZ_PARTITION': 'shopdroid',
    }

    rviz_arg = DeclareLaunchArgument(
        'rviz',
        default_value='false',
        description='Launch RViz2 alongside Gazebo simulation'
    )

    # 1. Start Gazebo Sim with rural Zimbabwe savannah world (ShopDroid is pre-embedded)
    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        additional_env=gz_env,
        output='screen'
    )

    # 2. ROS 2 <-> Gazebo Bridge (Velocity, Odometry, LiDAR & Camera)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/shopdroid/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/shopdroid/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/shopdroid/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
            '/shopdrone/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/shopdrone/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image'
        ],
        output='screen'
    )

    # 3. Ground Controller Autopilot
    ground_controller_node = Node(
        package='shopdrone_simulation',
        executable='ground_controller',
        output='screen'
    )

    # 4. Core Security, Power and Telemetry Subsystems
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

    # 5. Optional RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )

    return LaunchDescription([
        rviz_arg,
        gz_sim,
        bridge,
        ground_controller_node,
        cargo_lock_node,
        battery_monitor_node,
        obstacle_monitor_node,
        telemetry_node,
        rviz_node
    ])
