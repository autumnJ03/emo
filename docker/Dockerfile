# Ubuntu 22.04 + ROS 2 Humble Desktop
FROM osrf/ros:humble-desktop

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 基础工具与依赖
RUN apt-get update && apt-get install -y     git build-essential     python3-rosdep python3-colcon-common-extensions python3-vcstool     ros-humble-ros2-control ros-humble-ros2-controllers     socat nano less iputils-ping net-tools  && rm -rf /var/lib/apt/lists/*

# 初始化 rosdep（容忍已初始化）
SHELL ["/bin/bash","-lc"]
RUN rosdep init || true && rosdep update

# 拉取 UR 官方仓库（固定 humble 分支）
WORKDIR /ros2_ws/src
RUN git clone --branch humble --depth=1 https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver.git

# 安装依赖并编译（显式加载 ROS 环境 + 指定发行版 + 关闭测试）
WORKDIR /ros2_ws
RUN apt-get update  && source /opt/ros/humble/setup.bash  && rosdep install --from-paths src --ignore-src -r -y --rosdistro humble  && colcon build --symlink-install --cmake-args -DBUILD_TESTING=OFF

# 进入容器时自动加载工程环境
RUN echo "source /ros2_ws/install/setup.bash" >> /etc/bash.bashrc

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
