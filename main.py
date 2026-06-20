import subprocess
import json
import requests
import time
import yaml
import traceback
import os
import platform
from datetime import datetime

# =========================
# OS判定
# =========================
IS_WINDOWS = platform.system() == "Windows"

# =========================
# パス
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
LOG_PATH = os.path.join(BASE_DIR, "monitor.log")

TAILSCALE_CMD = "tailscale"

# =========================
# ログ
# =========================
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# =========================
# config読み込み
# =========================
def load_config(path):
    if not os.path.exists(path):
        raise Exception(f"❌ config.yaml が見つかりません:\n{path}")

    encodings = ["utf-8", "utf-8-sig", "cp932"]

    for enc in encodings:
        try:
            with open(path, encoding=enc) as f:
                log(f"config loaded ({enc})")
                config = yaml.safe_load(f)

                if not config:
                    raise Exception("❌ config.yaml が空です")

                return config
        except UnicodeDecodeError:
            continue

    raise Exception("❌ config.yaml 読み込み失敗")

# =========================
# Discord送信
# =========================
def send_discord(webhook, messages):
    payload = {"content": "\n".join(messages)}

    try:
        r = requests.post(webhook, json=payload, timeout=5)
        log(f"Discord送信 status={r.status_code}")
    except Exception as e:
        log(f"Discord送信失敗: {e}")

# =========================
# ping
# =========================
def check_ping(addr, enabled):
    if not enabled:
        return True

    # 🔥 OS分岐いらない
    cmd = [TAILSCALE_CMD, "ping", "--c", "3", addr]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    output = ((result.stdout or "") + (result.stderr or "")).lower()

    if any(x in output for x in [
        "pong",
        "via",
        "direct",
        "latency",
    ]):
        return True

    return False

# =========================
# メイン
# =========================
def main():
    # config読み込み（失敗で即終了）
    try:
        config = load_config(CONFIG_PATH)
    except Exception as e:
        print(str(e))
        input("Enterキーで終了...")
        return

    webhook = config["webhook_url"]
    interval = config.get("interval", 30)
    nodes = config["nodes"]

    ping_enabled = config.get("ping", {}).get("enabled", True)
    FAIL_THRESHOLD = config.get("ping", {}).get("fail_threshold", 3)

    stable_seconds = config.get("stable_seconds", 30)
    include_shared = config.get("include_shared", True)

    last_states = {}
    notified_state = {}
    change_time = {}
    fail_count = {node["name"]: 0 for node in nodes}

    log("Monitor started")
    send_discord(webhook, ["🚀 Tailscale Monitor 起動"])

    try:
        while True:
            try:
                now = time.time()
                states = {}
                changes = []

                for node in nodes:
                    name = node["name"]
                    alias = node.get("alias", "")

                    display_name = f"{name}（{alias}）" if alias else name

                    addr = node["address"]
                    is_important = node.get("important", False)

                    ping_ok = check_ping(addr, ping_enabled)

                    # ===== 失敗カウント =====
                    if ping_ok:
                        fail_count[name] = 0
                        current = True
                    else:
                        fail_count[name] += 1

                        if fail_count[name] >= FAIL_THRESHOLD:
                            current = False
                        else:
                            current = last_states.get(name, True)

                    states[name] = current

                    prev = last_states.get(name)

                    if prev is None:
                        last_states[name] = current
                        notified_state[name] = current
                        change_time[name] = now
                        continue

                    # ===== 状態変化検知 =====
                    if current != prev:
                        change_time[name] = now
                        last_states[name] = current

                        log(f"{name} 状態変化 → {current} (fail={fail_count[name]})")

                        if is_important:
                            icon = "🟢" if current else "🔴"
                            changes.append(f"{icon} {display_name}: {'ONLINE' if current else 'OFFLINE'}（重要）")
                            notified_state[name] = current

                        continue

                    # ===== 安定判定 =====
                    elapsed = now - change_time.get(name, now)

                    if current != notified_state.get(name) and elapsed >= stable_seconds:
                        icon = "🟢" if current else "🔴"
                        changes.append(f"{icon} {display_name}: {'ONLINE' if current else 'OFFLINE'}（{int(elapsed)}秒継続）")

                        notified_state[name] = current

                log(f"states: {states}")
                log(f"fail_count: {fail_count}")
                log(f"changes: {changes}")

                if changes:
                    send_discord(webhook, changes)

            except Exception as e:
                log(f"ERROR: {e}")
                log(traceback.format_exc())
                send_discord(webhook, [f"⚠️ Error: {e}"])

            time.sleep(interval)

    except KeyboardInterrupt:
        log("🛑 手動停止")

# =========================
if __name__ == "__main__":
    main()
