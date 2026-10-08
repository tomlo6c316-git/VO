import streamlit as st
from PIL import Image

# 初始化暫存，用來儲存多個 VO 項目
if 'vo_list' not in st.session_state:
    st.session_state.vo_list = []

st.set_page_config(page_title="VO 施工對照表系統", layout="centered")
st.title("📋 工程變更 (VO) 自動排版")

# ==========================================
# 1. 全域設定區 (排版選擇)
# ==========================================
st.sidebar.header("⚙️ 匯出排版設定")
layout_style = st.sidebar.radio(
    "選擇 PDF 每頁顯示數量：",
    ("1頁 2項 (2x2 排版)", "1頁 3項 (3x2 排版)")
)
st.sidebar.caption("💡 2x2 照片較大，適合細部特寫；3x2 適合大量工項快速瀏覽。")

# ==========================================
# 2. 新增工項區 (手機端操作)
# ==========================================
st.subheader("➕ 新增工項紀錄")
with st.form("add_vo_form", clear_on_submit=True):
    vo_num = st.text_input("VO 編號", placeholder="例：VO-001")
    task_desc = st.text_input("工項描述", placeholder="例：大堂天花板封板")
    
    col1, col2 = st.columns(2)
    with col1:
        before_img = st.file_uploader("上傳 事前 (Before)", type=["jpg", "jpeg", "png"])
    with col2:
        after_img = st.file_uploader("上傳 完成 (After) - 未完工請留空", type=["jpg", "jpeg", "png"])
        
    submitted = st.form_submit_button("💾 儲存此筆紀錄")
    if submitted and vo_num:
        # 將資料存入暫存清單
        st.session_state.vo_list.append({
            "vo_num": vo_num,
            "desc": task_desc,
            "before": before_img,
            "after": after_img
        })
        st.success(f"已加入 {vo_num}！目前共 {len(st.session_state.vo_list)} 筆。")

# ==========================================
# 3. 工整的預覽區 (模擬 PDF 表格)
# ==========================================
st.divider()
st.subheader(f"👁️ 預覽 ({layout_style})")

if len(st.session_state.vo_list) == 0:
    st.info("尚無資料，請在上方新增。")
else:
    # 這裡我們用 Streamlit 的 container 和自訂 CSS 來模擬「工整的表格」
    for index, item in enumerate(st.session_state.vo_list):
        # 標題列
        st.markdown(f"**{item['vo_num']} : {item['desc']}**")
        
        # 圖片對照列 (強迫對齊)
        img_col1, img_col2 = st.columns(2)
        
        with img_col1:
            if item['before']:
                img_b = Image.open(item['before'])
                st.image(img_b, caption="事前 (Before)", use_column_width=True)
            else:
                st.warning("缺事前照片")
                
        with img_col2:
            if item['after']:
                img_a = Image.open(item['after'])
                st.image(img_a, caption="完成 (After)", use_column_width=True)
            else:
                # 嚴格留空：顯示一個固定高度的灰色佔位框
                st.markdown(
                    """
                    <div style="border: 2px dashed #ccc; border-radius: 5px; height: 150px; 
                                display: flex; align-items: center; justify-content: center; color: #888;">
                        🚧 未完成 (保留空位)
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
        st.markdown("---") # 分隔線

# ==========================================
# 4. 匯出按鈕
# ==========================================
# ==========================================
# 4. 真正產生並匯出 PDF
# ==========================================
import urllib.request
import os
from fpdf import FPDF
import io

if st.button("📄 產生正式 PDF", type="primary"):
    if len(st.session_state.vo_list) == 0:
        st.error("請先新增至少一筆工項紀錄！")
    else:
        with st.spinner("PDF 產生中，這可能需要幾秒鐘..."):
            try:
                # 1. 確保雲端主機有中文字型 (避免亂碼)
                font_path = "fireflysung.ttf"
                if not os.path.exists(font_path):
                    # 如果沒有字型，自動下載開源中文字型
                    font_url = "https://github.com/hoishing/open-chinese-fonts/raw/master/fireflysung.ttf"
                    urllib.request.urlretrieve(font_url, font_path)

                # 2. 初始化 A4 PDF (寬210mm x 高297mm)
                pdf = FPDF(orientation="P", unit="mm", format="A4")
                pdf.add_font("Chinese", "", font_path, uni=True)
                
                # 計算排版尺寸
                items_per_page = 2 if "2x2" in layout_style else 3
                row_height = 125 if items_per_page == 2 else 80
                img_w = 85  # 照片寬度
                img_h = row_height - 15 # 照片高度
                
                for i, item in enumerate(st.session_state.vo_list):
                    # 每達到指定數量，自動換新頁並加上標題
                    if i % items_per_page == 0:
                        pdf.add_page()
                        pdf.set_font("Chinese", size=16)
                        pdf.cell(0, 12, "工程變更 (VO) 施工前後對照表", ln=1, align="C")
                        pdf.ln(5) # 加上一點間距

                    # 寫入 VO 編號與工項描述
                    pdf.set_font("Chinese", size=12)
                    pdf.cell(0, 10, f"{item['vo_num']} : {item['desc']}", ln=1)
                    
                    y_img = pdf.get_y() # 記住當前高度座標
                    
                    # 處理左側：事前照片 (Before)
                    if item['before']:
                        img_b = Image.open(item['before'])
                        # fpdf2 會自動等比例縮放圖片放入框內
                        pdf.image(img_b, x=15, y=y_img, w=img_w, h=img_h, keep_aspect_ratio=True)
                    else:
                        pdf.rect(15, y_img, img_w, img_h)
                        pdf.text(15 + img_w/2 - 15, y_img + img_h/2, "無事前照片")

                    # 處理右側：完成照片 (After)
                    if item['after']:
                        img_a = Image.open(item['after'])
                        pdf.image(img_a, x=110, y=y_img, w=img_w, h=img_h, keep_aspect_ratio=True)
                    else:
                        # 未完成：畫一個灰色框並標示留空
                        pdf.set_draw_color(150, 150, 150)
                        pdf.rect(110, y_img, img_w, img_h)
                        pdf.set_text_color(150, 150, 150)
                        pdf.text(110 + img_w/2 - 20, y_img + img_h/2, "未完成 (留空)")
                        pdf.set_draw_color(0, 0, 0)
                        pdf.set_text_color(0, 0, 0)
                    
                    # 將座標往下推，準備畫下一列
                    pdf.set_y(y_img + img_h + 10)

                # 3. 輸出成位元組並觸發 Streamlit 下載
                pdf_bytes = pdf.output()
                
                st.success("✅ PDF 生成成功！請點擊下方按鈕下載。")
                st.download_button(
                    label="⬇️ 點擊下載 PDF 檔案",
                    data=bytes(pdf_bytes),
                    file_name="VO_Report_對照表.pdf",
                    mime="application/pdf",
                    type="primary"
                )

            except Exception as e:
                st.error(f"生成 PDF 時發生錯誤: {e}")