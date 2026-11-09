"""Atomic photo-batch tests; every image is generated in memory."""

import copy
import io
import re
import unittest
from unittest.mock import patch

from PIL import Image

import pdf_export
from photo_records import MAX_BATCH_PHOTOS, add_before_batch, attach_after_batch


def photo_bytes(image_format="JPEG", color=(30, 90, 150), size=(32, 24)):
    """Make a small, distinguishable image without fixtures or user photos."""
    output = io.BytesIO()
    mode = "RGBA" if image_format == "PNG" else "RGB"
    if mode == "RGBA":
        color = (*color, 180)
    with Image.new(mode, size, color) as image:
        image.save(output, image_format)
    return output.getvalue()


class PhotoRecordsTests(unittest.TestCase):
    def setUp(self):
        self.jpeg = photo_bytes()
        self.png = photo_bytes("PNG", color=(180, 40, 70), size=(24, 32))
        self.other = photo_bytes(color=(40, 180, 70), size=(40, 20))
        self.uploads = [
            ("first.jpg", self.jpeg),
            ("第二張.png", self.png),
            ("third.jpg", self.other),
        ]

    def records(self, count=3):
        return [
            {
                "before_img": self.jpeg,
                "after_img": None,
                "before_name": f"old-{index}.jpg",
                "description": f"work item {index}",
                "metadata": {"tags": [f"tag-{index}"]},
            }
            for index in range(count)
        ]

    def assert_prepared_photo(self, actual, source):
        self.assertEqual(actual, pdf_export.prepare_photo(source))
        with Image.open(io.BytesIO(actual)) as image:
            image.load()
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.mode, "RGB")

    def assert_rejected_without_mutation(
        self, operation, records, uploads, targets=None, message=""
    ):
        snapshot = copy.deepcopy((records, uploads, targets))
        record_ids = [id(record) for record in records]
        with self.assertRaisesRegex(ValueError, message):
            operation()
        self.assertEqual((records, uploads, targets), snapshot)
        self.assertEqual([id(record) for record in records], record_ids)

    def test_one_before_accepts_jpeg_and_png_and_keeps_filename(self):
        for name, data in self.uploads[:2]:
            with self.subTest(name=name):
                uploads = [(name, data)]
                result = add_before_batch([], uploads)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["before_name"], name)
                self.assertIsNone(result[0]["after_img"])
                self.assertNotIn("after_name", result[0])
                self.assert_prepared_photo(result[0]["before_img"], data)
                self.assertEqual(uploads, [(name, data)])

    def test_multiple_before_preserve_selection_order_and_old_records(self):
        records = self.records(2)
        records[0]["after_img"] = self.other
        records[0]["after_name"] = "already-complete.jpg"
        snapshot = copy.deepcopy((records, self.uploads))
        result = add_before_batch(records, self.uploads)
        self.assertIsNot(result, records)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[:2], records)
        self.assertEqual(
            [record["before_name"] for record in result[2:]],
            [name for name, _ in self.uploads],
        )
        for record, (_, source) in zip(result[2:], self.uploads):
            self.assert_prepared_photo(record["before_img"], source)
            self.assertIsNone(record["after_img"])
        self.assertEqual((records, self.uploads), snapshot)

    def test_before_does_not_deduplicate_same_filename(self):
        uploads = [("same.jpg", self.jpeg), ("same.jpg", self.png)]
        result = add_before_batch([], uploads)
        self.assertEqual([record["before_name"] for record in result], ["same.jpg"] * 2)
        self.assert_prepared_photo(result[0]["before_img"], self.jpeg)
        self.assert_prepared_photo(result[1]["before_img"], self.png)

    def test_before_corrupt_member_rejects_whole_batch_without_mutation(self):
        for position in range(3):
            with self.subTest(position=position):
                records = self.records(2)
                uploads = list(self.uploads)
                uploads[position] = ("broken.png", b"not a valid image")
                self.assert_rejected_without_mutation(
                    lambda: add_before_batch(records, uploads),
                    records,
                    uploads,
                    message=rf"第 {position + 1} 張（broken\.png）無法讀取",
                )

    def test_before_empty_batch_rejected_without_mutation(self):
        records, uploads = self.records(), []
        self.assert_rejected_without_mutation(
            lambda: add_before_batch(records, uploads),
            records,
            uploads,
            message="至少一張",
        )

    def test_before_more_than_50_rejected_without_mutation(self):
        self.assertEqual(MAX_BATCH_PHOTOS, 50)
        records = self.records()
        uploads = [(f"photo-{index}.jpg", self.jpeg) for index in range(51)]
        self.assert_rejected_without_mutation(
            lambda: add_before_batch(records, uploads), records, uploads, message="最多 50"
        )

    def test_before_exactly_50_allowed_and_limit_is_per_batch(self):
        records = self.records(2)
        uploads = [(f"photo-{index}.jpg", self.jpeg) for index in range(50)]
        snapshot = copy.deepcopy((records, uploads))
        result = add_before_batch(records, uploads)
        self.assertEqual(len(result), 52)
        self.assertEqual(result[:2], records)
        self.assertEqual(
            [record["before_name"] for record in result[2:]],
            [name for name, _ in uploads],
        )
        self.assertEqual((records, uploads), snapshot)

    def test_one_after_sets_image_and_filename_without_changing_inputs(self):
        for name, data in self.uploads[:2]:
            with self.subTest(name=name):
                records, uploads, targets = self.records(1), [(name, data)], [0]
                snapshot = copy.deepcopy((records, uploads, targets))
                result = attach_after_batch(records, uploads, targets)
                self.assertIsNot(result, records)
                self.assertIsNot(result[0], records[0])
                self.assertEqual(result[0]["after_name"], name)
                self.assert_prepared_photo(result[0]["after_img"], data)
                self.assertEqual((records, uploads, targets), snapshot)

    def test_after_arbitrary_mapping_preserves_order_metadata_and_unselected_record(self):
        records, uploads, targets = self.records(4), list(self.uploads), [2, 0, 3]
        records[1]["after_img"] = self.other
        records[1]["after_name"] = "untouched-completed.jpg"
        snapshot = copy.deepcopy((records, uploads, targets))
        result = attach_after_batch(records, uploads, targets)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1], records[1])
        for index, (name, data) in zip(targets, uploads):
            self.assertEqual(result[index]["after_name"], name)
            self.assert_prepared_photo(result[index]["after_img"], data)
        for original, updated in zip(records, result):
            self.assertIsNot(original, updated)
            self.assertEqual(
                {key: value for key, value in updated.items() if key not in ("after_img", "after_name")},
                {key: value for key, value in original.items() if key not in ("after_img", "after_name")},
            )
        self.assertEqual((records, uploads, targets), snapshot)

    def test_after_can_fill_record_without_after_keys(self):
        records = [{"before_img": self.jpeg, "before_name": "before.jpg"}]
        snapshot = copy.deepcopy(records)
        result = attach_after_batch(records, [("after.png", self.png)], [0])
        self.assertEqual(result[0]["after_name"], "after.png")
        self.assert_prepared_photo(result[0]["after_img"], self.png)
        self.assertEqual(records, snapshot)

    def test_after_corrupt_member_rejects_whole_batch_without_mutation(self):
        for position in range(3):
            with self.subTest(position=position):
                records, uploads, targets = self.records(), list(self.uploads), [2, 0, 1]
                uploads[position] = ("corrupt.jpg", b"\xff\xd8truncated-jpeg")
                self.assert_rejected_without_mutation(
                    lambda: attach_after_batch(records, uploads, targets),
                    records,
                    uploads,
                    targets,
                    message=rf"第 {position + 1} 張（corrupt\.jpg）無法讀取",
                )

    def test_after_missing_or_extra_target_rejected_without_mutation(self):
        for targets in ([], [0], [0, 1, 2]):
            with self.subTest(targets=targets):
                records, uploads = self.records(), self.uploads[:2]
                self.assert_rejected_without_mutation(
                    lambda: attach_after_batch(records, uploads, targets),
                    records,
                    uploads,
                    targets,
                    message="每張事後相",
                )

    def test_after_invalid_target_types_rejected_without_mutation(self):
        for invalid in (None, "1", 1.0, True, False, [], {}):
            with self.subTest(target=invalid):
                records, uploads, targets = self.records(), self.uploads[:2], [0, invalid]
                self.assert_rejected_without_mutation(
                    lambda: attach_after_batch(records, uploads, targets),
                    records,
                    uploads,
                    targets,
                    message="有效的配對工項",
                )

    def test_after_out_of_range_target_rejected_without_mutation(self):
        for invalid in (-1, 3, 999):
            with self.subTest(target=invalid):
                records, uploads, targets = self.records(), self.uploads[:2], [0, invalid]
                self.assert_rejected_without_mutation(
                    lambda: attach_after_batch(records, uploads, targets),
                    records,
                    uploads,
                    targets,
                    message="有效的配對工項",
                )

    def test_after_target_into_empty_records_rejected_without_mutation(self):
        records, uploads, targets = [], self.uploads[:1], [0]
        self.assert_rejected_without_mutation(
            lambda: attach_after_batch(records, uploads, targets),
            records,
            uploads,
            targets,
            message="有效的配對工項",
        )

    def test_after_duplicate_targets_rejected_without_mutation(self):
        records, uploads, targets = self.records(), list(self.uploads), [2, 0, 2]
        self.assert_rejected_without_mutation(
            lambda: attach_after_batch(records, uploads, targets),
            records,
            uploads,
            targets,
            message="同一工項不能配對多張",
        )

    def test_after_existing_photo_is_never_overwritten_or_partially_applied(self):
        records, uploads, targets = self.records(), self.uploads[:2], [0, 2]
        records[2]["after_img"] = self.other
        records[2]["after_name"] = "keep-existing.jpg"
        self.assert_rejected_without_mutation(
            lambda: attach_after_batch(records, uploads, targets),
            records,
            uploads,
            targets,
            message="第 3 項已有完成相片.*不會覆蓋",
        )
        self.assertIsNone(records[0]["after_img"])
        self.assertEqual(records[2]["after_name"], "keep-existing.jpg")
        self.assertEqual(records[2]["after_img"], self.other)

    def test_after_empty_batch_rejected_without_mutation(self):
        records, uploads, targets = self.records(), [], []
        self.assert_rejected_without_mutation(
            lambda: attach_after_batch(records, uploads, targets),
            records,
            uploads,
            targets,
            message="至少一張",
        )

    def test_after_more_than_50_rejected_without_mutation(self):
        records = self.records(51)
        uploads = [(f"after-{index}.jpg", self.jpeg) for index in range(51)]
        targets = list(range(51))
        self.assert_rejected_without_mutation(
            lambda: attach_after_batch(records, uploads, targets),
            records,
            uploads,
            targets,
            message="最多 50",
        )

    def test_after_exactly_50_allowed_with_reverse_mapping(self):
        records = self.records(51)
        uploads = [(f"after-{index}.png", self.png) for index in range(50)]
        targets = list(reversed(range(50)))
        snapshot = copy.deepcopy((records, uploads, targets))
        result = attach_after_batch(records, uploads, targets)
        self.assertEqual(len(result), 51)
        for target, (name, _) in zip(targets, uploads):
            self.assertEqual(result[target]["after_name"], name)
            self.assert_prepared_photo(result[target]["after_img"], self.png)
        self.assertEqual(result[50], records[50])
        self.assertEqual((records, uploads, targets), snapshot)

    def test_batch_results_build_real_pdf_with_two_records_per_page(self):
        for count in (1, 2, 3, 4, 5):
            with self.subTest(count=count):
                uploads = [
                    (f"before-{index}.png", self.png if index % 2 else self.jpeg)
                    for index in range(count)
                ]
                before_records = add_before_batch([], uploads)
                targets = list(reversed(range(count)))
                after_uploads = [(f"after-{index}.jpg", self.other) for index in range(count)]
                completed_records = attach_after_batch(before_records, after_uploads, targets)
                for stage, records in (("before", before_records), ("completed", completed_records)):
                    with self.subTest(stage=stage):
                        snapshot = copy.deepcopy(records)
                        rendered = []
                        real_record_table = pdf_export._record_table

                        def track_record(pdf, record, index, y):
                            rendered.append((pdf.page_no(), index, y, record))
                            return real_record_table(pdf, record, index, y)

                        with patch("pdf_export._record_table", side_effect=track_record):
                            data = pdf_export.build_pdf(records)
                        self.assertTrue(data.startswith(b"%PDF-"))
                        self.assertEqual(len(re.findall(rb"/Type /Page\b", data)), (count + 1) // 2)
                        self.assertEqual(
                            [(page, index, y) for page, index, y, _ in rendered],
                            [(index // 2 + 1, index + 1, 72 + (index % 2) * 102) for index in range(count)],
                        )
                        for (_, _, _, rendered_record), expected_record in zip(rendered, records):
                            self.assertIs(rendered_record, expected_record)
                        self.assertEqual(records, snapshot)


if __name__ == "__main__":
    unittest.main()
