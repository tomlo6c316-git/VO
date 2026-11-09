"""VO PDF 匯出：公司品牌抬頭、精確 A4 表格及每頁兩項前後相。"""

import io
import math
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageOps, UnidentifiedImageError

FONT_PATH = Path(__file__).resolve().parent / "fonts" / "NotoSansHK-Regular.ttf"
FONT_BOLD_PATH = Path(__file__).resolve().parent / "fonts" / "NotoSansHK-SemiBold.ttf"
VO_NUMBER = "OBLV40777"
WORK_DESCRIPTION = "L08 Sample Floor 拆石膏板 Furring"
NAVY = (25, 52, 77)
GRAY = (101, 116, 130)
LIGHT_GRAY = (237, 241, 244)
WHITE = (255, 255, 255)


def prepare_photo(data: bytes) -> bytes:
    """驗證圖片、校正 EXIF 方向，輸出有大小上限的 RGB JPEG。"""
    try:
        with Image.open(io.BytesIO(data)) as source:
            photo = ImageOps.exif_transpose(source)
            photo.load()
            if "A" in photo.getbands() or "transparency" in photo.info:
                rgba = photo.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                photo = background
            else:
                photo = photo.convert("RGB")
            photo.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            photo.save(output, format="JPEG", quality=92)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("相片無法讀取，請重新上傳有效的 JPG 或 PNG 相片。") from exc


def prepare_logo(data: bytes) -> bytes:
    """只校正方向及縮放 Logo，保留透明度，不重畫或裁切標誌。"""
    if len(data) > 5 * 1024 * 1024:
        raise ValueError("公司 Logo 超過 5 MB，請上傳較小的 PNG 或 JPG 檔。")
    try:
        with Image.open(io.BytesIO(data)) as source:
            logo = ImageOps.exif_transpose(source).convert("RGBA")
            logo.load()
            logo.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            logo.save(output, format="PNG")
            return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("公司 Logo 無法讀取，請上傳有效的 PNG 或 JPG 圖片。") from exc


def _place_image(pdf: FPDF, data: bytes, x: float, y: float, w: float, h: float) -> None:
    """完整圖片以 contain 方式等比例置中，不裁切、不拉伸。"""
    with Image.open(io.BytesIO(data)) as image:
        width, height = image.size
    scale = min(w / width, h / height)
    draw_width, draw_height = width * scale, height * scale
    pdf.image(
        io.BytesIO(data), x=x + (w - draw_width) / 2,
        y=y + (h - draw_height) / 2, w=draw_width, h=draw_height,
    )


def _text_box(
    pdf: FPDF, text: str, x: float, y: float, w: float, h: float,
    size: float = 9, min_size: float = 7.5, color: tuple = NAVY,
    align: str = "L", field: str = "報告文字",
    bold: bool = False,
) -> None:
    """完整換行並有限度縮小字級；放不下時提示，不靜默截斷資料。"""
    text = str(text).strip()
    if not text:
        return
    while size >= min_size:
        pdf.set_font("NotoHK", style="B" if bold else "", size=size)
        line_height = size * 0.352778 * 1.18
        pdf.set_xy(x, y)
        lines = pdf.multi_cell(
            w=w, h=line_height, text=text, wrapmode="CHAR",
            dry_run=True, output="LINES", align=align,
        )
        if len(lines) * line_height <= h + 0.01:
            pdf.set_text_color(*color)
            pdf.set_xy(x, y + (h - len(lines) * line_height) / 2)
            pdf.multi_cell(
                w=w, h=line_height, text=text, wrapmode="CHAR",
                align=align, new_x="LEFT", new_y="NEXT",
            )
            return
        size -= 0.5
    raise ValueError(f"{field}太長，無法完整放入 PDF 欄位，請縮短內容後再產生。")


def _header(
    pdf: FPDF, company_name: str, logo_data: bytes | None,
    vo_number: str, work_description: str, record_count: int,
) -> None:
    if logo_data:
        _place_image(pdf, logo_data, 12, 12, 30, 20)
        company_x, company_w = 46, 87
    else:
        company_x, company_w = 12, 121
    _text_box(
        pdf, company_name or "工程變更紀錄", company_x, 12, company_w, 20,
        size=12, min_size=8, field="公司名稱", bold=True,
    )
    _text_box(pdf, "相片紀錄", 137, 12, 61, 10, size=19, min_size=19, align="R", bold=True)
    _text_box(
        pdf, "PHOTOGRAPHIC RECORD", 137, 23, 61, 7,
        size=8.5, min_size=8.5, align="R", color=GRAY,
    )
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.7)
    pdf.line(12, 36, 198, 36)

    # VO 資料列 9 mm，工程內容列 19 mm。長內容可完整換行。
    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.rect(12, 40, 186, 9, style="F")
    pdf.set_line_width(0.3)
    pdf.set_draw_color(*GRAY)
    pdf.rect(12, 40, 186, 28)
    pdf.line(12, 49, 198, 49)
    pdf.line(131, 40, 131, 49)
    _text_box(pdf, "VO No.", 15, 41, 22, 7, size=8.5)
    _text_box(pdf, vo_number, 38, 41, 89, 7, size=10, field="VO 編號")
    _text_box(pdf, f"工項總數  {record_count}", 134, 41, 61, 7, size=9, align="R")
    _text_box(pdf, "工程內容", 15, 51, 25, 15, size=8.5, color=GRAY)
    _text_box(
        pdf, work_description, 42, 50, 153, 17,
        size=9.5, min_size=7.5, field="工程內容",
    )


