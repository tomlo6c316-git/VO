import logging

import streamlit as st

from pdf_export import build_pdf, prepare_photo

logger = logging.getLogger(__name__)

st.set_page_config(page_title="VO 施工對照表系統")

# Session State 只保留同一瀏覽器連線內的資料，並非永久儲存。
if "vo_records" not in st.session_state:
    st.session_state.vo_records = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

st.title("VO 施工對照表系統")
st.caption("紀錄暫存於本次連線；離開或重新整理網頁前，請先下載 PDF。")

# ================= 上傳區塊 =================
before_photo = st.file_uploader("上傳 事前 (Before)", type=["png", "jpg", "jpeg"])
after_photo = st.file_uploader(
    "上傳 完成 (After) - 未完工請留空", type=["png", "jpg", "jpeg"]
)

if st.button("儲存此筆紀錄"):
    if before_photo is None:
        st.error("請至少上傳一張「事前 (Before)」相片。")
    else:
        try:
            # 先驗證及校正手機 EXIF 方向，再儲存獨立的圖片 bytes。
            record = {
                "before_img": prepare_photo(before_photo.getvalue()),
                "after_img": (
                    prepare_photo(after_photo.getvalue())
                    if after_photo is not None
                    else None
                ),
            }
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state.vo_records.append(record)
            # 新增工項後，舊 PDF 不再代表最新紀錄。
            st.session_state.pdf_data = None
            st.success(f"第 {len(st.session_state.vo_records)} 筆紀錄已成功儲存！")

st.divider()
st.markdown("### 預覽（PDF 每頁 2 項，2×2 排版）")

if not st.session_state.vo_records:
    st.info("尚無資料，請在上方新增。")
else:
    for idx, record in enumerate(st.session_state.vo_records):
        st.write(f"**第 {idx + 1} 項紀錄**")
        col1, col2 = st.columns(2)
        with col1:
            try:
                st.image(record["before_img"], caption="事前 (Before)", width="stretch")
            except Exception:
                st.error(f"第 {idx + 1} 項事前相片無法預覽，請重新上傳。")
        with col2:
            if record.get("after_img"):
                try:
                    st.image(record["after_img"], caption="完成 (After)", width="stretch")
                except Exception:
                    st.error(f"第 {idx + 1} 項完成相片無法預覽，請重新上傳。")
            else:
                st.info("尚未完工（完成相片留空）")

st.divider()

# ================= 產生 PDF 區塊 =================
if st.button("產生正式 PDF"):
    if not st.session_state.vo_records:
        st.error("請先新增至少一筆工項紀錄！")
    else:
        st.session_state.pdf_data = None
        try:
            with st.spinner("正在產生 PDF，請稍候..."):
                st.session_state.pdf_data = build_pdf(st.session_state.vo_records)
        except (FileNotFoundError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            logger.exception("VO PDF generation failed")
            st.error("PDF 產生失敗，請查看部署平台日誌，並確認已安裝 requirements.txt。")
        else:
            st.success("PDF 已產生，請按下方按鈕下載。")

# 放在產生按鈕的 if 區塊外，重新執行時仍保留下載入口。
if st.session_state.pdf_data:
    st.download_button(
        label="下載正式 PDF",
        data=st.session_state.pdf_data,
        file_name="VO_Photographic_Record.pdf",
        mime="application/pdf",
        on_click="ignore",
    )
