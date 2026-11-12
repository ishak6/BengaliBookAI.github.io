import unittest
from ocr_quality import text_quality, needs_ocr, choose_text


class OCRQualityTests(unittest.TestCase):
    def test_empty_or_short_native_text_needs_ocr(self):
        self.assertTrue(needs_ocr(""))
        self.assertTrue(needs_ocr("short text"))

    def test_clean_bengali_native_text_does_not_need_ocr(self):
        text = ("বাংলাদেশের ইতিহাস ও সংস্কৃতি সম্পর্কে এই অধ্যায়ে বিস্তারিত আলোচনা করা হয়েছে। " * 3)
        self.assertFalse(needs_ocr(text))
        self.assertGreater(text_quality(text), 0.72)

    def test_replacement_character_text_needs_ocr(self):
        text = ("বাংলা\\ufffdলেখা অ\\ufffdক্ষর ভুল\\ufffdভাবে পড়া হয়েছে। " * 8)
        self.assertTrue(needs_ocr(text))

    def test_choose_cleaner_ocr_when_native_text_is_corrupt(self):
        native = ("বাংলা\\ufffdলেখা অ\\ufffdক্ষর ভুল\\ufffdভাবে পড়া হয়েছে। " * 8)
        ocr = ("বাংলা ভাষার লেখা সঠিকভাবে শনাক্ত করা হয়েছে। " * 8)
        self.assertEqual(choose_text(native, ocr), ocr.strip())

    def test_preserve_good_native_text_when_ocr_is_worse(self):
        native = ("বাংলাদেশের ইতিহাস ও সংস্কৃতি সম্পর্কে এই অধ্যায়ে বিস্তারিত আলোচনা করা হয়েছে। " * 3)
        ocr = "বাংলা লেখা"
        self.assertEqual(choose_text(native, ocr), native.strip())


if __name__ == "__main__":
    unittest.main()
