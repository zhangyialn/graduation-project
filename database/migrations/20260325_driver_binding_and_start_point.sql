SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1) 扩展 users.role，增加 driver
ALTER TABLE users
  MODIFY COLUMN role ENUM('user','driver','approver','dispatcher','leader','admin')
  NOT NULL DEFAULT 'user';

-- 2) 扩展 drivers 表：绑定 user 和 vehicle，并统一状态
ALTER TABLE drivers
  ADD COLUMN user_id INT NULL AFTER id,
  ADD COLUMN vehicle_id INT NULL AFTER user_id;

UPDATE drivers SET status = 'unavailable' WHERE status = 'off';

ALTER TABLE drivers
  MODIFY COLUMN status ENUM('available','busy','unavailable') DEFAULT 'available';

-- 如已有司机数据，请先手动回填 user_id/vehicle_id 再执行下面两条 NOT NULL
-- 示例：UPDATE drivers SET user_id = 1, vehicle_id = 1 WHERE id = 1;
ALTER TABLE drivers
  MODIFY COLUMN user_id INT NOT NULL,
  MODIFY COLUMN vehicle_id INT NOT NULL;

CREATE UNIQUE INDEX uk_drivers_user_id ON drivers(user_id);
CREATE UNIQUE INDEX uk_drivers_vehicle_id ON drivers(vehicle_id);

-- 3) 扩展 car_applications：增加申请司机和起点
ALTER TABLE car_applications
  ADD COLUMN driver_id INT NULL AFTER department_id,
  ADD COLUMN start_point VARCHAR(120) NULL AFTER driver_id;

-- 如已有历史申请数据，请先按业务回填 driver_id 再执行 NOT NULL
-- 示例：UPDATE car_applications SET driver_id = 1 WHERE driver_id IS NULL;
ALTER TABLE car_applications
  MODIFY COLUMN driver_id INT NOT NULL;

CREATE INDEX idx_car_applications_driver_id ON car_applications(driver_id);

SET FOREIGN_KEY_CHECKS = 1;
