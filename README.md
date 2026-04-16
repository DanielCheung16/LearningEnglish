# 英文单词学习系统

基于**艾宾浩斯遗忘曲线**的个人英文单词学习系统，专为 Computer Engineering 和 Electrical Engineering 领域的词汇学习设计。

## ✨ 核心功能

### 📚 单词管理
- ➕ 添加个人词汇库
- 🏷️ 标记单词领域（计算机、电气工程等）
- 📝 添加专业领域例句和用法
- 🎵 自动获取单词音标和发音
- 🔍 搜索和分类管理

### ✏️ 艾宾浩斯复习系统
- 📊 基于科学的复习间隔算法（1天 → 3天 → 7天 → 15天 → 30天 → 60天）
- 📈 根据掌握程度自动调整复习频率
- 🎯 追踪学习进度和掌握程度
- 💪 渐进式学习，逐步掌握词汇

### 📧 邮件提醒系统
- 🔔 每日自动发送复习提醒
- 📋 邮件中显示待复习单词列表
- ⏰ 可自定义提醒时间
- 🔗 点击邮件链接直接打开复习界面

### 📊 学习统计
- 📈 总词数和掌握情况统计
- 🎯 学习进度可视化
- 📅 复习历史记录
- 🏆 掌握程度分析

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js / 浏览器（前端）

### 安装步骤

1. **克隆或创建项目目录**
   ```bash
   cd english_learning_system
   ```

2. **安装Python依赖**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **启动应用**
   ```bash
   python app.py
   ```

4. **打开浏览器**
   - 访问 `http://localhost:5000`
   - 主页 URL: `http://localhost:5000`

### 项目结构
```
english_learning_system/
├── backend/
│   ├── app.py                      # Flask主应用
│   ├── requirements.txt            # Python依赖
│   ├── modules/
│   │   ├── word_manager.py         # 单词管理
│   │   ├── spaced_repetition.py    # 艾宾浩斯算法
│   │   ├── review_manager.py       # 复习计划
│   │   ├── audio_manager.py        # 音频管理
│   │   ├── email_manager.py        # 邮件系统
│   │   └── scheduler.py            # 任务调度
│   ├── routes/
│   │   ├── word_routes.py          # 单词API
│   │   ├── review_routes.py        # 复习API
│   │   └── config_routes.py        # 配置API
│   └── data/                       # 数据存储
│       ├── words.json              # 单词库
│       ├── review_schedule.json    # 复习计划
│       └── user_config.json        # 用户配置
├── frontend/
│   ├── index.html                  # 主仪表板
│   ├── study.html                  # 添加单词
│   ├── review.html                 # 复习页面
│   ├── settings.html               # 设置页面
│   ├── css/
│   │   └── style.css               # 全局样式
│   └── js/
│       └── api.js                  # API客户端
└── README.md                       # 本文件
```

## 📖 使用指南

### 1️⃣ 添加单词
1. 点击顶部导航 "📚 学习"
2. 输入英文单词
3. 添加中文释义（可多个）
4. 添加专业领域例句
5. 点击 "保存单词"

**示例：**
```
单词: algorithm
释义: 算法 (名词)
例句: The sorting algorithm has O(n log n) complexity.
域: Computer Science
```

### 2️⃣ 开始复习
1. 点击顶部导航 "✏️ 复习"
2. 系统自动加载今日待复习的单词
3. 点击 "🔊 播放发音" 听发音
4. 根据掌握程度选择：
   - **😕 不熟悉** - 需要重新开始
   - **🙂 熟悉** - 按标准间隔复习
   - **😊 练习中** - 拉长复习间隔
   - **🎯 已掌握** - 标记为已掌握

### 3️⃣ 配置邮件提醒
1. 点击顶部导航 "⚙️ 设置"
2. 填入用户名和邮箱
3. 配置SMTP相关信息：
   - **Gmail**: `smtp.gmail.com` (端口: 587)
   - **Outlook**: `smtp-mail.outlook.com` (端口: 587)
   - **QQ邮箱**: `smtp.qq.com` (端口: 465)

