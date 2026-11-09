import logging

import streamlit as st

from pdf_export import (
    VO_NUMBER,
    WORK_DESCRIPTION,
    build_pdf,
    prepare_logo,
    prepare_photo,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="VO 施工對照表系統")

# Session State 只保留同一瀏覽器連線內的資料，並非永久儲存。
if "vo_records" not in st.session_state:
    st.session_state.vo_records = []
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

st.title("VO 施工對照表系統")
st.caption("紀錄暫存於本次連線；離開或重新整理網頁前，請先下載 PDF。")

# ================= PDF 報告設定 =================
logo_data = None
settings_valid = True
with st.expander("PDF 報告設定／公司 Logo", expanded=True):
    company_name = st.text_input(
        "公司名稱", key="report_company_name", max_chars=80,
        placeholder="輸入正式公司名稱（選填）",
    )
    company_logo = st.file_uploader(
        "公司 Logo（選填）", type=["png", "jpg", "jpeg"],
        key="report_logo_upload",
        help="建議透明背景 PNG，最多 5 MB。Logo 會等比例置於 PDF 左上角。",
    )
    if company_logo is not None:
        try:
            logo_data = prepare_logo(company_logo.getvalue())
        except ValueError as exc:
            settings_valid = False
            st.error(str(exc))
        else:
            st.image(logo_data, caption="公司 Logo 預覽", width=160)
    vo_number = st.text_input(
        "工作指示編號（VO No.）", value=VO_NUMBER,
        key="report_vo_number", max_chars=60,
    )
    work_description = st.text_area(
        "項目名稱／工程內容", value=WORK_DESCRIPTION,
        key="report_work_description", max_chars=240, height=90,
    )
    st.caption("Logo 與報告資料只用於本次 PDF，未設永久保存。")

# 改動品牌或報告資料後，不讓舊 PDF 以新設定的名義被下載。
pdf_signature = (company_name, vo_number, work_description, logo_data)
if st.session_state.get("pdf_signature") != pdf_signature or not settings_valid:
    st.session_state.pdf_data = None
    st.session_state.pdf_signature = pdf_signature

# ================= 相片上傳區塊 =================
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
    elif not settings_valid:
        st.error("請先修正公司 Logo 檔案，再產生 PDF。")
    else:
        st.session_state.pdf_data = None
        try:
            with st.spinner("正在產生 PDF，請稍候..."):
                st.session_state.pdf_data = build_pdf(
                    st.session_state.vo_records,
                    company_name=company_name,
                    logo_data=logo_data,
                    vo_number=vo_number,
                    work_description=work_description,
                )
        except (FileNotFoundError, ValueError) as exc:
            st.error(str(exc))
        except Exception:
            logger.exception("VO PDF generation failed")
            st.error("PDF 產生失敗，請查看部署平台日誌，並確認已安裝 requirements.txt。")
        else:
            st.success("PDF 已產生，請按下方按鈕下載。")

if st.session_state.pdf_data:
    st.download_button(
        label="下載正式 PDF",
        data=st.session_state.pdf_data,
        file_name="VO_Photographic_Record.pdf",
        mime="application/pdf",
        on_click="ignore",
    )
