import io
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.proto.Common_pb2 import FileURLs
from streamlit.runtime.uploaded_file_manager import UploadedFile, UploadedFileRec
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def upload(name, color="white", data=None):
    if data is None:
        output = io.BytesIO()
        Image.new("RGB", (120, 80), color).save(output, "JPEG")
        data = output.getvalue()
    return UploadedFile(UploadedFileRec(name, name, "image/jpeg", data), FileURLs())


class PhotoUploadUITests(unittest.TestCase):
    def run_app(self, inputs):
        def pick(label, *args, **kwargs):
            key = kwargs.get("key")
            if key == "report_logo_upload":
                return None
            return inputs.get(key, [])
        return patch("streamlit.file_uploader", side_effect=pick)

    def test_batch_before_saved_once_and_pdf_cleared(self):
        inputs = {"before_upload_0": [upload("one.jpg"), upload("two.jpg", "blue")]}
        with self.run_app(inputs) as picker:
            app = AppTest.from_file(str(ROOT / "app.py")).run()
            app.session_state["pdf_data"] = b"old pdf"
            app.button(key="save_before_batch").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.session_state["vo_records"]), 2)
            self.assertEqual(app.session_state["vo_records"][1]["before_name"], "two.jpg")
            self.assertIsNone(app.session_state["pdf_data"])
            self.assertEqual(app.session_state["before_upload_generation"], 1)
            self.assertTrue(app.button(key="save_before_batch").disabled)
            app.run()
            self.assertEqual(len(app.session_state["vo_records"]), 2)
            for call in picker.call_args_list:
                if call.kwargs.get("key", "").startswith(("before_upload_", "after_upload_")):
                    self.assertEqual(call.kwargs["type"], "image/*")
                    self.assertTrue(call.kwargs["accept_multiple_files"])

    def test_after_requires_confirmation_and_updates_correct_mapping(self):
        inputs = {"after_upload_0": [upload("after-a.jpg"), upload("after-b.jpg", "green")]}
        with self.run_app(inputs):
            app = AppTest.from_file(str(ROOT / "app.py")).run()
            before = upload("before.jpg").getvalue()
            app.session_state["vo_records"] = [
                {"before_img": before, "after_img": None, "before_name": f"before-{i}.jpg"}
                for i in range(3)
            ]
            app.run()
            self.assertTrue(app.button(key="save_after_batch").disabled)
            app.selectbox[0].select_index(3).run()
            app.checkbox[0].check().run()
            self.assertFalse(app.button(key="save_after_batch").disabled)
            app.button(key="save_after_batch").click().run()
            self.assertEqual(len(app.exception), 0)
            records = app.session_state["vo_records"]
            self.assertIsNone(records[0]["after_img"])
            self.assertEqual(records[2]["after_name"], "after-a.jpg")
            self.assertEqual(records[1]["after_name"], "after-b.jpg")
            self.assertEqual(app.session_state["after_upload_generation"], 1)

    def test_changed_pairing_requires_new_confirmation(self):
        inputs = {"after_upload_0": [upload("after.jpg")]}
        with self.run_app(inputs):
            app = AppTest.from_file(str(ROOT / "app.py")).run()
            before = upload("before.jpg").getvalue()
            app.session_state["vo_records"] = [{"before_img": before, "after_img": None}] * 2
            app.run()
            app.checkbox[0].check().run()
            app.selectbox[0].select_index(2).run()
            self.assertFalse(app.checkbox[0].value)
            self.assertTrue(app.button(key="save_after_batch").disabled)

    def test_invalid_batch_leaves_all_records_unchanged(self):
        inputs = {"before_upload_0": [upload("valid.jpg"), upload("bad.jpg", data=b"bad")]}
        with self.run_app(inputs):
            app = AppTest.from_file(str(ROOT / "app.py")).run()
            app.button(key="save_before_batch").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.session_state["vo_records"], [])
            self.assertTrue(any("bad.jpg" in error.value for error in app.error))


if __name__ == "__main__":
    unittest.main()
