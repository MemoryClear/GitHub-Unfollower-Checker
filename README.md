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
- 🤍 **白名单**：允许特定用户保持单向关注，不出现在 Unfollowers 列表，也不会被回关/取关
- 🚫 **黑名单**：一键取关的用户自动拉黑，以后一键回关不会再回关他们（防止被"骗关注"）
- 🤖 **GitHub Actions 定时自动运行**（每天一次，自动回关 + 取关）
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

### 3. 白名单（可选）

有几个用户是你**单方面关注**、不想被列进 "Unfollowers" 也不想被取关/回关的？把它们加入白名单。

仓库里已经有一份 `whitelist.txt`，直接用编辑器打开往里加就行，一行一个用户名（可带 `@`，`#` 为注释）：

> ⚠️ **`whitelist.txt` 是被 git 跟踪的，不要加进 `.gitignore`。** GitHub Actions 的 runner 是全新 checkout，只能看到仓库里有的文件；白名单如果不进仓库，CI 上会**静默失效**（`main.py` 只在显式传 `--whitelist` 时才警告文件不存在），名单里的人会被每日任务取关**并永久拉黑**。加完记得 commit + push，CI 才会拿到。

```
some-friend
@another-user   # 允许我对他单向关注
```

程序会自动读取脚本目录下的 `whitelist.txt`。白名单中的用户：

- 不出现在 **Unfollowers** 和 **Fans** 列表中
- 不会被 `--follow-back` 回关，也不会被 `--unfollow` 取关

临时白名单（不写文件）：

```bash
# 可重复使用 --exclude-user
python main.py --unfollow --exclude-user some-friend --exclude-user another-user
```

自定义白名单文件路径：

```bash
python main.py --whitelist path/to/whitelist.txt
```

### 4. 黑名单（防"骗关注"）

有些用户先关注你、骗到你回关后又取关你。运行 `--unfollow` 时，**取关成功的用户会自动写入 `blacklist.txt`**（首次运行自动创建，带日期注释、自动去重）：

```
stranger  # 2026-09-20 取关后自动加入
```

之后即使这个人再来关注你：

- 不出现在 **Fans** 列表
- `--follow-back` **不会**回关他

相关控制：

```bash
# 取关但不写入黑名单
python main.py --unfollow --no-blacklist

# 手动编辑黑名单恢复某人（删除或注释对应行即可）
# 自定义黑名单路径
python main.py --follow-back --blacklist path/to/blacklist.txt
```

也可以不经过取关、直接手动编辑 `blacklist.txt`（格式同白名单）来永久屏蔽某人。

## 📖 命令行参数

| 参数 | 说明 |
|------|------|
| `-u`, `--username` | 指定要查询的 GitHub 用户名（默认使用 token 对应的用户） |
| `--follow-back` | 🔁 一键回关所有粉丝（关注你但你没回关的人） |
| `--unfollow` | 🚫 一键取关所有 unfollowers（你关注了但没关注你的人） |
| `-y`, `--yes` | 跳过确认提示，直接执行批量操作 |
| `--no-mutual` | 不显示互相关注的用户列表 |
| `--no-fans` | 不显示关注你但你没回关的用户列表 |
| `--whitelist FILE` | 🤍 指定白名单文件路径（默认读取脚本目录下的 `whitelist.txt`） |
| `--exclude-user USERNAME` | 🤍 临时将某个用户加入白名单，可重复使用 |
| `--blacklist FILE` | 🚫 指定黑名单文件路径（默认读取脚本目录下的 `blacklist.txt`） |
| `--no-blacklist` | 🚫 `--unfollow` 时不自动把取关用户写入黑名单 |

