# English Learning System

一个本地运行的英语单词学习系统，支持：

- 单词录入与管理
- 自动补全音标、英文释义、英文例句、发音
- 基于 `FSRS-lite` 思路的复习调度
- 邮件提醒
- CSV 批量导入
- 手机通过局域网或 Tailscale 访问

当前项目适合个人自用，数据默认保存在本地 JSON 文件中。

## 功能概览

### 1. 单词管理
- 支持网页手动添加单词
- 支持删除单词
- 支持 CSV 批量导入
- 重复添加同一个词时，不会新建重复记录
- 如果重复添加已有单词，会：
  - 补齐该词缺失的信息
  - 下调复习掌握度
  - 提前下一次复习时间

### 2. 自动词典补全
- 使用 `Free Dictionary API`
- 可自动补全：
  - 音标
  - 英文释义
  - 英文例句
  - 发音音频

说明：
- 该 API 主要提供英文内容，不提供稳定的中文释义
- 页面里的自动补全更准确地说是英文 definitions，而不是中文 translation

### 3. 发音
- 优先使用 `Free Dictionary API` 返回的音频
- 如果失败，再回退到浏览器语音能力
- 手机端也已适配优先真实音频播放

### 4. 复习调度
- 当前使用的是 `FSRS-lite`
- 不是官方完整 FSRS 复刻版
- 但已经引入现代记忆调度的核心状态：
  - `stability`
  - `difficulty`
  - `retrievability`
  - `lapses`
  - `state`

当前引导复习间隔为：

```text
3小时 -> 5小时 -> 1天 -> 3天 -> 7天 -> 15天 -> 30天 -> 60天
```

复习结果会影响后续调度：
- `unfamiliar`：明显降低稳定性，提高难度，增加 lapse
- `familiar`：正常增长
- `practiced`：更强的正向增长
- `mastered`：更长的后续间隔

如果一个词反复失败过多次，会进入 `leech` 状态。

### 5. 邮件提醒
- 邮件提醒和复习算法是两层逻辑
- 算法负责计算 `next_review_date`
- 邮件系统负责在程序运行时检查哪些词到期并发送提醒

注意：
- 程序关闭后，不会发送邮件
- 这是本地运行提醒，不是云端托管提醒

## 快速开始

### 环境要求
- Python 3.8+

### 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 启动项目

在项目根目录运行：

```bash
python run.py
```

启动后访问：

- 主页：`http://localhost:5000`
- 学习页：`http://localhost:5000/study`
- 复习页：`http://localhost:5000/review`
- 设置页：`http://localhost:5000/settings`

## 目录结构

```text
English_learning/
├─ backend/
│  ├─ app.py
│  ├─ requirements.txt
│  ├─ data/
│  │  ├─ words.json
│  │  ├─ review_schedule.json
│  │  └─ user_config.json
│  ├─ modules/
│  │  ├─ audio_manager.py
│  │  ├─ dictionary_manager.py
│  │  ├─ email_manager.py
│  │  ├─ review_manager.py
│  │  ├─ scheduler.py
│  │  ├─ spaced_repetition.py
│  │  └─ word_manager.py
│  └─ routes/
│     ├─ config_routes.py
│     ├─ review_routes.py
│     └─ word_routes.py
├─ frontend/
│  ├─ index.html
│  ├─ review.html
│  ├─ settings.html
│  ├─ study.html
│  ├─ css/
│  └─ js/
└─ run.py
```

## 使用说明

### 手动添加单词
进入 `/study` 页面后：

1. 输入 `word`
2. `phonetic` 可留空，系统会尝试自动补
3. `Definitions` 可留空，系统会尝试从词典 API 拉取
4. `Examples` 可留空，系统会尝试拉取英文例句
5. 点击 `Save Word`

### 复习
进入 `/review` 页面后：

- 页面只显示“当前已经到复习时间的词”
- 不会显示所有词
- 复习按钮：
  - `Unfamiliar`
  - `Familiar`
  - `Practiced`
  - `Mastered`

### 删除单词
在 `/study` 页面最近单词列表里可以删除单词。

