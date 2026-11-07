"""推播 / 功能狀態測試工具（CLI）。在專案根目錄執行：

    python -m app.cli --help

【直接推播】不需要開 server，讀本機 DB 的裝置直接發 FCM（沒設定 FCM 就只印出、記錄）
    python -m app.cli devices                              列出已登記的裝置
    python -m app.cli push --token <FCM token>             推一則「預約成功」給這支手機
    python -m app.cli push --mailbox mb_xxx --type stock.arrived
    python -m app.cli push --all --type service.notice --title "測試公告"
    python -m app.cli topic --title "測試公告"             推給所有訂閱 assistive-notice 的 App
    python -m app.cli types                                列出所有通知類型與文案
    python -m app.cli outbox                               最近的推播紀錄
    python -m app.cli watch                                即時顯示新的推播（Ctrl+C 結束）

【功能狀態】要先用 TEST_MODE=true 開 server（python app/main.py），走真正的流程並推播
    python -m app.cli state                                信箱、預約、裝置、最近推播
    python -m app.cli scenario --token <FCM token>         建信箱 + 登記手機 + 借用預約（推「預約成功」）
    python -m app.cli trigger <預約編號> pickup_reminder   取貨提醒
    python -m app.cli trigger <預約編號> expired           逾期自動取消（會釋回庫存）
    python -m app.cli trigger <預約編號> confirmed|completed|cancelled
    python -m app.cli stock <variant_id> 3                 設定庫存（0 → >0 推「到貨通知」）
    python -m app.cli notice "11/20 系統維護"              發公告
    python -m app.cli flow --token <FCM token>             一次跑完：預約成功 → 取貨提醒 → 逾期
"""

import argparse
import asyncio
import json
import sys
import time

import httpx

from app.config import get_settings


# ---------------- 共用 ----------------
def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def _api(args) -> str:
    return args.server.rstrip("/") + get_settings().api_prefix


def _call(args, method: str, path: str, **kw):
    try:
        res = httpx.request(method, _api(args) + path, timeout=30, **kw)
    except httpx.ConnectError:
        sys.exit(f"✗ 連不到 server {args.server}。先用 TEST_MODE=true 啟動：python app/main.py")
    if res.status_code == 404 and path.startswith("/_test"):
        sys.exit("✗ server 不是測試模式。請在 .env 設 TEST_MODE=true 後重開 server。")
    if res.status_code >= 400:
        print(f"✗ HTTP {res.status_code}")
        _print_json(res.json() if res.headers.get("content-type", "").endswith("json") else res.text)
        sys.exit(1)
    return res.json() if res.content else None


def _print_pushes(rows) -> None:
    if not rows:
        print("（還沒有推播紀錄）")
    for r in rows:
        mark = {"ok": "✓", "local": "·", "retry": "↻"}.get(r["result"], "✗")
        print(f"{mark} #{r['id']} {r['created_at'][11:19]} [{r['result']}] {r['type']} → {r['target']}")
        print(f"     {r['title']}｜{r['body']}")


# ---------------- 直接推播（不需要 server）----------------
def cmd_devices(args) -> None:
    from app.features.devices import repository as repo

    rows = repo.all_devices()
    if not rows:
        print("（沒有登記的裝置。App 啟動時會呼叫 POST /devices，或用 `scenario --token` 登記）")
    for d in rows:
        print(f"{d.mailbox_id}  {d.platform}  {d.updated_at:%m/%d %H:%M}  {d.token}")


def cmd_types(args) -> None:
    from app.features.notification import texts

    print(texts.__doc__.split("\n\n", 1)[1])


def cmd_push(args) -> None:
    from app.features.devices import repository as repo
    from app.features.notification import texts
    from app.features.notification.service import PendingPush, log_push
    from app.tools import fcm
    from app.tools.security import new_id

    if args.token:
        targets = [(args.token, args.mailbox)]
    elif args.mailbox:
        targets = [(d.token, d.mailbox_id) for d in repo.by_mailbox(args.mailbox)]
    elif args.all:
        targets = [(d.token, d.mailbox_id) for d in repo.all_devices()]
    else:
        sys.exit("請指定 --token、--mailbox 或 --all")
    if not targets:
        sys.exit("✗ 找不到裝置（python -m app.cli devices 看已登記的）")

    title, body = texts.build(args.type, deadline=args.deadline, center_id=args.center, notice_title=args.title)
    data = {"type": args.type, "event_id": new_id("ev"), "reservation_id": args.reservation_id,
            "variant_id": args.variant_id}
    if not fcm.is_enabled():
        print("· 沒設定 Firebase，推播只記錄在本機（[local]），不會送到手機")

    async def run():
        for token, mailbox_id in targets:
            push = PendingPush(fcm.build_message(title=title, body=body, data=data, token=token), token, 0, mailbox_id)
            result = await fcm.send(push.message)
            log_push(push, result)
            print(f"{'✓' if result == fcm.SendResult.OK else '·' if result == fcm.SendResult.LOCAL else '✗'} "
                  f"[{result.value}] {token[:16]}…  {title}｜{body}")
            if result == fcm.SendResult.INVALID_TOKEN:
                repo.delete(token)
                print("  token 已失效，已從 DB 移除")

    asyncio.run(run())


