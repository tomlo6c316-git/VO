# 工程變更 (VO) 自動排版系統

以 Streamlit 上傳工程 VO 事前／完成相片，匯出繁體中文 A4 PDF。完成相片可留空；PDF 每頁放兩筆紀錄，左邊事前、右邊完成，形成 2×2 排版。

## 批量加入事前／事後相片

在「1. 新增事前相」一次選取多張圖片，核對清單後按「儲存事前相（批量新增）」。每張圖片新增一筆工項，依畫面清單順序排列；不是保證依手機點選次序。單張同樣適用。每批最多 50 張、每張最多 20 MB，建議使用 JPG／PNG。不支援的圖片會提示轉換格式，不會部分儲存該批資料。

在「2. 補上事後相」另外多選完成圖片，逐張檢查相應事前縮圖，並選擇要配對的工項。預設按待補工項清單順序建議配對，並非自動辨識前後相。核對後勾選確認，再按「儲存事後相（批量配對）」。同一工項不可配對兩張完成相，已附完成相的工項亦不會被默默覆蓋。修改清單或配對後需重新勾選確認。

成功儲存後會清空該批選取並清除舊 PDF；可繼續選下一批，再重新產生 PDF。未儲存的選取只是草稿，不會加入正式紀錄。

## 手機相簿入口

前後相上傳使用 `type="image/*"` 及多選，不加強制啟用相機的 capture，讓支援的手机瀏覽器提供圖片／相簿入口。實際預設畫面與起始相簿由手機系統及瀏覽器決定，網站不能強制設定。如果出現來源選單，請選「相片／相簿」；App 內建瀏覽器若只可單選，可改用手機 Chrome／Safari，或多次按 Browse files 累加圖片後一次儲存。這些方法仍視裝置支援而定。

此設定採 [Streamlit 官方 MIME 與多檔上傳 API](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)。[MDN 檔案選擇器說明](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/input/file) 說明 accept 為圖片格式提示、capture 為相機選項，實際介面可因瀏覽器與作業系統不同；亦有 [Streamlit Android 多選問題紀錄](https://github.com/streamlit/streamlit/issues/13627)。

## 公司 Logo 與正式報告版面

在 app 的「PDF 報告設定／公司 Logo」上傳正式公司 Logo，並輸入公司名稱、VO 編號及工程內容。Logo 支援 PNG/JPG，大小最多 5 MB；建議使用透明背景 PNG。Logo 保留原有比例及透明背景，不裁切、不拉伸。未提供 Logo 時，不會使用假標誌或其他公司的圖案。

PDF 採 A4 直向、12 mm 頁邊距，使用深藍品牌抬頭及淡灰 VO 資料表。每筆工項有完整外框、中央前後相分隔線、淡灰標題列及清楚紀錄編號；未附完成相片的位置會顯示「尚未完工」。相片保持完整比例，每頁重複抬頭，頁尾提供目前頁碼與總頁數。

文字會完整換行，必要時有限度縮小字級；超出可容納範圍時會提示縮短內容，不會靜默刪掉報告資料。更改公司名稱、Logo 或工程資料後，舊 PDF 會失效，請重新產生。Logo 及報告設定仍只保留於本次瀏覽器連線。

## 執行與部署

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Streamlit Community Cloud 請選擇此儲存庫的 `main` 分支及 `app.py` 作為入口。更新程式後須讓平台完成重新部署及依賴安裝；如平台未更新，可在管理介面重新啟動 App。

必須保留 `pdf_export.py`、`photo_records.py`、`photo_upload_ui.py`、`fonts/NotoSansHK-Regular.ttf`、`fonts/NotoSansHK-SemiBold.ttf` 及 `fonts/OFL.txt`。PDF 直接讀取隨儲存庫提供的字型，不需要在匯出時連接 GitHub 下載。兩份字型已預先固定為常規 400 與半粗 600 字重，匯出時毋須重新計算變動字型。

## PDF 故障修正

原版 `FireflySung.ttf` 下載網址回傳 `HTTP Error 404: Not Found`，首次匯出 PDF 因而中斷。現改用隨附的 Noto Sans HK 繁體中文字型，並加入失敗提示。字型路徑以程式檔位置為準，不依賴啟動時的工作目錄。

PDF 在記憶體內產生；下載按鈕於一般 Streamlit 重新執行後仍會保留。新增工項後會清除舊 PDF，請再按「產生正式 PDF」匯出最新版本。手機相片會校正 EXIF 方向，並等比例縮入固定相框，避免直相超出 A4 頁面。

## 現有限制

工項紀錄及已產生 PDF **只暫存於本次瀏覽器連線**，沒有永久資料庫。重新整理、連線重建或服務重啟後可能消失。離開前請先下載 PDF；本次修正沒有新增永久保存功能。

VO 編號及項目名稱預設沿用原版值，可在 app 報告設定修改。亦可修改 `pdf_export.py` 的 `VO_NUMBER` 及 `WORK_DESCRIPTION` 更改預設。每份報告使用一組公司及工程資料。目前不提供 3×2 排版選項或直接拍照按鈕；手機可透過檔案上傳介面選擇相片。

## 測試

```bash
python -m unittest discover -s tests -v
```

測試使用合成相片，涵蓋中文 PDF、奇偶筆數分頁、未完工、損壞相片、EXIF 方向、缺少字型、Logo 透明度／比例、長文字及設定改動後舊 PDF 失效，不寫入使用者工程資料。

## 字型來源與授權

隨附字型以 [Noto Sans CJK 官方香港繁體變動字型](https://github.com/notofonts/noto-cjk/blob/main/Sans/Variable/TTF/Subset/NotoSansHK-VF.ttf) 為來源，以 fontTools 預先建立 400／600 字重的靜態版本，保留字型內的原始版權資訊。原始字型與隨附靜態版本採 SIL Open Font License 1.1；授權全文隨附於 `fonts/OFL.txt`。
