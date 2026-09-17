# GitHub Unfollower Checker 🔍

找出 GitHub 上**取关了你、但你还在关注他们**的用户。支持**一键回关**和**一键取关**。

零外部依赖，仅使用 Python 标准库。

## ✨ 功能

- 📡 自动获取 followers 和 following 列表（支持分页）
- 🔴 列出**取关你的人**（你关注了他们，但他们没关注你）
- 🔵 列出**关注你但你没回关的人**（粉丝）
- 🟢 列出**互相关注**的用户
- 🔁 **一键回关**所有粉丝
- 🚫 **一键取关**所有 unfollowers
- ⚡ 自动检测 API 速率限制并保护
- 🎨 彩色终端表格输出
- 🚫 零外部依赖，仅使用 Python 标准库

## 📋 前提条件

- Python 3.10+
- GitHub Personal Access Token（需要 `user:follow` 权限才能使用关注/取关功能）

## 🚀 快速开始

### 1. 配置 Token

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 GitHub Personal Access Token：

```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**获取 Token：**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 `user:follow` 权限（关注/取关必须）
4. 生成后复制 token 填入 `.env`

### 2. 运行

```bash
# 查看对比结果
python main.py

# 一键回关所有粉丝
python main.py --follow-back

# 一键取关所有 unfollowers
python main.py --unfollow

# 同时回关 + 取关
python main.py --follow-back --unfollow

# 跳过确认提示（危险操作！）
python main.py --unfollow -y

# 指定用户名
python main.py -u <username>
```

## 📖 命令行参数

| 参数 | 说明 |
|------|------|
| `-u`, `--username` | 指定要查询的 GitHub 用户名（默认使用 token 对应的用户） |
| `--follow-back` | 🔁 一键回关所有粉丝（关注你但你没回关的人） |
| `--unfollow` | 🚫 一键取关所有 unfollowers（你关注了但没关注你的人） |
| `-y`, `--yes` | 跳过确认提示，直接执行批量操作 |
| `--no-mutual` | 不显示互相关注的用户列表 |
| `--no-fans` | 不显示关注你但你没回关的用户列表 |

## 📊 输出示例

```
╭────────────── 📈 GitHub Follow Report ──────────────╮
│ 👤 User: @yourname                                  │
│ 📊 Followers: 42                                    │
│ 📊 Following: 100                                   │
│                                                     │
│ 🔴 Unfollowers: 15                                  │
│ 🟢 Mutual follows: 27                               │
│ 🔵 Fans: 15                                         │
╰─────────────────────────────────────────────────────╯

🔴 Unfollowers - 你关注了他们，但他们没关注你 (15)
  #  Username   Profile URL
  ─  ─────────  ──────────────────────────────
  1  @user1     https://github.com/user1
  2  @user2     https://github.com/user2
  ...
```

执行 `--follow-back` 或 `--unfollow` 时：

```
📋 即将取关 15 个 unfollowers:
     @user1
     @user2
     ...

  确认取关以上 15 个用户？ [y/N]: y

🚀 开始批量取关 15 个用户...

  ✅ [1/15] @user1
  ✅ [2/15] @user2
  ...

╭──────────────────────────────────────────╮
│ 取关完成！                                │
│   成功: 15                               │
╰──────────────────────────────────────────╯
```

## ⚠️ 注意事项

- GitHub API 对认证用户限制 **5000 次请求/小时**
- 每次关注/取关操作间隔 0.5 秒，避免触发速率限制
- **一键取关是不可逆操作**，请确认后执行（默认会要求确认）
- Token 请妥善保管，不要提交到 Git（已在 `.gitignore` 中排除）
- 使用 `--follow-back` / `--unfollow` 需要 Token 有 `user:follow` 权限

## 📁 项目结构

```
github-follower-diff/
├── main.py            # 主程序（单文件，包含所有代码）
├── .env.example       # 环境变量模板
├── .env               # 你的配置（不要提交到 Git）
├── .gitignore
└── README.md
```

## 🛠️ 技术实现

- **HTTP 请求**：Python 标准库 `urllib`
- **关注/取关**：GitHub REST API `PUT/DELETE /user/following/{username}`
- **JSON 解析**：标准库 `json`
- **终端输出**：ANSI 颜色码
- **配置管理**：自定义 `.env` 解析器
- **分页处理**：自动遍历所有分页（每页 100 条）
- **对比逻辑**：Python 集合运算

## 📝 License

MIT