只要环境变量 `NO_COLOR` 非空，输出就会禁用 ANSI 颜色（[no-color.org](https://no-color.org/) 规范），适合写日志或重定向到文件。

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

## 🤖 自动运行（GitHub Actions）

不想每天手动跑？仓库里带了 `.github/workflows/follow-sync.yml`，每个**每天 UTC 08:23**（北京时间 16:23）自动执行 `--follow-back --unfollow`，并把更新后的 `blacklist.txt` 提交回仓库。

### 配置步骤

**1. 创建 Personal Access Token**

> ⚠️ 不能用 Actions 自动注入的 `GITHUB_TOKEN` —— 它只有仓库级权限，没有 `user:follow`，调关注接口会返回 403。

二选一：

- **Classic token**：https://github.com/settings/tokens → Generate new token (classic) → 勾选 `user:follow`
- **Fine-grained token**：https://github.com/settings/personal-access-tokens → 在 **Account permissions** 里找到 **Followers**，设为 **Read and write**

**2. 存为仓库 secret**

仓库 → Settings → Secrets and variables → Actions → New repository secret，名字必须是 **`GH_FOLLOW_TOKEN`**（workflow 里按这个名字引用）。

**3. 关于 workflow 写权限（一般不用改）**

workflow 里已经声明了 `permissions: contents: write`，正常情况下这就够了——仓库的 Workflow permissions 设置是**默认值**，workflow 里的 `permissions` 键可以按需提权，这也是 GitHub 推荐的最小权限做法。

但如果提交黑名单时 `git push` 报 403，按顺序排查：
1. 看 job 日志开头的 `GITHUB_TOKEN Permissions` 块，确认 `contents` 是不是 `write`
2. 如果组织策略强制只读，仓库级设置改不动 → 回到 Settings → Actions → General → Workflow permissions 选 **"Read and write permissions"**
3. fork PR 触发的运行会被强制只读，但本 workflow 走 `schedule` / `workflow_dispatch`，不受影响

### 使用

配置好后，去 Actions → **Follow Sync** → Run workflow，可以先勾上 `dry_run` 试跑一次：

- **勾选 `dry_run`**：只抓取并打印报告，不执行任何关注/取关。用来验证 token 是否有效、权限是否够。
- **不勾**：全自动执行回关 + 取关（等价于本地 `python main.py --follow-back --unfollow -y`）。

跑完的结果会写进 job 的 **Summary** 页，不用翻日志就能看。日志里也不带颜色（workflow 设了 `NO_COLOR=1`）。

> ⚠️ **`-y` 千万不能省。** `confirm()` 会捕获 `EOFError` 返回 `False`（`main.py:365-367`），所以 CI 里漏了 `-y` **不会报错**，而是「workflow 绿色通过、但一个关注/取关都没执行」——比崩溃更难发现。

### 定时任务的现实约束

1. **cron 用 UTC 时间**，且 GitHub 允许的最小间隔是 5 分钟
2. **不保证准点**：GitHub 负载高时，定时任务可能延迟几十分钟才触发
3. **60 天无活动会被自动禁用**：公开仓库的 scheduled workflow 在仓库连续 60 天没有任何活动后会被自动停用，需要去 Actions 页面手动重新启用
   - 这里有个联动：本 workflow 只在黑名单**有变化**时才产生 commit。如果你 60 天内没被任何人取关，就没有提交、没有活动，可能触发这条自动禁用。届时 GitHub 会发邮件，去 Actions 页面点一下重新启用即可。

另外，全自动模式的风控风险请见下方「注意事项」。

## ⚠️ 注意事项

- GitHub API 对认证用户限制 **5000 次请求/小时**
- 每次关注/取关操作间隔 0.5 秒，避免触发速率限制
- **一键取关是不可逆操作**，请确认后执行（默认会要求确认）
- Token 请妥善保管，不要提交到 Git（`.env` 已在 `.gitignore` 中排除）
- 使用 `--follow-back` / `--unfollow` 需要 Token 有 `user:follow` 权限
- **⚠️ 风控风险**：GitHub 的 [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies) 将 "following/unfollowing in bulk" 的自动化活动列为 spam 行为。手动偶尔跑一次属于个人工具范畴；挂上每日定时、无人值守地批量回关/取关，在风控视角里性质不同，存在账号被限流或封禁的可能。`--follow-back`（自动回关所有粉丝）尤其容易触发。
- `blacklist.txt` 会被自动提交回仓库，因此它的内容是**公开可见**的（如果仓库是 public）
- **⚠️ Actions 条款风险**：GitHub 的 [Additional Product Terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features) 规定，GitHub 托管 runner 不得用于「与仓库所属软件项目的生产、测试、部署或发布无关的任何其他活动」。把关注管理机器人挂在 Actions 上跑属于灰色地带。想彻底规避可以改用 VPS + cron/systemd timer。
- **误伤不可逆**：`--unfollow` 会取关**所有**没回关你的人，而黑名单是**永久**的。GitHub 的 follower 列表有缓存，某人账号被临时限制或短暂取关再回关，都可能让他掉出 `followers` → 被你取关并永久拉黑 → 即使他回关你也不会再被回关。建议定期看一眼黑名单文件，或改用 `--no-blacklist`。

## 📁 项目结构

```
github-follower-diff/
├── main.py                          # 主程序（单文件，包含所有代码）
├── .github/workflows/follow-sync.yml  # 定时自动执行（每天一次）
├── .env.example                     # 环境变量模板
├── .env                             # 你的配置（不要提交到 Git）
├── whitelist.txt.example            # 白名单模板
├── whitelist.txt                    # 你的白名单（进 Git，否则 CI 上会静默失效）
├── blacklist.txt.example            # 黑名单模板
├── blacklist.txt                    # 黑名单（--unfollow 自动追加；Actions 会提交回仓库）
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
