import streamlit as st
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
if st.button("📄 產生正式 PDF"):
    if len(st.session_state.vo_records) == 0:
        st.error("請先新增至少一筆工項紀錄！")
    else:
        st.success("🔄 正在產生 PDF...")
        
        # 👇 這裡接續你原本的 FPDF 程式碼
        # 注意：因為圖片現在是 Bytes 格式，放入 FPDF 時需使用 io.BytesIO()
        # 例如：pdf.image(io.BytesIO(record["before_img"]), x, y, w, h)
