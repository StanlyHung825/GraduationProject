#include "gpa_arm_path_planning/path_processor.hpp"

#include <ament_index_cpp/get_package_share_directory.hpp>

#include <exception>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <vector>

#include <nlohmann/json.hpp>

namespace gpa_arm_path_planning
{
void from_json(const nlohmann::json & json_value, WaypointType & type)
{
  const auto type_str = json_value.get<std::string>();
  if (type_str == "travel") {
    type = WaypointType::Travel;
    return;
  }

  if (type_str == "write") {
    type = WaypointType::Write;
    return;
  }

  throw std::invalid_argument("Unknown waypoint type: " + type_str);
}

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Waypoint, type, x, y, z);

namespace
{
std::string get_default_path_file()
{
  const auto share_dir =
    ament_index_cpp::get_package_share_directory("gpa_arm_path_planning");
  return share_dir + "/paths/path_example.json";
}

const char * to_cstr(WaypointType type)
{
  return type == WaypointType::Travel ? "travel" : "write";
}

}  // namespace

PathProcessorNode::PathProcessorNode()
: Node("path_processor_node")
{
  const auto file_path = get_default_path_file();

  if (!load_waypoints_from_json(file_path)) {
    RCLCPP_ERROR(get_logger(), "Failed to load waypoints from: %s", file_path.c_str());
    return;
  }

  RCLCPP_INFO(
    get_logger(), "Loaded %zu waypoints from %s", waypoint_queue_.size(), file_path.c_str());
}

bool PathProcessorNode::has_waypoints() const
{
  return !waypoint_queue_.empty();
}

std::size_t PathProcessorNode::queue_size() const
{
  return waypoint_queue_.size();
}

std::optional<Waypoint> PathProcessorNode::pop_next_waypoint()
{
  if (waypoint_queue_.empty()) {
    return std::nullopt;
  }

  Waypoint next = waypoint_queue_.front();
  waypoint_queue_.pop();
  return next;
}

bool PathProcessorNode::load_waypoints_from_json(const std::string & file_path)
{
  std::ifstream input(file_path);
  if (!input.is_open()) {
    RCLCPP_ERROR(get_logger(), "Cannot open JSON file: %s", file_path.c_str());
    return false;
  }

  nlohmann::json json_data;
  try {
    input >> json_data;
  } catch (const std::exception & ex) {
    RCLCPP_ERROR(get_logger(), "Invalid JSON in %s: %s", file_path.c_str(), ex.what());
    return false;
  }

  if (!json_data.is_array()) {
    RCLCPP_ERROR(get_logger(), "JSON root must be an array of waypoints");
    return false;
  }

  std::vector<Waypoint> parsed_waypoints;
  try {
    parsed_waypoints = json_data.get<std::vector<Waypoint>>();
  } catch (const std::exception & ex) {
    RCLCPP_ERROR(get_logger(), "Invalid waypoint payload: %s", ex.what());
    return false;
  }

  std::queue<Waypoint> parsed_queue;

  for (const auto & waypoint : parsed_waypoints) {
    parsed_queue.push(waypoint);
  }

  waypoint_queue_ = std::move(parsed_queue);

  if (!waypoint_queue_.empty()) {
    const auto & first = waypoint_queue_.front();
    RCLCPP_INFO(
      get_logger(),
      "First waypoint: type=%s x=%.3f y=%.3f z=%.3f",
      to_cstr(first.type),
      first.x,
      first.y,
      first.z);
  }

  return true;
}
}  // namespace gpa_arm_path_planning

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<gpa_arm_path_planning::PathProcessorNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
