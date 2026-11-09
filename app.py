import streamlit as st
import tempfile
import os
import io

# 1. 初始化 Session State (確保跨頁面/按鈕點擊時資料不會被清空)
if 'vo_records' not in st.session_state:
    st.session_state.vo_records = []

# (此處保留你原有的設定，如中文字型下載等)
st.title("VO 施工對照表系統")

# ================= 上傳區塊 =================
before_photo = st.file_uploader("上傳 事前 (Before)", type=['png', 'jpg', 'jpeg'])
after_photo = st.file_uploader("上傳 完成 (After) - 未完工請留空", type=['png', 'jpg', 'jpeg'])

if st.button("💾 儲存此筆紀錄"):
    if before_photo is not None:
        # 【關鍵修正】：使用 .getvalue() 將圖片轉成二進位位元組，避免 Streamlit 刷新後遺失檔案實體
        record = {
            "before_img": before_photo.getvalue(),
            "after_img": after_photo.getvalue() if after_photo is not None else None
        }
        st.session_state.vo_records.append(record)
        st.success(f"✅ 第 {len(st.session_state.vo_records)} 筆紀錄已成功儲存！請在下方預覽。")
    else:
        st.error("⚠️ 請至少上傳一張「事前 (Before)」相片。")

st.divider()

# ================= 預覽區塊 =================
st.markdown("### 👁️ 預覽 (1頁 2項 (2x2 排版))")

if len(st.session_state.vo_records) == 0:
    st.info("尚無資料，請在上方新增。")
else:
    for idx, record in enumerate(st.session_state.vo_records):
        st.write(f"**第 {idx + 1} 項紀錄**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(record["before_img"], caption="事前 (Before)", use_container_width=True)
            
        with col2:
            if record["after_img"]:
                st.image(record["after_img"], caption="完成 (After)", use_container_width=True)
            else:
                st.info("未完工 (自動留空)")

st.divider()

# ================= 產生 PDF 區塊 =================

# ================= 產生 PDF 區塊 =================
if st.button("📄 產生正式 PDF"):
    if len(st.session_state.vo_records) == 0:
        st.error("請先新增至少一筆工項紀錄！")
    else:
        st.success("🔄 正在產生 PDF，請稍候...")
        
        from fpdf import FPDF
        import tempfile
        import os
        
        # 1. 初始化 PDF
        pdf = FPDF()
        
        # (如果你有中文字型，可以在這裡載入。如果沒有，請先註解掉，以免報錯)
        # pdf.add_font("Firefly", "", "FireflySung.ttf", uni=True)
        # pdf.set_font("Firefly", size=12)
        
        # 2. 處理每一筆相片紀錄
        for idx, record in enumerate(st.session_state.vo_records):
            pdf.add_page() # 每筆紀錄獨立一頁
            
            # 寫入事前相片暫存
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_before:
                tmp_before.write(record["before_img"])
                tmp_before_path = tmp_before.name
            
            # 寫入事後相片暫存 (如果有)
            tmp_after_path = None
            if record["after_img"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_after:
                    tmp_after.write(record["after_img"])
                    tmp_after_path = tmp_after.name
            
            # 將圖片貼上 PDF (x, y 座標與寬度 w 可以依照你的排版需求微調)
            # 這裡設定 Before 在左，After 在右
            pdf.image(tmp_before_path, x=10, y=30, w=90)
            if tmp_after_path:
                pdf.image(tmp_after_path, x=110, y=30, w=90)
                
            # 清理圖片暫存檔
            os.remove(tmp_before_path)
            if tmp_after_path:
                os.remove(tmp_after_path)
                
        # 3. 將完成的 PDF 匯出為暫存檔，然後讀取成位元組 (Bytes) 交給 Streamlit 下載
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)  # 輸出實體 PDF 檔案到伺服器暫存區
            
            # 讀取該實體檔案
            with open(tmp_pdf.name, "rb") as f:
                pdf_data = f.read()
                
        # 清理 PDF 暫存檔
        os.remove(tmp_pdf.name)

        # 4. 產生綠色的下載按鈕
        st.download_button(
            label="✅ 產生成功！點擊這裡下載 PDF 報告",
            data=pdf_data,
            file_name="VO_Photographic_Record.pdf",
            mime="application/pdf"
        )
