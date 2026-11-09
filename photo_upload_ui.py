"""Streamlit 批量上傳介面；圖片选择器不設定相機 capture。"""

import hashlib

import streamlit as st

from photo_records import MAX_BATCH_PHOTOS, add_before_batch, attach_after_batch


def _save_batch(records: list[dict], generation_key: str, message: str) -> None:
    st.session_state.vo_records = records
    st.session_state.pdf_data = None
    st.session_state[generation_key] += 1
    st.session_state["photo_notice"] = message
    # 以新 key 重建 uploader，成功後清空選取，避免再次點擊重複新增。
    st.rerun()


def _show_photo(data: bytes, caption: str) -> None:
    try:
        st.image(data, caption=caption, width=160)
    except Exception:
        st.warning(f"{caption}：無法預覽，儲存時會驗證相片。")


def render_photo_uploads() -> None:
    for key in ("before_upload_generation", "after_upload_generation"):
        if key not in st.session_state:
            st.session_state[key] = 0
    if notice := st.session_state.pop("photo_notice", None):
        st.success(notice)

    st.subheader("批量加入前後相片")
    st.caption(
        "選擇相片可一次多選；如手機只允許單選，可多次按 Browse files 累加。"
        "圖片入口由手機／瀏覽器決定；如顯示來源選單，請選「相片／相簿」。"
    )
    before_tab, after_tab = st.tabs(["1. 新增事前相", "2. 補上事後相"])

    with before_tab:
        generation = st.session_state.before_upload_generation
        uploads = st.file_uploader(
            "從相簿選取事前相片（可多選）", type="image/*",
            accept_multiple_files=True, key=f"before_upload_{generation}",
            max_upload_size=20,
            help=f"每批最多 {MAX_BATCH_PHOTOS} 張、每張最多 20 MB。建議 JPG／PNG。每張新增一筆工項。",
        )
        valid_count = len(uploads) <= MAX_BATCH_PHOTOS
        if not valid_count:
            st.error(f"每批最多 {MAX_BATCH_PHOTOS} 張，請移除多出的相片或分批加入。")
        if uploads and valid_count:
            st.info(f"已選 {len(uploads)} 張；將依以下清單順序新增工項，完成相可稍後補上。")
            with st.expander("檢查事前相清單與縮圖"):
                start = len(st.session_state.vo_records)
                for position, photo in enumerate(uploads, 1):
                    st.text(f"第 {start + position} 項 ← {photo.name}")
                    _show_photo(photo.getvalue(), photo.name)
        if st.button(
            "儲存事前相（批量新增）", key="save_before_batch",
            disabled=not uploads or not valid_count,
        ):
            try:
                records = add_before_batch(
                    st.session_state.vo_records,
                    [(photo.name, photo.getvalue()) for photo in uploads],
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                _save_batch(records, "before_upload_generation", f"已新增 {len(uploads)} 項事前相紀錄。")

    with after_tab:
        generation = st.session_state.after_upload_generation
        pending = [
            index for index, record in enumerate(st.session_state.vo_records)
            if not record.get("after_img")
        ]
        if not st.session_state.vo_records:
            st.info("請先在「新增事前相」加入工項，再補上事後相。")
        elif not pending:
            st.info("所有工項已有完成相片；不會覆蓋原有相片。")
        uploads = st.file_uploader(
            "從相簿選取事後相片（可多選）", type="image/*",
            accept_multiple_files=True, key=f"after_upload_{generation}",
            max_upload_size=20, disabled=not pending,
            help=f"每批最多 {MAX_BATCH_PHOTOS} 張、每張最多 20 MB。儲存前請核對每張相片配對的工項。",
        )
        valid_count = len(uploads) <= MAX_BATCH_PHOTOS and len(uploads) <= len(pending)
        if uploads and not valid_count:
            st.error(f"本批超出可配對數量：待補工項 {len(pending)} 項，每批上限 {MAX_BATCH_PHOTOS} 張。")
        targets = []
        confirmed = False
        if uploads and valid_count:
            st.warning("暫按清單順序建議配對，並非自動辨識。請逐張核對縮圖，可更改配對工項。")
            target_labels = {
                index: f"第 {index + 1} 項 — {st.session_state.vo_records[index].get('before_name', '事前相片')}"
                for index in pending
            }

            def format_target(index):
                if index is None:
                    return "請選擇工項"
                return target_labels[index]

            options = [None, *pending]
            for position, photo in enumerate(uploads):
                with st.container(border=True):
                    st.text(f"事後相 {position + 1}：{photo.name}")
                    target = st.selectbox(
                        "配對到哪一項？", options=options,
                        index=position + 1, format_func=format_target,
                        key=f"after_target_{generation}_{photo.file_id}",
                    )
                    targets.append(target)
                    left, right = st.columns(2)
                    with left:
                        if target is not None:
                            _show_photo(st.session_state.vo_records[target]["before_img"], f"第 {target + 1} 項事前")
                    with right:
                        _show_photo(photo.getvalue(), "本張事後")
            if len(set(targets)) != len(targets):
                st.error("同一工項被配對多次，請更改配對。")
            mapping_key = hashlib.sha256(
                repr([(photo.file_id, target) for photo, target in zip(uploads, targets)]).encode()
            ).hexdigest()[:16]
            confirmed = st.checkbox(
                "我已核對所有前後相配對", key=f"confirm_after_batch_{generation}_{mapping_key}",
            )
        if st.button(
            "儲存事後相（批量配對）", key="save_after_batch",
            disabled=not uploads or not valid_count or not confirmed,
        ):
            try:
                records = attach_after_batch(
                    st.session_state.vo_records,
                    [(photo.name, photo.getvalue()) for photo in uploads], targets,
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                _save_batch(records, "after_upload_generation", f"已為 {len(uploads)} 項工項補上事後相。")
