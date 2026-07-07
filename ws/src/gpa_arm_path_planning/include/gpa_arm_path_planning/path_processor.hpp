 #pragma once

 #include <optional>
 #include <queue>
 #include <string>

 #include <rclcpp/rclcpp.hpp>

 namespace gpa_arm_path_planning
 {
 enum class WaypointType
 {
	 Travel,
	 Write
 };

 struct Waypoint
 {
	 WaypointType type;
	 double x;
	 double y;
	 double z;
 };

 class PathProcessorNode : public rclcpp::Node
 {
 public:
	 PathProcessorNode();

	 bool has_waypoints() const;
	 std::size_t queue_size() const;
	 std::optional<Waypoint> pop_next_waypoint();

 private:
	 bool load_waypoints_from_json(const std::string & file_path);

	 std::queue<Waypoint> waypoint_queue_;
 };
 }  // namespace gpa_arm_path_planning
