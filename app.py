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
if st.button("📄 產生正式 PDF", type="primary"):
    # 這裡會觸發後台的 FPDF 程式
    st.success(f"正在以「{layout_style}」格式產出 PDF...")
    # 實際開發時，這裡會呼叫 def generate_pdf(data_list, layout_style)