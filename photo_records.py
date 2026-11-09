"""批量前後相：全批驗證成功才回傳更新，避免半批寫入或覆蓋。"""

from pdf_export import prepare_photo

MAX_BATCH_PHOTOS = 50


def _validate_batch(uploads: list[tuple[str, bytes]]) -> None:
    if not uploads:
        raise ValueError("請先從相簿選取至少一張相片。")
    if len(uploads) > MAX_BATCH_PHOTOS:
        raise ValueError(f"每批最多 {MAX_BATCH_PHOTOS} 張相片，請分批加入。")


def _prepare_batch(uploads: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    _validate_batch(uploads)
    prepared = []
    for position, (name, data) in enumerate(uploads, 1):
        try:
            photo = prepare_photo(data)
        except ValueError as exc:
            raise ValueError(f"第 {position} 張（{name}）無法讀取，請移除或改用 JPG／PNG。") from exc
        prepared.append((name, photo))
    return prepared


def add_before_batch(records: list[dict], uploads: list[tuple[str, bytes]]) -> list[dict]:
    """保留回傳清單的順序；每張事前相新增一筆工項。"""
    prepared = _prepare_batch(uploads)
    additions = [
        {"before_img": photo, "after_img": None, "before_name": name}
        for name, photo in prepared
    ]
    return [*records, *additions]


def attach_after_batch(
    records: list[dict], uploads: list[tuple[str, bytes]], targets: list[int | None],
) -> list[dict]:
    """targets 為零起算工項索引；只補缺失完成相，不暗中覆蓋。"""
    _validate_batch(uploads)
    if len(uploads) != len(targets):
        raise ValueError("每張事後相都必須指定一個配對工項。")
    if any(type(index) is not int or not 0 <= index < len(records) for index in targets):
        raise ValueError("請為每張事後相選擇有效的配對工項。")
    if len(set(targets)) != len(targets):
        raise ValueError("同一工項不能配對多張事後相，請檢查配對選擇。")
    for index in targets:
        if records[index].get("after_img"):
            raise ValueError(f"第 {index + 1} 項已有完成相片，本次操作不會覆蓋。")
    prepared = _prepare_batch(uploads)
    updated = [dict(record) for record in records]
    for index, (name, photo) in zip(targets, prepared):
        updated[index]["after_img"] = photo
        updated[index]["after_name"] = name
    return updated
