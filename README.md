# Docker for ROS2 Humble + Universal Robots Driver

This directory contains a Docker setup for Ubuntu 22.04 (ROS 2 Humble) with the Universal Robots ROS2 Driver.
本目录提供适用于 Ubuntu 22.04（ROS2 Humble）的 Docker 环境，内置 UR 官方 ROS2 驱动。

## Build 构建
```bash
docker build --no-cache -t ur_ros2:latest ./docker
```

## Run 运行
```bash
docker run -it --name ur_ros2_dev ur_ros2:latest
```

## Test ROS2 通信测试
Terminal A (inside container):
```bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp talker
```
Terminal B (host -> same container):
```bash
docker exec -it ur_ros2_dev bash
source /opt/ros/humble/setup.bash
ros2 run demo_nodes_cpp listener
```

## Verify UR packages 验证 UR 包
```bash
source /ros2_ws/install/setup.bash
ros2 pkg list | grep -E '^ur_'
```

## Notes 注意
- Base image: `osrf/ros:humble-desktop`
- UR repo branch pinned to `humble`
- Installed `ros-humble-ros2-control` and `ros-humble-ros2-controllers`
- Disabled tests during build (`-DBUILD_TESTING=OFF`)
