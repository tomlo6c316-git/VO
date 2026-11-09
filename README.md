# 工程變更 (VO) 自動排版系統

以 Streamlit 上傳工程 VO 事前／完成相片，匯出繁體中文 A4 PDF。完成相片可留空；PDF 每頁放兩筆紀錄，左邊事前、右邊完成，形成 2×2 排版。

## 執行與部署

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit Community Cloud 請選擇此儲存庫的 `main` 分支及 `app.py` 作為入口。更新程式後須讓平台完成重新部署及依賴安裝；如平台未更新，可在管理介面重新啟動 App。

必須保留 `pdf_export.py`、`fonts/NotoSansHK-VF.ttf` 及 `fonts/OFL.txt`。PDF 直接讀取隨儲存庫提供的字型，不需要在匯出時連接 GitHub 下載。

## PDF 故障修正

原版 `FireflySung.ttf` 下載網址回傳 `HTTP Error 404: Not Found`，首次匯出 PDF 因而中斷。現改用隨附的 Noto Sans HK 繁體中文字型，並加入失敗提示。字型路徑以程式檔位置為準，不依賴啟動時的工作目錄。

PDF 在記憶體內產生；下載按鈕於一般 Streamlit 重新執行後仍會保留。新增工項後會清除舊 PDF，請再按「產生正式 PDF」匯出最新版本。手機相片會校正 EXIF 方向，並等比例縮入固定相框，避免直相超出 A4 頁面。

## 現有限制

工項紀錄及已產生 PDF **只暫存於本次瀏覽器連線**，沒有永久資料庫。重新整理、連線重建或服務重啟後可能消失。離開前請先下載 PDF；本次修正沒有新增永久保存功能。

VO 編號及項目名稱沿用原版固定值。若需更改，可修改 `pdf_export.py` 的 `VO_NUMBER` 及 `WORK_DESCRIPTION`。目前不提供 3×2 排版選項或直接拍照按鈕；手機可透過檔案上傳介面選擇相片。

## 測試

```bash
python -m unittest discover -s tests -v
```

測試使用合成相片，涵蓋中文 PDF、奇偶筆数分頁、未完工、損壞相片、EXIF 方向、缺少字型及下載資料跨 rerun 保留，不寫入使用者工程資料。

## 字型來源與授權

隨附字型來源：[Noto Sans CJK 官方香港繁體字型](https://github.com/notofonts/noto-cjk/blob/main/Sans/Variable/TTF/Subset/NotoSansHK-VF.ttf)。原始字型採 SIL Open Font License 1.1；授權全文隨附於 `fonts/OFL.txt`。
