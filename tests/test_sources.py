"""Offline checks of the source fetcher's parsing and comparison (tools/sources)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', 'sources'))
import paras as P  # noqa: E402
import sources as S  # noqa: E402

PAGE = """<html><head><title>x</title><script>var a=1;</script></head><body>
<p align="center">DECREE ON THE PASTORAL OFFICE</p>
<p>PREFACE</p>
<p>1. Christ the Lord, Son of the living God, came that He might save His people from their sins.(1)</p>
<p>2. In this Church of Christ the Roman pontiff, as the successor of Peter, enjoys supreme power.(2*) He is the pastor of all.</p>
<p>CHAPTER I</p>
<p>The bishops also have been designated by the Holy Spirit [3] to take the place of the apostles.</p>
<p>3. Bishops, sharing in the solicitude for all the churches, exercise this office in communion.</p>
<p>NOTES</p>
<p>1. Cf. Matt. 1:21.</p>
</body></html>"""


class Paras(unittest.TestCase):
    def setUp(self):
        self.ps = P.paras(PAGE)
        self.arts = P.articles(self.ps)

    def test_numbers_and_continuations(self):
        self.assertEqual(sorted(self.arts), [1, 2, 3])
        self.assertEqual(len(self.arts[2]), 2)  # an unnumbered paragraph belongs to the article before it

    def test_footnote_markers_removed(self):
        text = ' '.join(t for v in self.arts.values() for t in v)
        for mark in ('(1)', '(2*)', '[3]'):
            self.assertNotIn(mark, text)

    def test_stops_at_notes_and_keeps_headings(self):
        self.assertNotIn('Matt', ' '.join(self.arts[1]))
        self.assertEqual(self.ps[0]['head'], 'PREFACE')

    def test_roman(self):
        self.assertEqual([P.roman(x) for x in ('IV', 'IX', 'XL', 'XIV')], [4, 9, 40, 14])


class Compare(unittest.TestCase):
    SOURCE = S.norm('Bishops, sharing in the solicitude for all the churches, exercise this office (12) in communion with the pope.')

    def test_matching_entry_with_omissions(self):
        e = {'text': ['... Bishops, sharing in the solicitude for all the churches, exercise this office ...']}
        self.assertEqual(S.check_entry(e, self.SOURCE), [])

    def test_changed_word_is_reported(self):
        e = {'text': ['Bishops, sharing in the solicitude for all the dioceses, exercise this office in communion with the pope.']}
        bad = S.check_entry(e, self.SOURCE)
        self.assertEqual(len(bad), 1)
        self.assertGreater(bad[0]['similarity'], 0.8)

    def test_short_fragments_ignored(self):
        self.assertEqual(S.check_entry({'text': ['Amen ... so be it.']}, self.SOURCE), [])


class Helpers(unittest.TestCase):
    def test_local_articles(self):
        self.assertEqual(S.local_articles(['LG1', 'LG25', 'LGNP']), ('LG', {1, 25}))
        self.assertEqual(S.local_articles(['VC1', 'X2'])[0], None)

    def test_initials_avoid_taken_prefixes(self):
        self.assertEqual(S.initials('Christus Dominus', {'LG'}), ('CD', False))
        self.assertEqual(S.initials('Vita Consecrata', {'VC'}), ('VICO', True))

    def test_ranges(self):
        self.assertEqual(S.ranges([1, 2, 3, 5, 7, 8]), '1-3, 5, 7-8')
        self.assertEqual(S.ranges([]), '-')

    def test_source_line(self):
        t = {'title': 'Christus Dominus', 'genre': 'Decree', 'date': '1965-10-28'}
        self.assertEqual(S.source_line(t), '[From the Decree, "Christus Dominus," Oct. 28, 1965]')

    def test_archive_item(self):
        self.assertEqual(S.archive_item('https://archive.org/details/patrologiaecursu0087mign/page/n586/mode/2up'),
                         'patrologiaecursu0087mign')
        self.assertIsNone(S.archive_item('https://www.vatican.va/x.html'))


if __name__ == '__main__':
    unittest.main()
