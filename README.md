# 🧻 vibe-napkin

> **You mouth the code, we wipe the crumbs.**  
> 你负责用嘴编代码，我负责帮你擦嘴。

**vibe coding 软件工程管理工具** — 协助 vibe coder 保质保量完成商业级项目开发。

传统瀑布流：PRD → 设计 → 代码（PRD 是输入）  
**vibe-napkin**：代码 → 业务单元 → 知识库 → PRD（PRD 是输出）

---

## 📦 安装

```bash
pip install vibe-napkin
```

需要 [zvec](https://github.com/) 做向量知识库：

```bash
pip install zvec
```

---

## 🎮 六大命令

| 命令 | 动作 | 说明 |
|:-----|:-----|:------|
| `vibe-napkin init` | ⛺ 支桌子 | 初始化环境 + 模板底座 |
| `vibe-napkin wipe` | 🧻 擦嘴 | 扫描变更 + 自动校验 + 同步文档 |
| `vibe-napkin tidy` | 🗑️ 收拾桌子 | 锁检测 → 更新向量知识库 |
| `vibe-napkin save` | 💾 存档 | 保存进度快照 |
| `vibe-napkin load` | 📂 读档 | 恢复存档继续开发 |
| `vibe-napkin list` | 📋 清单 | 查看所有存档 |

---

## 🚀 快速开始

```bash
# 1. 在项目目录初始化
cd my-project
vibe-napkin init

# 2. 编写业务单元文档
#    → docs/业务单元/001-你的功能.md

# 3. 功能开发完，验收后
vibe-napkin wipe          # 同步文档
vibe-napkin tidy          # 更新知识库
vibe-napkin save -l "商品采集完成"  # 存档

# 4. 下次继续
vibe-napkin load 2026-06-29-001-商品采集完成
```

---

## 💡 工作流程

```mermaid
graph LR
    A[开发功能] --> B[验收]
    B --> C[vibe-napkin wipe]
    C --> D[vibe-napkin tidy]
    D --> E[vibe-napkin save]
    E --> F[下一关]
    F -.->|下次 load 继续| A
```

---

## 📁 项目骨架

```
my-project/
├── .napkin/
│   ├── config.toml           # 配置（embedding模型、zvec路径、MCP端口）
│   ├── checkpoints/           # 存档（游戏存档式 JSON）
│   └── file_hashes.json       # 变更检测缓存
├── docs/
│   ├── README.md
│   ├── 业务单元/              # 纵向贯穿文档（产品+技术+部署+数据库）
│   │   ├── README.md          # 6段式模板规范
│   │   └── _template.md       # 空模板
│   └── 约束基线/              # 项目约束模板（用户自填）
│       ├── README.md
│       ├── _baseline-技术约束.md
│       ├── _baseline-部署约束.md
│       └── _baseline-产品约束.md
```

---

## 🧠 业务单元模板

每个功能点 ≤ 200 行，纵向贯穿"产品 + 技术 + 部署 + 数据库"。

```markdown
# [业务名称]

## 关键词
英文,中文,俄文 逗号分隔，用于向量库召回匹配

## 业务规则
- 规则 1（一句话说明核心逻辑）

## 代码位置
- 函数/类名：`路径::符号` 行号

## 关联业务单元
- [相关单元名](./关联单元.md)

## 历史决策（近 3 次）
- YYYY-MM-DD（commit hash）：决策内容，原因

## 变更触发器
- 什么情况下需要回来改这里
```

---

## ⚠️ 使用须知

1. **功能开发完** → 充分验收后再 `wipe`。开发者自己负责功能质量
2. `wipe` 自动校验格式，阻断级错误直接拦截，小问题自动修复
3. `tidy` 前请关闭 AI 侧的 MCP 知识库连接，避免死锁冲突
4. `tidy` 完成后重新连接 MCP，知识库已更新
5. 版本回退请使用 git，vibe-napkin 不管理版本

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| CLI 框架 | Python + Typer |
| 配置管理 | TOML (tomlkit) |
| 终端渲染 | Rich |
| 变更检测 | git status / 文件 hash |
| 向量知识库 | zvec |
| MCP 管理 | 端口检测 + 锁协议 |
| 发布 | PyPI |

---

## 📄 License

MIT