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
        st.success("🔄 正在產生包含排版的 PDF，請稍候...")
        
        from fpdf import FPDF
        import tempfile
        import os
        import urllib.request
        
        # 1. 確保環境中有中文字型 (如果沒有，自動從可靠來源下載)
        font_path = "FireflySung.ttf"
        if not os.path.exists(font_path):
            st.info("首次產生 PDF：正在下載中文字型檔，請稍候...")
            font_url = "https://github.com/matomo-org/travis-scripts/raw/master/fonts/FireflySung.ttf"
            urllib.request.urlretrieve(font_url, font_path)

        # 2. 初始化 PDF 與字型
        pdf = FPDF()
        # 加入支援 Unicode 的中文字型
        pdf.add_font("Firefly", "", font_path, uni=True) 
        
        # 3. 處理每一筆相片紀錄，加入文字與排版
        for idx, record in enumerate(st.session_state.vo_records):
            pdf.add_page() 
            
            # --- 【排版設計：頁面抬頭】 ---
            pdf.set_font("Firefly", size=18)
            pdf.set_text_color(0, 51, 102) # 深藍色字體
            pdf.cell(200, 15, txt="相片紀錄 PHOTOGRAPHIC RECORD", ln=True, align='C')
            
            # --- 【排版設計：工項與編號資料】 ---
            pdf.set_font("Firefly", size=12)
            pdf.set_text_color(0, 0, 0) # 黑色字體
            pdf.cell(200, 8, txt="工作指示編號 (VO No.): OBLV40777", ln=True, align='C')
            pdf.cell(200, 8, txt=f"項目: L08 Sample Floor 拆石膏板 Furring - 紀錄 {idx+1}", ln=True, align='C')
            pdf.ln(10) # 換行留白，準備放圖片
            
            # --- 【相片處理】 ---
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_before:
                tmp_before.write(record["before_img"])
                tmp_before_path = tmp_before.name
            
            tmp_after_path = None
            if record["after_img"]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_after:
                    tmp_after.write(record["after_img"])
                    tmp_after_path = tmp_after.name
            
            # --- 【排版設計：插入圖片與圖片標籤】 ---
            pdf.set_font("Firefly", size=14)
            
            # 左側：事前
            pdf.text(x=35, y=60, txt="事前 (Before)")
            pdf.image(tmp_before_path, x=10, y=65, w=90)
            
            # 右側：事後
            if tmp_after_path:
                pdf.text(x=135, y=60, txt="事後 (After)")
                pdf.image(tmp_after_path, x=110, y=65, w=90)
            else:
                pdf.set_text_color(255, 0, 0) # 紅字提示未完工
                pdf.text(x=125, y=60, txt="事後 (After) - 尚未完工")
                pdf.set_text_color(0, 0, 0) # 恢復黑字
                
            # 清理圖片暫存檔
            os.remove(tmp_before_path)
            if tmp_after_path:
                os.remove(tmp_after_path)
                
        # 4. 匯出 PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name) 
            with open(tmp_pdf.name, "rb") as f:
                pdf_data = f.read()
        os.remove(tmp_pdf.name)

        # 5. 顯示下載按鈕
        st.download_button(
            label="✅ 產生成功！點擊下載排版好的 PDF",
            data=pdf_data,
            file_name="VO_Photographic_Record.pdf",
            mime="application/pdf"
        )
