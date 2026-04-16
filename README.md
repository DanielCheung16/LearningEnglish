# English Learning System

一个本地运行的英语单词学习系统，支持：

- 添加、删除单词
- 自动补全音标、英文释义、英文例句、发音
- `FSRS-lite` 复习调度
- 邮件提醒
- CSV 批量导入
- 手机通过局域网或 Tailscale 访问

## 快速开始

### 1. 安装依赖

在项目根目录运行：

```bash
pip install -r backend/requirements.txt
```

### 2. 启动项目

```bash
python run.py
```

然后打开：

- `http://localhost:5000`
- 学习页：`/study`
- 复习页：`/review`
- 设置页：`/settings`

如果你是第一次从 GitHub 拉取这个项目，建议先初始化本地空数据：

```bash
make setup
```

如果你的环境没有 `make`，也可以直接运行：

```bash
pip install -r backend/requirements.txt
python scripts/init_data.py
python run.py
```

## 第一次使用

建议按这个顺序：

1. 打开 `/study`
2. 添加 1 到 2 个单词
3. 测试自动补音标、释义、发音
4. 打开 `/review` 看复习队列
5. 最后再决定要不要配置邮件提醒

说明：
- 邮件提醒不是必须先配置
- 数据默认保存在本地 JSON 文件

## 复习逻辑

当前系统使用 `FSRS-lite`，不是官方完整 FSRS，但已经采用更现代的记忆状态模型。

当前引导间隔：

```text
3小时 -> 5小时 -> 1天 -> 3天 -> 7天 -> 15天 -> 30天 -> 60天
```

`/review` 页面只显示“当前已经到复习时间的词”，不会显示全部单词。

如果重复添加同一个词：
- 不会创建重复记录
- 会命中已有单词
- 会降低掌握度并提前下一次复习

## 发音与词典

系统使用 `Free Dictionary API`：

- 自动补音标
- 自动补英文释义
- 自动补英文例句
- 优先使用词典返回的音频发音

注意：
- 这个 API 主要提供英文内容，不稳定提供中文释义

## CSV 导入

在 `/study` 页面使用 `Batch Import`。

支持列：

```text
word, phonetic, meaning, part_of_speech, example_sentence, example_translation, domain
```

最少只需要：

```text
word
```

`domain` 当前固定为：

- `Hardware`
- `Terminology`
- `Daliy`
- `Others`

建议先下载页面里的 `CSV Template`，用 Excel 填写后再导入。

## 数据位置

本地数据默认保存在：

- `backend/data/words.json`
- `backend/data/review_schedule.json`
- `backend/data/user_config.json`

删除这些文件会丢失对应数据。

## 手机访问

### 同一局域网

用运行程序那台电脑的局域网 IP：

```text
http://<LAN-IP>:5000
```

### Tailscale

如果手机和电脑都在同一个 tailnet：

```text
http://<Tailscale-IP>:5000
```

前提：
- 电脑开着
- 程序正在运行

## 邮件提醒

邮件提醒依赖本地程序运行：

- 程序开着：可以发
- 程序关了：不会发

如果要使用邮件提醒，在 `/settings` 中配置 SMTP 即可。

## 主要接口

### 单词

```text
POST   /api/words
GET    /api/words
DELETE /api/words/<word_id>
POST   /api/words/batch-import
POST   /api/words/audio-info
POST   /api/words/audio-verify
```

### 复习

```text
GET    /api/review/today
POST   /api/review/submit
GET    /api/review/history/<word_id>
GET    /api/review/stats
POST   /api/review/reset/<word_id>
```

## 常见问题

### 页面打不开
- 确认已经运行 `python run.py`
- 确认访问的是 `http://localhost:5000`

### 手机打不开
- 不要访问手机自己的 `localhost`
- 要用电脑的局域网 IP 或 Tailscale IP

### 删除单词会不会删除掌握度
会。删除单词时会同时删除它对应的复习记录和掌握度。
