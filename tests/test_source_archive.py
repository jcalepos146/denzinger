"""Keep the public bibliography independent from the local research collection."""
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from source_archive import BATCHES, archive_page, catalogue


class SourceArchiveTests(unittest.TestCase):
    def test_local_files_are_searchable_without_extracting_them(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            archives = Path(temporary)
            for name in BATCHES:
                with ZipFile(archives / f'{name}(1).zip', mode='w') as archive:
                    archive.writestr('research/basel.txt', 'research_marker & <script>test</script>')
            items = catalogue(stack, archives)
            self.assertEqual(len(items), 5)
            self.assertFalse((archives / 'research').exists())
            self.assertIn('5 of 5 files', archive_page(items, 'research_marker', '', True))
            self.assertIn('0 of 5 files', archive_page(items, 'research_marker', '', False))
            self.assertIn('1 of 5 files', archive_page(items, 'basel', 'Low priority', False))

    def test_public_output_keeps_sealed_payload_and_public_editions(self):
        with tempfile.TemporaryDirectory() as temporary:
            dist = Path(temporary) / 'dist'
            subprocess.run([sys.executable, str(ROOT / 'build/build.py'), '--out', str(dist),
                            '--url', 'https://example.org/denzinger1.0/'],
                           check=True, capture_output=True)
            page = (dist / 'editions/index.html').read_text(encoding='utf-8')
            self.assertIn('https://example.org/denzinger1.0/editions/', page)
            self.assertIn('Bullarium Romanum', page)
            for term in ('Haec Sancta', 'Mainz', 'Raynaldus', 'Moyses vir Dei'):
                self.assertNotIn(term, page)
            self.assertFalse((dist / 'local-sources').exists())
            self.assertEqual(list(dist.rglob('*.zip')), [])
            self.assertEqual((dist / 'data/sealed.json').read_bytes(),
                             (ROOT / 'src/data/sealed.json').read_bytes())
            research = json.loads((dist / 'data/continuity.json').read_text(encoding='utf-8'))
            d1 = next(case for case in research['cases'] if case['id'] == 'D1')
            self.assertTrue(d1['sealed'])
            self.assertEqual(d1['refs'], [])
        self.assertLessEqual(set(d1), {'id', 'group', 'title', 'sealed', 'hard_gate', 'refs'})
