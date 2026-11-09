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
        
        # 【修正重點 1】：必須在處理相片迴圈之前，先建立 pdf 物件
        from fpdf import FPDF
        pdf = FPDF()
        
        # 💡 如果你有設定中文字型 (例如 FireflySung)，請在這裡載入：
        # pdf.add_font("Firefly", "", "你的中文字型檔徑.ttf", uni=True)
        # pdf.set_font("Firefly", size=12)
        
        pdf.add_page() # 新增 PDF 的第一頁
        
        # 【修正重點 2】：接著才開始執行讀取與貼上圖片的迴圈
        for idx, record in enumerate(st.session_state.vo_records):
            
            import tempfile
            import os
            
            # 1. 將「事前相片」寫入暫存檔
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_before:
                tmp_before.write(record["before_img"])
                tmp_before_path = tmp_before.name
            
            # 2. 將「完成相片」寫入暫存檔
            tmp_after_path = None
            if record["after_img"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_after:
                    tmp_after.write(record["after_img"])
                    tmp_after_path = tmp_after.name
            
            # 3. 讓 pdf 物件讀取暫存檔 (注意這裡使用的是剛建立好的 pdf 變數)
            pdf.image(tmp_before_path, x=10, y=30, w=90)
            if tmp_after_path:
                pdf.image(tmp_after_path, x=110, y=30, w=90)
                
            # 4. 用完立刻刪除暫存檔
            os.remove(tmp_before_path)
            if tmp_after_path:
                os.remove(tmp_after_path)
                
        # 輸出並提供下載按鈕
        # ... 接續你的 pdf.output() 或 download_button 程式碼 ...
