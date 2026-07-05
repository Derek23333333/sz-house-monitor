# B端思维·进阶工作台

帮助 ToB 方向高级业务分析师（BA+产品+PM 复合岗）通过每日 5 分钟被动阅读 + 一键互动，从"高级"迈向"资深"。

## 功能模块

| 模块 | 说明 |
|------|------|
| 📰 每日视野 | 每日 3-5 条 ToB 行业资讯 + AI 启发规则引擎自动生成核心启发，支持 👍👎 反馈 |
| 🔧 ToB 武器库 | 60+ 条思维框架（沟通话术、分析框架、检查清单、反常识观点），每日随机推送，支持自定义新增 |
| 📖 每日一课 | 50 个思维模型 + 80 条 B 端专业常识，单日推模型（含今日小行动）、双日推常识（含真实案例） |
| 🔥 灵感火花 | 30+ 条跨界启发（历史/军事/艺术/生物/哲学），底部一键随机获取 |

## 快速部署到 GitHub Pages

### 1. 创建 GitHub 仓库

在 GitHub 上创建一个**公开**仓库（建议命名：`btoa-workbench`）。

### 2. 上传文件

将本文件夹内所有文件上传到仓库根目录，结构如下：

```
/
├── index.html                  ← 导航页，点击进入工作台
├── btoa-workbench.html         ← 主工作台（核心页面）
├── fetch_news.py
├── requirements.txt
├── .github/workflows/
│   └── update_news.yml
└── README.md
```

### 3. 启用 GitHub Pages

1. 进入仓库 **Settings → Pages**
2. **Source** 选择 **Deploy from a branch**
3. **Branch** 选择 `main`（或你的默认分支），目录选择 `/ (root)`
4. 点击 **Save**

等待 1-2 分钟，页面地址会显示在 Settings → Pages 页面顶部（格式：`https://你的用户名.github.io/仓库名/`）

### 4. 首次手动触发数据更新

部署后 `data.json` 还不存在。手动触发 GitHub Actions 生成初始数据：

1. 进入仓库 **Actions** 标签页
2. 左侧选择 **"更新 ToB 行业资讯"**
3. 点击 **Run workflow** → **Run workflow**

等待运行完成（约 1-2 分钟），`data.json` 会自动生成并推送回仓库。

### 5. 访问

打开浏览器访问 `https://你的用户名.github.io/仓库名/`，进入导航页后点击「进入工作台」使用 `btoa-workbench.html`。

## 自动更新机制

GitHub Actions 会在每日**北京时间 8:00** 自动运行，从以下数据源抓取最新资讯：

- 牛透社（SaaS/ToB 垂直媒体）
- 36氪企服频道
- IDC圈云头条
- InfoQ 中文站

如需手动更新，可在 Actions 页面点击 **Run workflow**。

## 技术说明

- 纯前端实现，无后端依赖
- 所有 CSS/JS 内嵌在 `btoa-workbench.html` 中，无外部 CDN 依赖
- 用户数据（反馈、打卡记录、自定义内容）存储在浏览器 localStorage
- `data.json` 首次由 GitHub Actions 运行后生成

## 设计风格

紫黑风 — 深邃、沉静、高级感，移动端优先（375px 基准），PC 自适应。
