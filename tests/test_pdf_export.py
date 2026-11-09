import io
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

from pdf_export import build_pdf, prepare_photo

ROOT = Path(__file__).resolve().parents[1]


def photo_bytes(size=(600, 400), image_format="JPEG", mode="RGB", exif=None):
    output = io.BytesIO()
    image = Image.new(mode, size, "white")
    kwargs = {"exif": exif} if exif is not None else {}
    image.save(output, image_format, **kwargs)
    return output.getvalue()


class PDFExportTests(unittest.TestCase):
    def test_valid_pdf_without_network_and_two_records_per_page(self):
        for count in (1, 2, 3, 4):
            with self.subTest(count=count):
                records = [
                    {"before_img": photo_bytes((300, 900)), "after_img": photo_bytes()}
                    for _ in range(count)
                ]
                with patch("urllib.request.urlopen", side_effect=AssertionError("no network")):
                    data = build_pdf(records)
                self.assertTrue(data.startswith(b"%PDF-"))
                self.assertEqual(len(re.findall(rb"/Type /Page\b", data)), (count + 1) // 2)

    def test_png_transparency_and_missing_after(self):
        data = build_pdf([{"before_img": photo_bytes(mode="RGBA", image_format="PNG"), "after_img": None}])
        self.assertTrue(data.startswith(b"%PDF-"))

    def test_exif_orientation(self):
        exif = Image.Exif()
        exif[274] = 6
        prepared = prepare_photo(photo_bytes((100, 200), exif=exif))
        with Image.open(io.BytesIO(prepared)) as image:
            self.assertEqual(image.size, (200, 100))
            self.assertNotIn(274, image.getexif())

    def test_invalid_photo_and_empty_records(self):
        with self.assertRaises(ValueError):
            prepare_photo(b"not an image")
        with self.assertRaisesRegex(ValueError, "第 1 項事前相片"):
            build_pdf([{"before_img": b"bad", "after_img": None}])
        with self.assertRaisesRegex(ValueError, "缺少事前"):
            build_pdf([{"before_img": None, "after_img": None}])
        with self.assertRaises(ValueError):
            build_pdf([])

    def test_missing_font(self):
        with self.assertRaisesRegex(FileNotFoundError, "缺少中文字型"):
            build_pdf([{"before_img": photo_bytes()}], ROOT / "missing-font.ttf")

    def test_streamlit_pdf_survives_rerun(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.session_state["vo_records"] = [{"before_img": photo_bytes(), "after_img": None}]
        app.button[1].click().run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        generated = app.session_state["pdf_data"]
        self.assertTrue(generated.startswith(b"%PDF-"))
        self.assertEqual(len(app.get("download_button")), 1)
        app.run()
        self.assertEqual(app.session_state["pdf_data"], generated)
        self.assertEqual(len(app.get("download_button")), 1)
        self.assertEqual(len(app.exception), 0)

    def test_streamlit_no_records(self):
        app = AppTest.from_file(str(ROOT / "app.py")).run()
        app.button[1].click().run()
        self.assertEqual(len(app.exception), 0)
        self.assertIsNone(app.session_state["pdf_data"])
        self.assertEqual(len(app.error), 1)


if __name__ == "__main__":
    unittest.main()
