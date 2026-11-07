"""推播文案（繁體中文）。

⚠ 通知會顯示在鎖定畫面：不放姓名、身分證、電話。
  預約類通知不放輔具名稱 / 項目（使用輔具會透露身心障礙或健康狀況，規格原則 4）。
  例外：到貨通知（stock.arrived）依團隊決定顯示品項名稱，讓使用者知道是什麼到貨了。

| type                         | 標題         | 內容                               |
|------------------------------|--------------|------------------------------------|
| reservation.booked           | 預約成功     | 請於 {期限} 前到{中心}取貨         |
| reservation.pickup_reminder  | 取貨提醒     | 預約將於 {期限} 到期，請記得取貨   |
| reservation.expired          | 預約已逾期   | 預約已自動取消                     |
| reservation.confirmed        | 中心已確認   | {中心}已確認你的申請               |
| reservation.completed        | 服務已完成   | 你的申請已辦理完成                 |
| reservation.cancelled        | 預約已取消   | 這筆預約已取消                     |
| stock.arrived                | 到貨通知     | 你訂閱的「{品項名稱}」已到貨，可以預約了（查不到名稱：你訂閱的輔具已到貨，可以預約了） |
| service.notice               | 服務公告     | {公告標題}                         |
"""

from datetime import date

from app.tools.districts import CENTER_NAMES

_WEEKDAYS = "一二三四五六日"


def fmt_date(d: date | str | None) -> str:
    """2026-11-08 → 11/8（日）"""
    if d is None:
        return "期限"
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{d.month}/{d.day}（{_WEEKDAYS[d.weekday()]}）"


def center_name(center_id: str | None) -> str:
    return CENTER_NAMES.get(center_id or "", "輔具中心")


def build(type: str, *, deadline: date | str | None = None, center_id: str | None = None,
          notice_title: str | None = None, variant_name: str | None = None) -> tuple[str, str]:
    """回傳 (title, body)。"""
    match type:
        case "reservation.booked":
            return "預約成功", f"請於 {fmt_date(deadline)} 前到{center_name(center_id)}取貨"
        case "reservation.pickup_reminder":
            return "取貨提醒", f"預約將於 {fmt_date(deadline)} 到期，請記得取貨"
        case "reservation.expired":
            return "預約已逾期", "預約已自動取消"
        case "reservation.confirmed":
            return "中心已確認", f"{center_name(center_id)}已確認你的申請"
        case "reservation.completed":
            return "服務已完成", "你的申請已辦理完成"
        case "reservation.cancelled":
            return "預約已取消", "這筆預約已取消"
        case "stock.arrived":
            if variant_name:
                return "到貨通知", f"您登記的「{variant_name}」已經到貨，歡迎前往預約。"
            return "到貨通知", "您登記的輔具已經到貨，歡迎前往預約。"
        case "service.notice":
            return "服務公告", notice_title or "輔具中心有新公告"
    return "輔具預約", "你有一則新通知"