#### Gmail设置步骤：
1. 访问 [Google Account](https://myaccount.google.com)
2. 左侧选项 → "安全性"
3. 向下滚动 → "应用专用密码"
4. 选择应用：Mail，设备：Windows（或其他）
5. 生成密码，在设置中粘贴

4. 点击 "🧪 测试邮件配置" 验证
5. 设置提醒时间
6. 启用邮件提醒

## 🧠 艾宾浩斯遗忘曲线原理

### 复习间隔
系统根据科学研究推荐的间隔时间提醒复习：

```
第1次复习: 1天后
第2次复习: 3天后
第3次复习: 7天后
第4次复习: 15天后
第5次复习: 30天后
第6次复习: 60天后
```

### 掌握程度调整
- **不熟悉 (0.5x)**: 重新从第1个间隔开始
- **熟悉 (1.0x)**: 按标准间隔
- **练习中 (1.3x)**: 间隔拉长30%
- **已掌握 (1.5x)**: 间隔拉长50%

### 进度计算
- 掌握程度 = 最近5次复习的平均掌握度
- 当掌握度达到 75% 且连续标记为"练习中"或"已掌握"时，该单词标记为掌握

## 🔌 API文档

### 单词管理
```
POST   /api/words                      # 添加单词
GET    /api/words                      # 获取所有单词
GET    /api/words/<word_id>            # 获取特定单词
PUT    /api/words/<word_id>            # 更新单词
DELETE /api/words/<word_id>            # 删除单词
POST   /api/words/batch-import         # 批量导入
GET    /api/words/search?q=<query>     # 搜索单词
```

### 复习管理
```
GET    /api/review/today               # 今日复习列表
POST   /api/review/submit              # 提交复习结果
GET    /api/review/history/<word_id>   # 复习历史
GET    /api/review/stats               # 复习统计
GET    /api/review/overdue             # 已逾期复习
POST   /api/review/reset/<word_id>     # 重置复习进度
```

### 配置管理
```
GET    /api/config                     # 获取配置
PUT    /api/config                     # 更新配置
POST   /api/config/email-test          # 测试邮件
PUT    /api/config/reminder-time       # 更新提醒时间
PUT    /api/config/reminder-toggle     # 切换提醒
```

## 🌐 系统特色

### 📱 完全本地化
- 所有数据存储在本地JSON文件
- 无需登录，无用户追踪
- 离线可用

### 🔒 隐私保护
- 单词库和学习记录完全私密
- 仅在用户主动配置时才发送邮件
- 不收集任何统计数据

### ⚡ 轻量高效
- 无前端框架依赖，快速加载
- 后端使用Flask，部署简单
- 数据结构清晰，易于二次开发

### 🎯 专业导向
- 重点覆盖IT、电气工程领域词汇
- 包含行业常用例句
- 支持领域分类

## 📈 学习建议

1. **坚持每日复习** - 养成习惯，效果最佳
2. **按照系统提示复习** - 不要跳过复习
3. **认真标记掌握程度** - 准确反馈确保算法有效
4. **添加优质例句** - 了解单词在实际工程中的用法
5. **定期查看进度** - 通过统计看到自己的进步

## 🐛 故障排除

### 启动失败
- 检查Python版本 `python --version` 必须 >= 3.8
- 确保装 `pip install -r backend/requirements.txt`

### 邮件无法发送
- 检查SMTP配置是否正确
- 使用应用专用密码（不是邮箱登录密码）
- 确保邮箱启用了SMTP功能

### 复习数据丢失
- JSON数据文件在 `backend/data/` 文件夹
- 定期备份这个文件夹

## 🔄 后续计划

- ✨ 支持SQLite数据库迁移
- 👥 多用户支持
- 📱 移动应用（iOS/Android）
- ☁️ 云同步功能
- 🤖 AI辅助生成例句释义
- 📚 社区词库分享

## 📝 许可证

MIT License - 自由使用和修改

## 🤝 贡献

欢迎提交issue和pull request改进这个项目！

---

**开始你的英文学习之旅吧！** 🚀
