
# Dockerfile for Nav2 on RPI5(arm64)
FROM ubuntu:22.04 AS base

ARG USERNAME=user
ARG USERID=1000
ARG USERGID=${USERID}
ARG SHELL=bash
ARG DEBIAN_FRONTEND=noninteractive

ENV USERNAME=${USERNAME}
ENV SHELL=/bin/${SHELL}
ENV TERM=xterm-256color
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV ROS_DISTRO=humble

# Keep downloaded packages for caching purposes
# Ref: https://github.com/moby/buildkit/blob/master/frontend/dockerfile/docs/reference.md#example-cache-apt-packages
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && apt-get install -y \
    sudo \
    curl \
    wget \
    tmux \
    htop \
    git \
    gnupg2 \
    net-tools \
    build-essential \
    cmake \
    locales \
    nlohmann-json3-dev \
    python3-pip \
    python3-setuptools && \
    rm -rf /var/lib/apt/lists/*

# install ros2
COPY script/install-ros2.sh /tmp/install-ros2.sh
RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    chmod +x /tmp/install-ros2.sh && \
    ./tmp/install-ros2.sh && \
    rm /tmp/install-ros2.sh

# Install colcon and other Python tools
RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install -y \
    python3-colcon-common-extensions \
    python3-colcon-mixin \
    python3-rosdep \
    python3-vcstool && \
    rm -rf /var/lib/apt/lists/*

# Install useful ROS2 packages and dependency
RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install -y \
    ros-$ROS_DISTRO-rviz2 \
    ros-$ROS_DISTRO-geometry-msgs &&\
    rm -rf /var/lib/apt/lists/*

# Install gazebo
RUN --mount=type=cache,target=/var/cache/apt,sharing=private \
    apt-get update && \
    apt-get install -y \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-ros2-control \
    ros-humble-xacro \
    ros-humble-ros2-controllers \
    ros-humble-joint-state-publisher-gui


# Create a non-root user to use the container
RUN groupadd --gid ${USERGID} ${USERNAME} \
    && useradd --uid ${USERID} --gid ${USERGID} -m ${USERNAME} -s /bin/bash \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER ${USERNAME}
WORKDIR /home/${USERNAME}/ws
COPY ./settings/.bashrc /home/${USERNAME}/.bashrc 

RUN sudo apt autoremove -y && \
    sudo apt clean -y


SHELL ["/bin/bash", "-c"]
CMD ["bash"]