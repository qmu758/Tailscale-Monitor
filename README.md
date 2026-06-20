# Tailscale-Monitor
This script notifies Discord of the online/offline status of machines on Tailscale.

Tailscale監視 → Discord通知スクリプト
README（Windows / VPS対応）

---

## ■ 概要

このスクリプトは、Tailscaleに接続されている端末の
「オンライン / オフライン状態」を監視し、
Discordに通知します。

・特定ノードのみ監視可能
・一定時間安定後に通知（誤検知防止）
・重要ノードは即通知
・Windows / VPS 両対応

---

## ■ 必要なもの

・Python 3.8以上
・Tailscale
・Discord Webhook URL

---

## ■ Pythonライブラリインストール

以下を実行してください：

Windows / VPS 共通

pip install requests pyyaml

※ VPSの場合：

pip3 install requests pyyaml

---

## ■ 設定ファイル（config.yaml）

同じフォルダの config.yaml を編集

例：

webhook_url: "https://discord.com/api/webhooks/XXXX"

interval: 30
stable_seconds: 30

nodes:

* name: "example-node"
  address: "100.xxx.xxx.xxx"
  important: true

ping:
enabled: false

---

## ■ Windowsでの使い方

① フォルダに配置
main.py
config.yaml

② コマンドプロンプトで実行

python main.py

③ 常駐したい場合
タスクスケジューラを使用

---

## ■ VPSでの使い方

① VPSのSSHポートを開放する　※ポート番号：22（デフォルト）

② VPSにログイン

ssh root@IPアドレス

③ Pythonインストール

apt update
apt install python3 python3-pip -y

④ ライブラリインストール

pip3 install requests pyyaml

⑤ Tailscaleインストール

curl -fsSL https://tailscale.com/install.sh | sh

⑥ Tailscale起動

tailscale up

→ 表示されるURLをブラウザで開きログイン

⑦ ファイル配置

mkdir ~/tailscale-monitor
cd ~/tailscale-monitor

nano main.py
nano config.yaml

（main.py config.yaml のファイル内容を貼り付け → Ctrl + O → Enter → Ctrl + X）

⑧ 実行

python3 main.py

---

## ■ VPSで常駐させる（重要）

① crontab設定

crontab -e

② 以下を追加

@reboot sleep 10 && tailscale up
@reboot sleep 20 && cd /root/tailscale-monitor && /usr/bin/python3 main.py

③ 保存

Ctrl + O → Enter → Ctrl + X

---

## ■ 動作確認

ログ確認：

tail -f monitor.log

---

## ■ よくあるエラー

① config.yamlが見つからない
→ 同じフォルダに配置

② config.yamlが空
→ 中身を記入する

③ tailscaleが未接続
→ tailscale up を実行

④ Discord通知されない
→ Webhook URL確認

---

## ■ 注意事項

・Webhook URLは他人に共有しないでください
・VPSは常時起動が前提です
・無料VPSは停止する場合があります

---

## ■ 補足

・重要ノードは即通知
・通常ノードは一定時間後に通知

---

## ■ 備考

・monitor.log にログ出力
・Windows / Linux 自動判定対応
・Ctrl+Cで安全終了

---

## 以上
