#!/usr/bin/env python3
"""
GitHub Unfollower Checker
=========================
找出 GitHub 上取关了你、但你还在关注他们的人。
支持一键回关粉丝、一键取关 unfollowers。

用法:
    python main.py                       # 查看对比结果
    python main.py --follow-back         # 一键回关所有粉丝
    python main.py --unfollow            # 一键取关所有 unfollowers
    python main.py -u <username>         # 查看指定用户
    python main.py --exclude-user octocat  # 临时把某用户加入白名单

白名单: 在脚本目录下的 whitelist.txt 中一行写一个用户名，
这些用户不会出现在 Unfollowers/Fans 列表中，也不会被一键回关/一键取关处理。

在 .env 文件中设置 GITHUB_TOKEN，或直接设置环境变量。
零外部依赖，仅使用 Python 标准库。
"""

import json
import os
import sys
import time
import argparse
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path


# ─── ANSI Colors ──────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD_RED = f"{BOLD}{RED}"
BOLD_GREEN = f"{BOLD}{GREEN}"
BOLD_BLUE = f"{BOLD}{BLUE}"
BOLD_CYAN = f"{BOLD}{CYAN}"
BOLD_YELLOW = f"{BOLD}{YELLOW}"

if os.environ.get("NO_COLOR") or sys.platform == "win32":
    try:
        os.system("")  # Enable VT processing on Windows 10+
    except Exception:
        pass


# ─── .env Loader ──────────────────────────────────────────────────────────────