def cmd_topic(args) -> None:
    from app.features.notification import texts
    from app.features.notification.service import PendingPush, log_push
    from app.tools import fcm
    from app.tools.security import new_id

    title, body = texts.build("service.notice", notice_title=args.title)
    msg = fcm.build_message(title=title, body=body, data={"type": "service.notice", "event_id": new_id("ev")},
                            topic=get_settings().fcm_notice_topic)
    result = asyncio.run(fcm.send(msg))
    log_push(PendingPush(msg, None, 0), result)
    print(f"[{result.value}] topic:{get_settings().fcm_notice_topic}  {title}｜{body}")


def cmd_outbox(args) -> None:
    from app.tools import db

    rows = db.query("SELECT * FROM push_log ORDER BY id DESC LIMIT ?", (args.n,))
    _print_pushes(list(reversed(rows)))


def cmd_watch(args) -> None:
    from app.tools import db

    last = (db.query("SELECT MAX(id) AS m FROM push_log")[0]["m"] or 0)
    print(f"等待新的推播…（每 {args.interval} 秒檢查一次，Ctrl+C 結束）")
    try:
        while True:
            rows = db.query("SELECT * FROM push_log WHERE id > ? ORDER BY id", (last,))
            if rows:
                _print_pushes(rows)
                last = rows[-1]["id"]
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass


# ---------------- 功能狀態（打測試模式 server）----------------
def cmd_state(args) -> None:
    s = _call(args, "GET", "/_test/state", params={"limit": args.n})
    print(f"FCM：{'已設定' if s['fcm_enabled'] else '未設定（只記錄不送出）'}　庫存版本：{s['stock_version']}")
    print(f"\n信箱（{len(s['mailboxes'])}）")
    for m in s["mailboxes"]:
        print(f"  {m['mailbox_id']}  事件 {m['events']}  裝置 {m['devices']}")
    print(f"\n預約（{len(s['reservations'])}）")
    for r in s["reservations"]:
        print(f"  {r['id']}  {r['service']:<7} {r['status']:<10} {r['center_id']:<6} 期限 {r['pickup_deadline']}  "
              f"送件 {r['forward_state']}  信箱 {r['mailbox_id']}")
    print(f"\n裝置（{len(s['devices'])}）")
    for d in s["devices"]:
        print(f"  {d['token']}  → {d['mailbox_id']}")
    print("\n最近推播")
    _print_pushes(list(reversed(s["recent_pushes"])))


def cmd_scenario(args) -> dict:
    r = _call(args, "POST", "/_test/scenario", json={"token": args.token, "variant_id": args.variant})
    res = r["reservation"]
    print(f"✓ 信箱 {r['mailbox_id']}")
    print(f"  mailbox_key {r['mailbox_key']}（App 用這個呼叫 /devices、/subscriptions）")
    print(f"✓ 預約 {res['id']}  狀態 {res['status']}  中心 {r['center_id']}  取貨期限 {res['pickup']['deadline']}")
    print(f"  access_key {res['access_key']}")
    if r["device_token"].startswith("local-"):
        print("· 沒給 --token：已登記本機假裝置，推播只記錄在本機（outbox / watch 看得到），不會送到手機")
    else:
        print("✓ 已登記手機，應該會收到「預約成功」")
    return r


def cmd_trigger(args) -> None:
    r = _call(args, "POST", f"/_test/reservations/{args.reservation_id}/trigger", json={"event": args.event})
    print(f"✓ {r['id']} → 狀態 {r['status']}（version {r['version']}）")


def cmd_stock(args) -> None:
    r = _call(args, "POST", "/_test/stock", json={"variant_id": args.variant_id, "stock": args.stock,
                                                    "waiting": args.waiting})
    print(f"✓ {'已更新' if r['changed'] else '沒有變動'}，庫存版本 {r['version']}")


