# 眼动数据处理系统 - 移除Session功能更新

## 概述
已成功移除所有session相关功能，改为使用统一的文件命名策略，简化了系统架构并提高了可维护性。

## 主要变更

### 1. 移除的内容
- 删除了所有 `get_session_folder()` 和 `create_session_folder()` 的调用
- 移除了 `from app.model import` 导入
- 不再使用动态session目录

### 2. 统一文件命名策略

#### 上传文件 (存储在 UPLOAD_FOLDER)
- `video.mp4` - 视频文件
- `gaze_data.xlsx` - Excel眼动数据文件
- `config_image.png` - 配置用的图像文件

#### 输出文件 (存储在 OUTPUT_FOLDER)
- `segments.json` - 初始视频分割结果
- `segments_25fps.json` - 调整后的25fps分割数据
- `markers.json` - 标记点坐标数据
- `tags.json` - AprilTag和ArUco标记信息
- `config_image.png` - 处理后的配置图像
- `raw_gaze/` - 原始眼动数据目录
  - `{participant}.npy` - 各参与者的原始眼动数据
- `final_output/` - 最终处理结果目录
  - 各种可视化图像和分析结果

### 3. 修改的API端点

#### `/api/frame_config`
- 统一保存为 `config_image.png`
- 输出保存为 `tags.json` 和 `markers.json`
- 图像保存到 OUTPUT_FOLDER

#### `/api/extract_raw_gaze`
- 统一保存Excel文件为 `gaze_data.xlsx`
- 输出.npy文件到 `raw_gaze/` 目录

#### `/api/detect_segments`
- 统一保存视频为 `video.mp4`
- 输出保存为 `segments.json`
- 包含fps信息

#### `/api/submit_segments`
- 保存调整后分割为 `segments_25fps.json`
- 自动触发眼动数据处理
- 输出到 `final_output/` 目录

#### `/api/results/<filename>`
- 支持从多个目录查找文件
- 优先级：UPLOAD_FOLDER → OUTPUT_FOLDER → raw_gaze → final_output

#### `/api/upload_user_result/<index>`
- 根据文件类型自动选择存储目录
- 视频文件存储到 UPLOAD_FOLDER
- 其他文件存储到 OUTPUT_FOLDER

#### `/api/submit_final_results`
- 使用统一的文件路径
- 自动处理眼动数据
- 输出到 `final_output/` 目录

#### `/api/view_json/<filename>`
- 支持从多个目录查找JSON文件
- 优先查找 OUTPUT_FOLDER，然后是 UPLOAD_FOLDER

### 4. 新增API端点

#### `/api/check_existing_files`
- 检查所有关键文件的存在状态
- 返回布尔值表示各文件是否存在

#### `/api/get_final_results`
- 获取最终处理结果
- 支持图像base64编码和JSON数据返回

### 5. 文件组织结构

```
backend/var/
├── uploads/                    # 用户上传的原始文件
│   ├── video.mp4              # 统一命名的视频文件
│   ├── gaze_data.xlsx         # 统一命名的Excel文件
│   └── config_image.png       # 统一命名的配置图像
└── outputs/                   # 处理结果输出
    ├── segments.json          # 视频分割结果
    ├── segments_25fps.json    # 调整后分割
    ├── markers.json           # 标记点数据
    ├── tags.json             # 标记信息
    ├── config_image.png      # 处理后图像
    ├── raw_gaze/             # 原始眼动数据
    │   └── *.npy
    └── final_output/         # 最终结果
        ├── *.png            # 可视化图像
        └── *.json           # 分析结果
```

### 6. 优势

#### 简化性
- 无需管理session状态
- 统一的文件命名规则
- 更简单的文件路径管理

#### 一致性
- 所有同类型文件使用相同文件名
- 新上传文件自动替换旧文件
- 避免文件名冲突和混乱

#### 维护性
- 更容易定位和管理文件
- 减少了代码复杂度
- 便于调试和故障排除

#### 可靠性
- 避免了session丢失的问题
- 文件位置固定且可预测
- 更好的错误处理

### 7. 使用方式

1. **用户上传文件**：自动使用统一命名保存
2. **处理数据**：按固定文件名读取和输出
3. **获取结果**：从固定位置读取结果文件
4. **替换数据**：新上传的同类型文件自动替换旧文件

### 8. 兼容性说明

- 前端代码无需修改（API接口保持一致）
- 现有的处理逻辑完全兼容
- 文件访问路径自动适配

这次更新大大简化了系统架构，提高了可维护性和用户体验，同时保持了所有现有功能的完整性。
