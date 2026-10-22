import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'shopdrone_simulation'

data_files = [
    ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
]

# Recursively include all simulation assets, launch files, models, textures, and rviz configs
for dir_name in ['launch', 'worlds', 'models', 'materials', 'meshes', 'rviz']:
    if os.path.exists(dir_name):
        for root, dirs, files in os.walk(dir_name):
            if files:
                install_dir = os.path.join('share', package_name, root)
                file_paths = [os.path.join(root, f) for f in files]
                data_files.append((install_dir, file_paths))

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=data_files,
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mphathisi Ndlovu',
    maintainer_email='n02529052a@nust.ac.zw',
    description='ROS 2 and Gazebo simulation package for ShopDrone rural delivery system',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'flight_controller = shopdrone_simulation.flight_controller:main',
            'ground_controller = shopdrone_simulation.ground_controller:main',
            'cargo_lock = shopdrone_simulation.cargo_lock:main',
            'battery_monitor = shopdrone_simulation.battery_monitor:main',
            'obstacle_monitor = shopdrone_simulation.obstacle_monitor:main',
            'telemetry_publisher = shopdrone_simulation.telemetry_publisher:main',
            'mission_runner = shopdrone_simulation.mission_runner:main',
        ],
    },
)