def cmd_notice(args) -> None:
    r = _call(args, "POST", "/_test/notices", json={"title": args.title, "center_ids": args.center or []})
    print(f"✓ 公告已寫進 {r['mailboxes']} 個信箱，並推播到 topic")


def cmd_flow(args) -> None:
    print("① 建立預約")
    r = cmd_scenario(args)
    rid = r["reservation"]["id"]
    for event, label in (("pickup_reminder", "② 取貨提醒"), ("expired", "③ 逾期自動取消")):
        time.sleep(args.interval)
        print(label)
        args.reservation_id, args.event = rid, event
        cmd_trigger(args)
    time.sleep(1)
    print("\n推播紀錄")
    s = _call(args, "GET", "/_test/state", params={"limit": 10})
    _print_pushes([p for p in reversed(s["recent_pushes"]) if p["mailbox_id"] == r["mailbox_id"]])


def main(argv=None) -> None:
    from app.features.reservation.schemas import Status  # noqa: F401  (確保 app 可 import)

    types = ["reservation.booked", "reservation.pickup_reminder", "reservation.expired", "reservation.confirmed",
             "reservation.completed", "reservation.cancelled", "stock.arrived", "service.notice"]
    p = argparse.ArgumentParser(prog="python -m app.cli", description="推播 / 功能狀態測試工具",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    s = get_settings()
    p.add_argument("--server", default=f"http://{s.host}:{s.port}", help="server 網址（功能狀態指令用，預設讀 HOST / PORT）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices", help="列出已登記的裝置").set_defaults(fn=cmd_devices)
    sub.add_parser("types", help="列出通知類型與文案").set_defaults(fn=cmd_types)

    s = sub.add_parser("push", help="直接推播給裝置（不需要 server）")
    g = s.add_mutually_exclusive_group()
    g.add_argument("--token", help="FCM token")
    g.add_argument("--all", action="store_true", help="DB 裡所有裝置")
    s.add_argument("--mailbox", help="只推給這個信箱的裝置")
    s.add_argument("--type", default="reservation.booked", choices=types)
    s.add_argument("--reservation-id", default="B202611070001")
    s.add_argument("--variant-id")
    s.add_argument("--deadline", help="取貨期限 YYYY-MM-DD（booked / pickup_reminder 用）")
    s.add_argument("--center", default="heyi", choices=["heyi", "south", "west"])
    s.add_argument("--title", help="公告標題（service.notice 用）")
    s.set_defaults(fn=cmd_push)

    s = sub.add_parser("topic", help="推公告到 topic（不需要 server）")
    s.add_argument("--title", required=True)
    s.set_defaults(fn=cmd_topic)

    s = sub.add_parser("outbox", help="最近的推播紀錄")
    s.add_argument("-n", type=int, default=20)
    s.set_defaults(fn=cmd_outbox)

    s = sub.add_parser("watch", help="即時顯示新的推播")
    s.add_argument("--interval", type=float, default=2)
    s.set_defaults(fn=cmd_watch)

    s = sub.add_parser("state", help="[server] 狀態總覽")
    s.add_argument("-n", type=int, default=10)
    s.set_defaults(fn=cmd_state)

    s = sub.add_parser("scenario", help="[server] 建信箱 + 登記裝置 + 借用預約")
    s.add_argument("--token")
    s.add_argument("--variant")
    s.set_defaults(fn=cmd_scenario)

    s = sub.add_parser("trigger", help="[server] 讓預約進入某狀態")
    s.add_argument("reservation_id")
    s.add_argument("event", choices=["pickup_reminder", "expired", "confirmed", "completed", "cancelled"])
    s.set_defaults(fn=cmd_trigger)

    s = sub.add_parser("stock", help="[server] 設定庫存")
    s.add_argument("variant_id")
    s.add_argument("stock", type=int)
    s.add_argument("--waiting", type=int, default=0)
    s.set_defaults(fn=cmd_stock)

    s = sub.add_parser("notice", help="[server] 發公告")
    s.add_argument("title")
    s.add_argument("--center", action="append", choices=["heyi", "south", "west"])
    s.set_defaults(fn=cmd_notice)

    s = sub.add_parser("flow", help="[server] 一次跑完：預約成功 → 取貨提醒 → 逾期")
    s.add_argument("--token")
    s.add_argument("--variant")
    s.add_argument("--interval", type=float, default=3, help="每一步間隔秒數")
    s.set_defaults(fn=cmd_flow)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