def _record_table(pdf: FPDF, record: dict, index: int, y: float) -> None:
    x, width, height = 12, 186, 96
    pdf.set_fill_color(*NAVY)
    pdf.rect(x, y, width, 7, style="F")
    _text_box(pdf, f"工項紀錄  {index:02d}", 15, y + 0.5, 100, 6, size=10, color=WHITE, bold=True)
    status = "已附完成相片" if record.get("after_img") else "完成相片待補"
    _text_box(pdf, status, 141, y + 0.5, 54, 6, size=8, color=WHITE, align="R")

    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.rect(x, y + 7, width, 8, style="F")
    _text_box(pdf, "事前 BEFORE", 15, y + 7.5, 87, 7, size=9.5, align="C")
    _text_box(pdf, "完成 AFTER", 108, y + 7.5, 87, 7, size=9.5, align="C")

    for key, photo_x in (("before_img", 15), ("after_img", 108)):
        data = record.get(key)
        if data:
            try:
                _place_image(pdf, prepare_photo(data), photo_x, y + 18, 87, 75)
            except ValueError as exc:
                label = "事前" if key == "before_img" else "完成"
                raise ValueError(f"第 {index} 項{label}相片無法讀取，請重新上傳。") from exc
        elif key == "before_img":
            raise ValueError(f"第 {index} 項缺少事前相片，請重新上傳。")
        else:
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(105, y + 15, 93, 81, style="F")
            _text_box(
                pdf, "尚未完工", 108, y + 47, 87, 12,
                size=11, color=GRAY, align="C",
            )

    # 相片繪製後補畫真正的 PDF 表格線，列／欄交接保持一致。
    pdf.set_draw_color(*GRAY)
    pdf.set_line_width(0.25)
    pdf.line(x, y + 7, x + width, y + 7)
    pdf.line(x, y + 15, x + width, y + 15)
    pdf.line(105, y + 7, 105, y + height)
    pdf.set_draw_color(*NAVY)
    pdf.set_line_width(0.45)
    pdf.rect(x, y, width, height)


def build_pdf(
    records: list[dict], font_path: Path = FONT_PATH, *,
    company_name: str = "", logo_data: bytes | None = None,
    vo_number: str = VO_NUMBER, work_description: str = WORK_DESCRIPTION,
) -> bytes:
    if not records:
        raise ValueError("請先新增至少一筆工項紀錄！")
    if not Path(font_path).is_file():
        raise FileNotFoundError(
            "缺少中文字型：請確認儲存庫包含 fonts/NotoSansHK-Regular.ttf，然後重新部署。"
        )
    bold_font_path = FONT_BOLD_PATH if Path(font_path) == FONT_PATH else Path(font_path)
    if not bold_font_path.is_file():
        raise FileNotFoundError("缺少半粗中文字型：請確認包含 fonts/NotoSansHK-SemiBold.ttf。")
    logo_data = prepare_logo(logo_data) if logo_data else None
    pdf = FPDF(format="A4")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(False)
    pdf.add_font("NotoHK", fname=str(font_path))
    pdf.add_font("NotoHK", style="B", fname=str(bold_font_path))
    pdf.set_title("VO Photographic Record")
    if company_name:
        pdf.set_author(company_name)
    page_count = math.ceil(len(records) / 2)

    for start in range(0, len(records), 2):
        pdf.add_page()
        _header(pdf, company_name, logo_data, vo_number, work_description, len(records))
        for row, record in enumerate(records[start:start + 2]):
            _record_table(pdf, record, start + row + 1, 72 + row * 102)
        pdf.set_draw_color(*GRAY)
        pdf.set_line_width(0.2)
        pdf.line(12, 278, 198, 278)
        _text_box(pdf, "VO PHOTOGRAPHIC RECORD", 12, 280, 110, 5, size=7.5, color=GRAY)
        _text_box(
            pdf, f"第 {pdf.page_no()} / {page_count} 頁", 138, 280, 60, 5,
            size=8, align="R", color=GRAY,
        )

    return bytes(pdf.output())
