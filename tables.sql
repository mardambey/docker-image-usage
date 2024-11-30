CREATE TABLE `docker_image_usage` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `image_name` varchar(255) DEFAULT NULL,
  `image_tag` varchar(255) DEFAULT NULL,
  `container_id` varchar(255) DEFAULT NULL,
  `container_name` varchar(255) DEFAULT NULL,
  `event_time` datetime DEFAULT NULL,
  `event_type` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `image_name` (`image_name`),
  KEY `event_time` (`event_time`),
  KEY `event_type` (`event_type`)
);