删除时会同时删除：
- 单词记录
- 对应的复习记录
- 该词的掌握度、复习历史、下次复习时间

### CSV 批量导入
在 `/study` 页的 `Batch Import` 区域使用。

支持：
- 上传 `.csv`
- 下载模板 `word_import_template.csv`

支持列：

```text
word, phonetic, meaning, part_of_speech, example_sentence, example_translation, domain
```

最少只需要：

```text
word
```

`domain` 当前固定为以下 4 类：

- `Hardware`
- `Terminology`
- `Daliy`
- `Others`

模板示例：

```csv
word,phonetic,meaning,part_of_speech,example_sentence,example_translation,domain
algorithm,,算法,noun,This algorithm is efficient.,这个算法很高效。,Terminology
voltage,,电压,noun,The voltage is too high.,电压太高了。,Hardware
database,,数据库,noun,The database stores user records.,数据库存储用户记录。,Terminology
```

### CSV 中文说明
如果你用 Excel 导入中文 CSV：

- 页面会优先尝试 `UTF-8`
- 也会兼容 `gb18030`
- 模板下载时已经带了 `UTF-8 BOM`

建议做法：

1. 先下载模板
2. 用 Excel 打开
3. 填写内容
4. 保存为 CSV
5. 再导入

## 网络访问

### 同一台电脑
直接访问：

```text
http://localhost:5000
```

### 手机局域网访问
使用运行程序那台设备的局域网 IP：

```text
http://<LAN-IP>:5000
```

### Tailscale 访问
如果电脑和手机都加入同一个 tailnet，可以直接访问：

```text
http://<Tailscale-IP>:5000
```

说明：
- 不需要同一个 Wi-Fi
- 但电脑要开机，程序要在运行
- 浏览器可能提示 “不安全”，因为这里是 HTTP，不是 HTTPS

## 主要 API

### 单词

```text
POST   /api/words
GET    /api/words
GET    /api/words/<word_id>
PUT    /api/words/<word_id>
DELETE /api/words/<word_id>
POST   /api/words/batch-import
GET    /api/words/search?q=<query>
POST   /api/words/audio-info
POST   /api/words/audio-verify
```

### 复习

```text
GET    /api/review/today
POST   /api/review/submit
GET    /api/review/history/<word_id>
GET    /api/review/stats
GET    /api/review/overdue
POST   /api/review/reset/<word_id>
GET    /api/review/by-date?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

### 配置

```text
GET    /api/config
PUT    /api/config
POST   /api/config/email-test
PUT    /api/config/reminder-time
PUT    /api/config/reminder-toggle
```

## 当前实现边界

### 1. 不是官方完整 FSRS
当前是 `FSRS-lite`，目标是：
- 可运行
- 结构正确
- 比固定倍率更合理

但它不是：
- 官方 FSRS 参数训练版
- 与 Anki 完全一致的实现

### 2. Free Dictionary API 不提供稳定中文
所以自动补全主要是：
- 英文释义
- 英文例句
- 音标
- 音频

中文释义如果需要高质量自动翻译，需要后续再接翻译 API。

### 3. 邮件提醒依赖本地程序运行
如果本地程序退出、电脑休眠或关机：
- 不会发邮件
- 不会自动补发错过的提醒

## 常见问题

### 为什么 `/review` 里看不到所有单词？
因为 `/review` 只显示已经到复习时间的词，不显示全部词。

### 为什么重复添加同一个词没有新增一条？
这是当前的设计。重复添加时会：
- 命中已有词
- 降低掌握度
- 提前下一次复习

### 删除单词会不会连掌握度一起删？
会。删除单词时会一起删除它的复习记录和掌握度。

### 为什么程序关掉后不发邮件？
因为调度器就在本地 Flask 进程里。程序不运行，提醒任务就不会执行。

## 后续可以继续做的方向

- 引入真正的翻译 API，补中文释义/中文例句
- 把 FSRS-lite 进一步升级为更接近官方 FSRS 的版本
- 增加 leech 可视化提示
- 增加复习状态展示，例如 stability / difficulty / lapses
- 迁移到 SQLite
- 部署到线上服务
