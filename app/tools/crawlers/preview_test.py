"""人工建立 HTML fixture，驗證官網 ID、缺值與營業日邊界。"""

import unittest
from datetime import date

from .preview import (build_calendar, parse_attrs, parse_categories, parse_variants,
                      read_csv, soup_of, table_rows)


class ParserTests(unittest.TestCase):
    def test_category_ids_are_not_reindexed(self):
        html = '''<div class="col-md-9"><div class="ind-tab">
        <img src="/app37/tools/showvehiclemodel/20" alt="其他圖片">
        <button onclick="window.location.assign('/app37/rentView/vehicleDetail/20')">查看</button>
        </div></div>'''
        result = parse_categories(html)
        self.assertEqual(result[0]["id"], "20")
        self.assertTrue(result[0]["detail_url"].endswith("/20"))

    def test_variants_preserve_original_ids_and_unknown_stock(self):
        html = '''<div class="col-md-9"><table class="ind-tab">
        <tr><td rowspan="3"><img src="/app37/tools/showvehiclemodeltype/185"></td><th>輪椅</th></tr>
        <tr><td>座寬15或16吋（體重70公斤以下者適用）</td><td>---</td><td>剩餘:未知</td></tr>
        <tr><td colspan="2">請先評估</td><td><span>等待人數：0</span></td></tr>
        </table></div>'''
        variants, stock = parse_variants(html, "https://tpap.gov.taipei/test")
        self.assertEqual(variants[0]["id"], stock[0]["variant_id"])
        self.assertEqual(stock[0]["variant_id"], "185")
        self.assertIsNone(stock[0]["stock"])
        self.assertEqual(stock[0]["waiting"], 0)
        self.assertIsNone(variants[0]["attrs"]["seat_width_in"])
        self.assertEqual(variants[0]["attrs"]["weight_max_kg"], 70)
        self.assertEqual(len(variants[0]["specs"]), 1)

    def test_explicit_units_only(self):
        attrs = parse_attrs(["座寬45.72公分", "適用身高150–180公分", "承重100公斤"])
        self.assertEqual(attrs["seat_width_in"], 18)
        self.assertEqual(attrs["height_min"], 150)
        self.assertEqual(attrs["height_max"], 180)
        self.assertEqual(attrs["weight_max_kg"], 100)
        self.assertIsNone(parse_attrs(["座高45公分", "重量15公斤"]))

    def test_available_item_without_waiting_field_uses_documented_zero(self):
        html = '''<table class="ind-tab">
        <tr><td rowspan="3"><img src="/app37/tools/showvehiclemodeltype/30"></td><th>無輪</th></tr>
        <tr><td>身高150-175cm</td><td>---</td><td>剩餘:6</td></tr>
        <tr><td colspan="2">說明</td><td><button onclick="window.location.assign('/app37/rentView/chooseCenterCategory/30')">預約</button></td></tr>
        </table>'''
        _, stock = parse_variants(html, "https://tpap.gov.taipei/test")
        self.assertEqual(stock[0]["waiting"], 0)
        self.assertIsNone(stock[0]["waiting_observed"])
        self.assertIn("README", stock[0]["waiting_basis"])

    def test_government_saturday_does_not_close_center(self):
        center = {"open_days": [2, 3, 4, 5, 6], "hours": [{"from": "09:00", "to": "12:00"}, {"from": "13:30", "to": "17:00"}]}
        rows = [{"西元日期": "20261107", "是否放假": "2", "備註": ""}]
        calendar = build_calendar(center, date(2026, 11, 7), 3, rows)
        self.assertEqual([r["open"] for r in calendar], [True, False, False])
        self.assertEqual(len(calendar[0]["hours"]), 2)
        rows[0]["備註"] = "國定假日"
        self.assertFalse(build_calendar(center, date(2026, 11, 7), 1, rows)[0]["open"])

    def test_rowspan_retains_parent_center(self):
        table = soup_of('<table><tr><th>中心</th><th>據點</th></tr><tr><td rowspan="2">合宜</td><td>士林</td></tr><tr><td>北投</td></tr></table>').table
        self.assertEqual(table_rows(table), [["中心", "據點"], ["合宜", "士林"], ["合宜", "北投"]])

    def test_csv_rejects_error_page_and_preserves_missing_marker(self):
        with self.assertRaises(ValueError):
            read_csv(b"<!doctype html><html>Error</html>")
        rows = read_csv("\ufeff行政區,人數\n中山區,-\n".encode("utf-8"))
        self.assertEqual(rows[0]["人數"], "-")


if __name__ == "__main__":
    unittest.main()
