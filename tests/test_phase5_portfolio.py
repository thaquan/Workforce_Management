"""Keep the public, aggregate-only portfolio assets reproducible in CI.

Uses only Python standard library: no Power BI Desktop or Pillow on runner.
"""

from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "docs" / "portfolio"
IMAGES = GALLERY / "images"
EXPECTED = {
    "01-executive-overview.png",
    "02-workforce-planning.png",
    "03-attrition-analysis.png",
    "04-retention-engagement.png",
    "05-recruitment-performance.png",
    "06-data-quality-trust.png",
}


class PortfolioPublishingTests(unittest.TestCase):
    def test_all_six_report_canvas_images_are_readable_and_metadata_free(self):
        found = {p.name for p in IMAGES.iterdir() if p.is_file()}
        self.assertEqual(found, EXPECTED)
        for name in sorted(EXPECTED):
            path = IMAGES / name
            contents = path.read_bytes()
            self.assertTrue(contents.startswith(b"\x89PNG\r\n\x1a\n"), name)
            self.assertLess(len(contents), 350_000, name)
            width, height = struct.unpack(">II", contents[16:24])
            self.assertEqual((width, height), (1936, 1089), name)
            self.assertEqual(width * 9, height * 16, name)
            self.assertEqual(contents[12:16], b"IHDR", name)
            # A PNG text/exif chunk could unintentionally contain local paths
            # or private source information; the exported images need none.
            offset = 8
            while offset + 12 <= len(contents):
                count = struct.unpack(">I", contents[offset:offset + 4])[0]
                kind = contents[offset + 4:offset + 8]
                self.assertNotIn(kind, {b"tEXt", b"iTXt", b"zTXt", b"eXIf"}, name)
                offset += 12 + count
                if kind == b"IEND":
                    break
            self.assertEqual(offset, len(contents), name)

    def test_every_local_portfolio_link_resolves(self):
        markdowns = [ROOT / "README.md", *GALLERY.glob("*.md"),
                     ROOT / "docs" / "phase7" / "dagster_extension_plan.md"]
        self.assertGreaterEqual(len(markdowns), 7)
        for page in markdowns:
            content = page.read_text(encoding="utf-8")
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                destination = target.split("#", 1)[0].strip()
                if not destination or "://" in destination or destination.startswith("mailto:"):
                    continue
                self.assertTrue((page.parent / destination).exists(),
                                f"Broken link in {page}: {target}")

    def test_gallery_states_data_limitations_and_is_not_a_fake_live_demo(self):
        readme = (GALLERY / "README.md").read_text(encoding="utf-8")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(readme.count("!["), 6)
        for warning in ("33 of 36", "provisional", "not causal",
                        "Power BI Service", "static screenshots"):
            self.assertIn(warning.lower(), readme.lower())
        self.assertIn("docs/portfolio/images/01-executive-overview.png", root_readme)
        self.assertIn("docs/portfolio/README.md", root_readme)


if __name__ == "__main__":
    unittest.main()