def load_dotenv(env_path: Path):
    """Load key=value pairs from a .env file into os.environ."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ.setdefault(key, value)


# ─── Whitelist ────────────────────────────────────────────────────────────────

def whitelist_key(login: str) -> str:
    """白名单匹配键：去掉 @ 前缀并转小写（GitHub 用户名不区分大小写）。"""
    return login.lstrip("@").lower()


def load_whitelist(whitelist_path: Path, extra_users: list[str] | None = None) -> set[str]:
    """
    读取白名单用户名集合（全部转小写，GitHub 用户名不区分大小写）。
    文件格式：一行一个用户名，可带 @ 前缀，# 开头或行中 # 之后为注释。
    extra_users: 通过 --exclude-user 传入的临时白名单。
    """
    names: set[str] = set()

    if whitelist_path.exists():
        for line in whitelist_path.read_text(encoding="utf-8").splitlines():
            name = line.split("#", 1)[0].strip()
            if name:
                names.add(whitelist_key(name))

    for user in extra_users or []:
        name = user.strip()
        if name:
            names.add(whitelist_key(name))

    return names


# ─── GitHub API ───────────────────────────────────────────────────────────────

class GitHubAPI:
    """GitHub API client with pagination, rate limit handling, and follow/unfollow."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str):
        self.token = token

    def _request(self, url: str, method: str = "GET") -> tuple:
        """
        Make an API request. Returns (data, response_headers).
        data is None for 204 No Content responses.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
            "User-Agent": "github-unfollower-checker",
        }
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_headers = dict(resp.headers)
                status = resp.status
                if status == 204:
                    return None, resp_headers
                body = resp.read().decode("utf-8")
                data = json.loads(body) if body else None
                return data, resp_headers
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                msg = json.loads(body).get("message", body)
            except Exception:
                msg = body
            raise RuntimeError(f"GitHub API error {e.code}: {msg}")

    def _check_rate_limit(self, headers: dict):
        remaining = int(headers.get("X-RateLimit-Remaining", -1))
        if 0 <= remaining < 10:
            reset_time = int(headers.get("X-RateLimit-Reset", 0))
            wait_seconds = max(0, reset_time - int(time.time()))
            print(f"  ⚠️  Rate limit warning: {remaining} requests remaining. "
                  f"Resets in {wait_seconds}s.")
            if remaining == 0:
                print(f"  ⏳ Rate limit exceeded. Waiting {wait_seconds + 1}s...")
                time.sleep(wait_seconds + 1)

    def _fetch_all_pages(self, endpoint: str) -> list[dict]:
        """Fetch all pages from a paginated GET endpoint."""
        results = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.BASE_URL}{endpoint}?page={page}&per_page={per_page}"
            data, headers = self._request(url, "GET")
            self._check_rate_limit(headers)

            if not data:
                break

            results.extend(data)
            page += 1

            if len(data) < per_page:
                break

        return results

    def get_authenticated_user(self) -> str:
        data, _ = self._request(f"{self.BASE_URL}/user")
        return data["login"]

    def get_followers(self, username: str) -> list[dict]:
        return self._fetch_all_pages(f"/users/{username}/followers")

    def get_following(self, username: str) -> list[dict]:
        return self._fetch_all_pages(f"/users/{username}/following")

    def follow_user(self, username: str) -> bool:
        """Follow a user. Returns True on success."""
        try:
            self._request(f"{self.BASE_URL}/user/following/{username}", "PUT")
            return True
        except RuntimeError as e:
            print(f"    ❌ Failed to follow @{username}: {e}")
            return False

    def unfollow_user(self, username: str) -> bool:
        """Unfollow a user. Returns True on success."""
        try:
            self._request(f"{self.BASE_URL}/user/following/{username}", "DELETE")
            return True
        except RuntimeError as e:
            print(f"    ❌ Failed to unfollow @{username}: {e}")
            return False


# ─── Comparator ───────────────────────────────────────────────────────────────

@dataclass
class ComparisonResult:
    username: str
    followers: list[dict]
    following: list[dict]
    unfollowers: list[dict]   # 你关注了但没关注你的人（已剔除白名单）
    mutual: list[dict]        # 互相关注
    fans: list[dict]          # 关注你但你没回关的人（已剔除白名单）
    whitelisted_hidden: list[dict] = field(default_factory=list)  # 被白名单隐藏的用户


def compare(followers: list[dict], following: list[dict], username: str) -> ComparisonResult:
    """对比 followers 和 following，算出三类用户。"""
    follower_ids = {u["id"] for u in followers}
    following_ids = {u["id"] for u in following}

    follower_map = {u["id"]: u for u in followers}
    following_map = {u["id"]: u for u in following}

    unfollower_ids = following_ids - follower_ids
    mutual_ids = following_ids & follower_ids
    fan_ids = follower_ids - following_ids

    unfollowers = sorted([following_map[uid] for uid in unfollower_ids], key=lambda u: u["login"].lower())
    mutual = sorted([follower_map[uid] for uid in mutual_ids], key=lambda u: u["login"].lower())
    fans = sorted([follower_map[uid] for uid in fan_ids], key=lambda u: u["login"].lower())

    return ComparisonResult(
        username=username,
        followers=followers,
        following=following,
        unfollowers=unfollowers,
        mutual=mutual,
        fans=fans,
    )


# ─── Output ───────────────────────────────────────────────────────────────────

def print_table(users: list[dict], title: str, color: str):
    """打印用户表格。"""
    print()
    print(f"{color}{title}{RESET}")

    if not users:
        print(f"  {DIM}(无){RESET}")
        return

    max_login = max(len(u["login"]) for u in users)
    num_width = len(str(len(users)))

    header = f"  {'#':>{num_width}}  {'Username':<{max_login + 1}}  {'Profile URL'}"
    print(f"{DIM}{header}{RESET}")
    print(f"  {'─' * num_width}  {'─' * (max_login + 1)}  {'─' * 30}")

    for i, user in enumerate(users, 1):
        login = user["login"]
        url = user.get("html_url", f"https://github.com/{login}")
        print(f"  {DIM}{i:>{num_width}}{RESET}  {color}@{login}{RESET}  {DIM}{url}{RESET}")


def print_result(result: ComparisonResult):
    """打印完整的对比结果。"""
    print()

    # 汇总面板
    print(f"{BOLD_CYAN}╭────────────── 📈 GitHub Follow Report ──────────────╮{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}👤 User:{RESET} {BOLD_CYAN}@{result.username}{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}📊 Followers:{RESET} {len(result.followers)}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}📊 Following:{RESET} {len(result.following)}")
    print(f"{BOLD_CYAN}│{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}🔴 Unfollowers:{RESET} {BOLD_RED}{len(result.unfollowers)}{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}🟢 Mutual follows:{RESET} {BOLD_GREEN}{len(result.mutual)}{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}🔵 Fans:{RESET} {BOLD_BLUE}{len(result.fans)}{RESET}")
    print(f"{BOLD_CYAN}╰─────────────────────────────────────────────────────╯{RESET}")

    # 白名单提示
    if result.whitelisted_hidden:
        names = ", ".join(
            f"@{u['login']}"
            for u in sorted(result.whitelisted_hidden, key=lambda u: u["login"].lower())
        )
        print(f"  {DIM}🤍 白名单用户（不出现在 Unfollowers/Fans 列表，也不参与回关/取关）: {names}{RESET}")

    # 取关你的人
    if result.unfollowers:
        print_table(
            result.unfollowers,
            f"🔴 Unfollowers - 你关注了他们，但他们没关注你 ({len(result.unfollowers)})",
            RED,
        )
    else:
        print(f"\n  {BOLD_GREEN}✅ 没有人取关你！{RESET}")

    # 关注你但你没回关的人
    if result.fans:
        print_table(
            result.fans,
            f"🔵 Fans - 关注你但你没回关 ({len(result.fans)})",
            BLUE,
        )

    # 互相关注
    if result.mutual:
        print_table(
            result.mutual,
            f"🟢 Mutual follows - 互相关注 ({len(result.mutual)})",
            GREEN,
        )

    print()


# ─── Batch Actions ────────────────────────────────────────────────────────────

def confirm(prompt: str) -> bool:
    """Ask user for y/n confirmation."""
    try:
        answer = input(f"{BOLD_YELLOW}{prompt} [y/N]: {RESET}").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def batch_follow(api: GitHubAPI, users: list[dict], action: str):
    """
    Batch follow/unfollow users with progress display.
    action: "follow" or "unfollow"
    """
    if not users:
        print(f"\n  {DIM}没有需要处理的用户。{RESET}")
        return

    verb = "关注" if action == "follow" else "取关"
    total = len(users)

    print(f"\n{BOLD_CYAN}🚀 开始批量{verb} {total} 个用户...{RESET}\n")

    success = 0
    failed = 0

    for i, user in enumerate(users, 1):
        login = user["login"]

        if action == "follow":
            ok = api.follow_user(login)
        else:
            ok = api.unfollow_user(login)

        status = f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"
        print(f"  {status} [{i}/{total}] @{login}")

        if ok:
            success += 1
        else:
            failed += 1

        # Small delay to be nice to the API
        if i < total:
            time.sleep(0.5)

    print(f"\n{BOLD_CYAN}╭──────────────────────────────────────────╮{RESET}")
    print(f"{BOLD_CYAN}│{RESET} {BOLD}{verb}完成！{RESET}")
    print(f"{BOLD_CYAN}│{RESET}   成功: {GREEN}{success}{RESET}")
    if failed:
        print(f"{BOLD_CYAN}│{RESET}   失败: {RED}{failed}{RESET}")
    print(f"{BOLD_CYAN}╰──────────────────────────────────────────╯{RESET}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="GitHub Unfollower Checker - 找出取关了你的人，支持一键回关/取关",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                  查看对比结果
  python main.py --follow-back    一键回关所有粉丝
  python main.py --unfollow       一键取关所有 unfollowers
  python main.py -u <username>    查看指定用户
  python main.py --exclude-user octocat    把 @octocat 加入白名单（不显示也不处理）
        """,
    )
    parser.add_argument("-u", "--username", help="GitHub 用户名（默认用 token 对应的用户）")
    parser.add_argument("--follow-back", action="store_true", help="一键回关所有粉丝（关注你但你没回关的人）")
    parser.add_argument("--unfollow", action="store_true", help="一键取关所有 unfollowers（你关注了但没关注你的人）")
    parser.add_argument("--no-mutual", action="store_true", help="不显示互相关注")
    parser.add_argument("--no-fans", action="store_true", help="不显示粉丝")
    parser.add_argument("-y", "--yes", action="store_true", help="跳过确认提示，直接执行")
    parser.add_argument(
        "--whitelist",
        metavar="FILE",
        help="白名单文件路径（默认读取脚本目录下的 whitelist.txt，一行一个用户名，# 为注释）",
    )
    parser.add_argument(
        "--exclude-user",
        action="append",
        metavar="USERNAME",
        help="将指定用户加入白名单（可重复使用多次）",
    )
    args = parser.parse_args()

    # 加载配置
    script_dir = Path(__file__).parent
    load_dotenv(script_dir / ".env")

    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "your_token_here":
        print("❌ Error: GITHUB_TOKEN 未设置。")
        print()
        print("请设置你的 GitHub Personal Access Token:")
        print("  1. 复制 .env.example 为 .env")
        print("  2. 编辑 .env，填入你的 token")
        print("  3. 获取 token: https://github.com/settings/tokens")
        print("     注意：一键关注/取关需要 user:follow 权限")
        sys.exit(1)

    username = args.username or os.getenv("GITHUB_USERNAME")

    try:
        api = GitHubAPI(token)

        if not username:
            print("🔍 正在检测当前用户...")
            username = api.get_authenticated_user()

        print(f"\n📡 正在获取 @{username} 的数据...")

        print("  获取 followers...")
        followers = api.get_followers(username)
        print(f"  找到 {len(followers)} 个 followers")

        print("  获取 following...")
        following = api.get_following(username)
        print(f"  找到 {len(following)} 个 following")

        print("  对比中...")
        result = compare(followers, following, username)

        if args.no_mutual:
            result.mutual = []
        if args.no_fans:
            result.fans = []

        # ── 应用白名单 ──
        # 白名单用户不出现在 Unfollowers/Fans 列表中，也不会被回关/取关
        whitelist_path = Path(args.whitelist) if args.whitelist else script_dir / "whitelist.txt"
        if args.whitelist and not whitelist_path.exists():
            print(f"⚠️  白名单文件不存在: {whitelist_path}")
        whitelist = load_whitelist(whitelist_path, args.exclude_user)
        if whitelist:
            result.whitelisted_hidden = [
                u for u in result.unfollowers + result.fans
                if whitelist_key(u["login"]) in whitelist
            ]
            result.unfollowers = [
                u for u in result.unfollowers if whitelist_key(u["login"]) not in whitelist
            ]
            result.fans = [
                u for u in result.fans if whitelist_key(u["login"]) not in whitelist
            ]
            print(f"  🤍 白名单已启用: 共 {len(whitelist)} 人，本次过滤 {len(result.whitelisted_hidden)} 人")

        # 显示对比结果
        print_result(result)

        # ── 一键回关粉丝 ──
        if args.follow_back:
            fans = result.fans
            if not fans:
                print(f"\n  {DIM}没有需要回关的粉丝。{RESET}\n")
            else:
                print(f"\n  {BOLD_BLUE}📋 即将回关 {len(fans)} 个粉丝:{RESET}")
                for user in fans:
                    print(f"     {BLUE}@{user['login']}{RESET}")

                if args.yes or confirm(f"\n  确认回关以上 {len(fans)} 个粉丝？"):
                    batch_follow(api, fans, "follow")
                else:
                    print(f"  {DIM}已取消。{RESET}")

        # ── 一键取关 unfollowers ──
        if args.unfollow:
            unfollowers = result.unfollowers
            if not unfollowers:
                print(f"\n  {DIM}没有需要取关的用户。{RESET}\n")
            else:
                print(f"\n  {BOLD_RED}📋 即将取关 {len(unfollowers)} 个 unfollowers:{RESET}")
                for user in unfollowers:
                    print(f"     {RED}@{user['login']}{RESET}")

                if args.yes or confirm(f"\n  确认取关以上 {len(unfollowers)} 个用户？"):
                    batch_follow(api, unfollowers, "unfollow")
                else:
                    print(f"  {DIM}已取消。{RESET}")

    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n已中断。")
        sys.exit(0)


if __name__ == "__main__":
    main()
