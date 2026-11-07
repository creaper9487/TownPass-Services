# 本機政府辦公日曆

來源：[行政院人事行政總處／政府資料開放平臺資料集 14718](https://data.gov.tw/dataset/14718)。
資料集標示政府資料開放授權條款第 1 版。下載及驗證日期：2026-11-07。

| 本機檔案 | 年份 | 已驗證日期數 | 官方原始 CSV |
|---|---|---:|---|
| holidays_2026.csv | 民國 115／2026 | 365 | https://www.dgpa.gov.tw/FileConversion?filename=dgpa%2Ffiles%2F202506%2Fa52331bd-a189-466b-b0f0-cae3062bbf74.csv&nfix= |
| holidays_2027.csv | 民國 116／2027 | 365 | https://www.dgpa.gov.tw/FileConversion?filename=dgpa%2Ffiles%2F202607%2Ff538b1ff-ba60-4c63-9477-10db8e6612d1.csv&nfix= |

檔案保留官方 CSV 欄位與資料，UTF-8 BOM；由 `parse_holidays` 驗證全年筆數、唯一日期、年度及休假標記。
執行期只讀本機檔案，不呼叫 dgpa.gov.tw。部署時需連同這個 data 資料夾一起包含。

年度手動更新：

1. 到官方資料集下載一般格式 CSV，勿選 Google 行事曆專用格式。
2. 儲存為 `holidays_西元年.csv`，在 `_calendar_source.py` 登記該年份並記錄來源。
3. 執行 `python -m pytest -q`，確認全年資料解析與跨年測試通過。
4. 將 CSV 與程式一同提交、部署；官方修正既有年度時，更新該檔案並重新部署。

未提供年度仍明確回報尚未實作；本機檔案缺漏或損壞會報錯，不假造節日。
