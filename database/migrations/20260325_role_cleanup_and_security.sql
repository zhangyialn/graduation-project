SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1) 角色值迁移：清理冗余角色
UPDATE users SET role = 'approver' WHERE role = 'leader';
UPDATE users SET role = 'admin' WHERE role = 'dispatcher';

-- 2) 收敛 users.role 枚举
ALTER TABLE users
  MODIFY COLUMN role ENUM('user','driver','approver','admin')
  NOT NULL DEFAULT 'user';

-- 3) 增加首次登录改密标记
ALTER TABLE users
  ADD COLUMN must_change_password TINYINT(1) NOT NULL DEFAULT 0 AFTER import_batch_id;

-- 4) 存量用户统一开启首次改密（按需可改为仅新用户）
UPDATE users
SET must_change_password = 1
WHERE is_deleted = 0;

SET FOREIGN_KEY_CHECKS = 1;
