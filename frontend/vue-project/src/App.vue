<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script setup>
// App.vue
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
  line-height: 1.6;
  color: #2d3436;
  background-color: #f4f7ed;
  font-size: 14px;
  font-weight: 400;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  min-height: 100vh;
}

/* 全局按钮美化 */
:deep(.el-button) {
  border-radius: 6px !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-button.is-primary) {
  background: linear-gradient(135deg, #6b8e23 0%, #556b2f 100%) !important;
  border: none !important;
  color: #ffffff !important;
}

:deep(.el-button.is-primary:hover) {
  background: linear-gradient(135deg, #556b2f 0%, #3d5a1f 100%) !important;
  border-color: #556b2f !important;
  box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3) !important;
}

:deep(.el-button.is-plain) {
  background-color: #f0f3eb !important;
  border-color: #d4dcc9 !important;
  color: #6b8e23 !important;
}

:deep(.el-button.is-plain:hover) {
  background-color: #e5edd8 !important;
  border-color: #c5cdb6 !important;
  color: #556b2f !important;
}

/* 表单项美化 */
:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  color: #2d3436;
  font-weight: 500;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  transition: all 0.3s ease;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: #d4c5b9;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05), 0 0 0 3px rgba(107, 142, 35, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.15);
}

:deep(.el-input__prefix) {
  color: #8b7355;
}

/* 卡片美化 */
:deep(.el-card) {
  border-radius: 12px;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  background-color: #ffffff;
}

:deep(.el-card:hover) {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border-color: #d4c5b9;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  border-bottom: 1px solid #e5ddd2;
}

/* 日期选择器美化 */
:deep(.el-date-editor) {
  width: 100%;
}

:deep(.el-date-editor .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
  border-radius: 6px;
}

/* 数字输入美化 */
:deep(.el-input-number .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.03);
}

/* 提示框美化 */
:deep(.el-alert) {
  border-radius: 6px;
  border: 1px solid transparent;
}

:deep(.el-alert.is-error) {
  background-color: #fef0f0;
  border-color: #fde2e4;
  color: #f56c6c;
}

:deep(.el-alert.is-success) {
  background-color: #f0f9ff;
  border-color: #c6e2ff;
  color: #67c23a;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #d4c5b9;
  border-radius: 4px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: #6b8e23;
}

/* 表格美化 */
:deep(.el-table) {
  background-color: #ffffff;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-table__header) {
  background-color: #f4f7ed;
}

:deep(.el-table__header-wrapper th) {
  background-color: #f4f7ed;
  color: #2d3436;
  font-weight: 600;
  border-bottom-color: #e5ddd2;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #fefdfb !important;
}

:deep(.el-table__body-wrapper tbody tr:hover) {
  background-color: #fefdfb;
}

:deep(.el-table td) {
  border-bottom-color: #e5ddd2;
}

/* 下拉框美化 */
:deep(.el-select .el-input__wrapper) {
  background-color: #fefdfb;
  border: 1px solid #e5ddd2;
  border-radius: 6px;
}

:deep(.el-select .el-input__wrapper:hover) {
  border-color: #d4c5b9;
}

:deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #6b8e23;
  box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.15);
}

:deep(.el-popper.is-dark) {
  background: #ffffff;
  border: 1px solid #e5ddd2;
}

:deep(.el-select-dropdown) {
  background-color: #ffffff;
  border: 1px solid #e5ddd2;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-option) {
  color: #2d3436;
  padding: 10px 16px;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-option:hover) {
  background-color: #f4f7ed;
}

:deep(.el-option.selected) {
  background-color: #eff3e6;
  color: #6b8e23;
  font-weight: 500;
}

/* 对话框美化 */
:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f4f7ed 0%, #eff3e6 100%);
  border-bottom: 1px solid #e5ddd2;
}

:deep(.el-dialog__title) {
  color: #2d3436;
  font-weight: 600;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-dialog__body) {
  background-color: #ffffff;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-dialog__footer) {
  background-color: #ffffff;
  border-top: 1px solid #eee;
}

/* 分页美化 */
:deep(.el-pagination) {
  color: #2d3436;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-pager li) {
  color: #2d3436;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-pager li.active) {
  color: #ffffff;
  background-color: #6b8e23;
}

:deep(.el-pager li:hover) {
  color: #6b8e23;
}

:deep(.el-pagination button) {
  color: #2d3436;
}

:deep(.el-pagination button:hover) {
  color: #6b8e23;
}

/* 标签美化 */
:deep(.el-tag) {
  border-radius: 4px;
  font-weight: 500;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-tag.el-tag--success) {
  background-color: #d1fae5;
  border-color: #a7f3d0;
  color: #065f46;
}

:deep(.el-tag.el-tag--warning) {
  background-color: #fef3c7;
  border-color: #fde68a;
  color: #92400e;
}

:deep(.el-tag.el-tag--danger) {
  background-color: #fee2e2;
  border-color: #fecaca;
  color: #dc2626;
}

:deep(.el-tag.el-tag--info) {
  background-color: #e0f2fe;
  border-color: #bae6fd;
  color: #0369a1;
}

/* 标签页美化 */
:deep(.el-tabs__header) {
  border-bottom: 1px solid #e5ddd2;
}

:deep(.el-tabs__nav) {
  border-bottom: none;
}

:deep(.el-tabs__item) {
  color: #2d3436;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-tabs__item.is-active) {
  color: #6b8e23;
  font-weight: 500;
}

:deep(.el-tabs__item:hover) {
  color: #6b8e23;
}

:deep(.el-tabs__active-bar) {
  background-color: #6b8e23;
}

/* 输入框前缀图标美化 */
:deep(.el-input__prefix) {
  color: #6b8e23;
}

/* 弹出菜单美化 */
:deep(.el-dropdown-menu) {
  background-color: #ffffff;
  border: 1px solid #e5ddd2;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-dropdown-menu__item) {
  color: #2d3436;
  font-family: 'Noto Sans SC', 'Noto Sans', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, Roboto, sans-serif !important;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f4f7ed;
  color: #6b8e23;
}

/* 清空按钮美化 */
:deep(.el-input__clear) {
  color: #8b7355;
}

:deep(.el-input__clear:hover) {
  color: #6b8e23;
}
</style>