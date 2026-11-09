"""VO PDF 匯出：本地中文字型、記憶體圖片及每頁兩項 A4 排版。"""

import io
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageOps, UnidentifiedImageError

FONT_PATH = Path(__file__).resolve().parent / "fonts" / "NotoSansHK-VF.ttf"
VO_NUMBER = "OBLV40777"
WORK_DESCRIPTION = "L08 Sample Floor 拆石膏板 Furring"


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


def _draw_photo(pdf: FPDF, data: bytes, x: float, y: float) -> None:
    """等比例置中於 90×86 mm 框內；直相不裁切、不拉長。"""
    prepared = prepare_photo(data)
    with Image.open(io.BytesIO(prepared)) as photo:
        width, height = photo.size
    scale = min(90 / width, 86 / height)
    draw_width, draw_height = width * scale, height * scale
    pdf.image(
        io.BytesIO(prepared),
        x=x + (90 - draw_width) / 2,
        y=y + (86 - draw_height) / 2,
        w=draw_width,
        h=draw_height,
    )


def build_pdf(records: list[dict], font_path: Path = FONT_PATH) -> bytes:
    if not records:
        raise ValueError("請先新增至少一筆工項紀錄！")
    if not Path(font_path).is_file():
        raise FileNotFoundError(
            "缺少中文字型：請確認儲存庫包含 fonts/NotoSansHK-VF.ttf，然後重新部署。"
        )

    pdf = FPDF(format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(False)
    pdf.add_font("NotoHK", fname=str(font_path))
    pdf.set_title("VO Photographic Record")

    for start in range(0, len(records), 2):
        pdf.add_page()
        pdf.set_font("NotoHK", size=17)
        pdf.set_text_color(0, 51, 102)
        pdf.set_xy(10, 10)
        pdf.cell(w=pdf.epw, h=12, text="相片紀錄 PHOTOGRAPHIC RECORD", align="C")
        pdf.set_font("NotoHK", size=11)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(10, 23)
        pdf.cell(w=pdf.epw, h=8, text=f"工作指示編號 (VO No.): {VO_NUMBER}", align="C")
        pdf.set_xy(10, 32)
        pdf.cell(w=pdf.epw, h=8, text=f"項目: {WORK_DESCRIPTION}", align="C")

        for row, record in enumerate(records[start:start + 2]):
            index = start + row + 1
            y = 45 + row * 116
            pdf.set_font("NotoHK", size=11)
            pdf.set_xy(10, y)
            pdf.cell(w=pdf.epw, h=7, text=f"第 {index} 項紀錄")
            pdf.set_xy(10, y + 8)
            pdf.cell(w=90, h=7, text="事前 (Before)", align="C")
            pdf.set_xy(110, y + 8)
            pdf.cell(w=90, h=7, text="完成 (After)", align="C")

            for key, x in (("before_img", 10), ("after_img", 110)):
                pdf.set_draw_color(190, 190, 190)
                pdf.rect(x, y + 17, 90, 86)
                data = record.get(key)
                if data:
                    try:
                        _draw_photo(pdf, data, x, y + 17)
                    except ValueError as exc:
                        label = "事前" if key == "before_img" else "完成"
                        raise ValueError(f"第 {index} 項{label}相片無法讀取，請重新上傳。") from exc
                elif key == "before_img":
                    raise ValueError(f"第 {index} 項缺少事前相片，請重新上傳。")
                else:
                    pdf.set_text_color(110, 110, 110)
                    pdf.set_xy(x, y + 55)
                    pdf.cell(w=90, h=8, text="尚未完工", align="C")
                    pdf.set_text_color(0, 0, 0)

        pdf.set_xy(10, 280)
        pdf.set_font("NotoHK", size=9)
        pdf.cell(w=pdf.epw, h=6, text=f"第 {pdf.page_no()} 頁", align="C")

    # fpdf2 直接回傳 bytearray，不建立／刪除暫存 PDF 或相片檔。
    return bytes(pdf.output())
