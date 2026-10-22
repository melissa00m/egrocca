import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    pkg_shopdrone = get_package_share_directory('shopdrone_simulation')
    robot_type = LaunchConfiguration('robot_type').perform(context).strip().lower()

    world_path = os.path.join(pkg_shopdrone, 'worlds', 'rural_zimbabwe.sdf')
    rviz_config = os.path.join(pkg_shopdrone, 'rviz', 'shopdrone.rviz')

    # Comprehensive Gazebo Harmonic resource path configuration
    resource_paths = [
        pkg_shopdrone,
        os.path.join(pkg_shopdrone, 'models'),
        os.path.join(pkg_shopdrone, 'models', 'shopdrone'),
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

    # 1. Start Gazebo Sim with the African Savannah world
    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        additional_env=gz_env,
        output='screen'
    )

    actions = [gz_sim]

    # 2. Select Controller and Dynamic Spawn (if aerial drone)
    if robot_type == 'drone':
        model_path = os.path.join(pkg_shopdrone, 'models', 'shopdrone', 'model.sdf')
        spawn_robot = ExecuteProcess(
            cmd=[
                'gz', 'service', '-s', '/world/rural_zimbabwe/create',
                '--reqtype', 'gz.msgs.EntityFactory',
                '--reptype', 'gz.msgs.Boolean',
                '--timeout', '5000',
                '--req', f'sdf_filename: "{model_path}", name: "shopdrone", pose: {{position: {{x: 0, y: 0, z: 0.22}}}}'
            ],
            additional_env=gz_env,
            output='screen'
        )
        actions.append(spawn_robot)

        controller_node = Node(
            package='shopdrone_simulation',
            executable='flight_controller',
            output='screen'
        )
    else: # Default: 'droid' (pre-spawned directly in rural_zimbabwe.sdf for 100% reliable startup)
        controller_node = Node(
            package='shopdrone_simulation',
            executable='ground_controller',
            output='screen'
        )

    actions.append(controller_node)

    # 3. ROS 2 <-> Gazebo Bridge (Velocity, Odometry, LiDAR & Camera)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/shopdroid/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/shopdroid/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/shopdrone/lidar@sensor_msgs/msg/LaserScan@gz.msgs.LaserScan',
            '/shopdrone/camera/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/shopdrone/camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo'
        ],
        output='screen'
    )
    actions.append(bridge)

    # 4. Common Subsystems (Cargo Lock OTP, Battery Monitor, Obstacle Monitor, Telemetry)
    cargo_lock_node = Node(
        package='shopdrone_simulation',
        executable='cargo_lock',
        output='screen'
    )
    actions.append(cargo_lock_node)

    battery_monitor_node = Node(
        package='shopdrone_simulation',
        executable='battery_monitor',
        output='screen'
    )
    actions.append(battery_monitor_node)

    obstacle_monitor_node = Node(
        package='shopdrone_simulation',
        executable='obstacle_monitor',
        output='screen'
    )
    actions.append(obstacle_monitor_node)

    telemetry_node = Node(
        package='shopdrone_simulation',
        executable='telemetry_publisher',
        output='screen'
    )
    actions.append(telemetry_node)

    # 5. Optional RViz2 Visualizer
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        condition=IfCondition(LaunchConfiguration('rviz')),
        output='screen'
    )
    actions.append(rviz_node)

    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot_type',
            default_value='droid',
            description='Select simulated robot type: "droid" (All-Terrain Terrestrial Droid) or "drone" (Legacy Multirotor)'
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='false',
            description='Launch RViz2 alongside Gazebo simulation'
        ),
        OpaqueFunction(function=launch_setup)
    ])
