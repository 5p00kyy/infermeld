import json
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.rows = []
        self.row = None
        self.cell = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ['href', 'src', 'srcset']:
            if name in attrs:
                self.links.append((tag, name, attrs[name]))
        if tag == 'tr':
            self.row = {'attrs': attrs, 'cells': []}
        if tag in ['th', 'td'] and self.row is not None:
            self.cell = ''

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ['th', 'td'] and self.cell is not None and self.row is not None:
            self.row['cells'].append(self.cell.strip())
            self.cell = None
        if tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None


class PresentationTests(unittest.TestCase):
    def test_site_links_remain_inside_project_path(self):
        for path in (ROOT / 'site').glob('*.html'):
            page = Page(path.read_text())
            for tag, attr, link in page.links:
                with self.subTest(page=path.name, link=link):
                    target = urlsplit(link)
                    if target.scheme or target.netloc:
                        self.assertEqual(attr, 'href', 'no remote embedded assets')
                        self.assertEqual(target.scheme, 'https')
                        continue
                    self.assertFalse(target.path.startswith('/'), 'root URLs break project Pages')
                    destination = (path.parent / unquote(target.path)).resolve() if target.path else path
                    self.assertTrue(destination.is_relative_to(ROOT / 'site'))
                    self.assertTrue(destination.is_file())
                    if target.fragment:
                        document = page if destination == path else Page(destination.read_text())
                        self.assertIn(unquote(target.fragment), document.ids)

    def test_historical_table_matches_every_scoped_measurement(self):
        page = Page((ROOT / 'site/index.html').read_text())
        record = json.loads((ROOT / 'site/results.json').read_text())
        rows = [row for row in page.rows if 'data-workload' in row['attrs']]
        self.assertEqual(len(rows), len(record['rows']))
        for expected in record['rows']:
            matches = [row for row in rows if row['attrs']['data-family'] == expected['family']
                       and row['attrs']['data-workload'] == expected['workload']]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]['cells'], [record['models'][expected['family']]['label'],
                             expected['workload'], f"{expected['decode_tps']:.2f}",
                             f"{expected['end_to_end_tps']:.2f}", f"{expected['prefill_tps']:.2f}"])

    def test_displayed_cli_acceptance_matches_the_retained_cases(self):
        page = Page((ROOT / 'site/index.html').read_text())
        record = json.loads((ROOT / 'site/cli-acceptance.json').read_text())
        rows = [row for row in page.rows if 'data-mtp' in row['attrs']]
        self.assertEqual(len(rows), len(record['cases']))
        for expected in record['cases']:
            matches = [row for row in rows if row['attrs']['data-mtp'] == str(expected['mtp'])]
            self.assertEqual(len(matches), 1)
            passed = sum(check['passed'] is True for check in expected['checks'])
            mode = 'Default · no MTP' if expected['mtp'] == 0 else f"Explicit · MTP{expected['mtp']}"
            self.assertEqual(matches[0]['cells'], [mode, f"{expected['context_reserved']:,}",
                             f"{passed} / {len(expected['checks'])}",
                             f"Owned exit {expected['shutdown_exit']}"])

    def test_badge_assets_have_accessible_and_truthful_labels(self):
        from xml.etree import ElementTree
        readme = (ROOT / 'README.md').read_text()
        paths = re.findall(r'\]\((assets/[^)]+\.svg)\)', readme)
        self.assertEqual(len(paths), 5)
        for path in paths:
            asset = ElementTree.fromstring((ROOT / path).read_text())
            self.assertEqual(asset.attrib.get('role'), 'img')
            self.assertTrue(asset.attrib.get('aria-label'))
            self.assertNotIn('passing', asset.attrib['aria-label'])
        for path in (ROOT / 'assets').glob('*.svg'):
            ElementTree.fromstring(path.read_text())


if __name__ == '__main__':
    unittest.main()
