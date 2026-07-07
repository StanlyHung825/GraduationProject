cmake_minimum_required(VERSION 3.8)
project(gpa_arm_path_planning)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(nlohmann_json REQUIRED)

include_directories(include)

add_executable(path_processor_node src/path_processor_node.cpp)
ament_target_dependencies(path_processor_node rclcpp ament_index_cpp)
target_link_libraries(path_processor_node nlohmann_json::nlohmann_json)

install(
  TARGETS path_processor_node
  DESTINATION lib/${PROJECT_NAME}
)
install(DIRECTORY
  paths
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
