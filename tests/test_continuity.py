"""Regression checks for the hermeneutic of ecclesial continuity (src/data/continuity.json).

These hold the research layer to its protocol: all 24 cases are present and discoverable, the hard
gate is never passed by analogy alone, quotations are word for word, and the original texts and
guides are untouched by the layer.
"""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build'))
from build import load_all, check, Problems
from continuity import CASE_IDS, validate_continuity, case_refs, norm


class ContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_all()
        cls.order, problems = check(cls.data)
        assert not problems, problems
        cls.k = cls.data['continuity']
        cls.cases = {c['id']: c for c in cls.k['cases']}
        cls.entries = {e['id']: e for e in cls.data['entries']}

    def problems_after(self, change):
        d = copy.deepcopy(self.data)
        change(d['continuity'])
        P = Problems()
        validate_continuity(d, self.order, P)
        return P

    def test_all_24_cases_present_in_order(self):
        self.assertEqual([c['id'] for c in self.k['cases']], CASE_IDS)
        self.assertEqual(len(CASE_IDS), 24)

    def test_every_case_rests_on_some_text_or_names_its_gap(self):
        for c in self.k['cases']:
            self.assertTrue(case_refs(c) or c['gaps'], c['id'])

    def test_d1_is_the_hard_gate_and_provisional(self):
        d1 = self.cases['D1']
        self.assertTrue(d1.get('hard_gate'))
        self.assertEqual([g['n'] for g in d1['gate']], list(range(1, 8)))
        self.assertTrue(d1['provisional'])
        self.assertNotEqual(d1['verdict'], 'demonstrated_concord')

    def test_d1_cannot_be_declared_demonstrated_by_analogy(self):
        def promote(k):
            for c in k['cases']:
                if c['id'] == 'D1':
                    c['verdict'] = 'demonstrated_concord'
        self.assertTrue(any('demonstrated concord' in p or 'unresolved, not reconciled' in p for p in self.problems_after(promote)))

    def test_failed_condition_blocks_concord(self):
        def fail(k):
            for c in k['cases']:
                if c['id'] == 'D1':
                    c['verdict'] = 'plausible_concord'
                    c['gate'][3]['status'] = 'fail'
        self.assertTrue(any('failed pass condition' in p for p in self.problems_after(fail)))

    def test_no_case_is_demonstrated_while_sources_unverified(self):
        for c in self.k['cases']:
            if c['verdict'] == 'demonstrated_concord':
                self.assertTrue(c['source_verified'] and not c['provisional'], c['id'])

    def test_quotations_are_word_for_word(self):
        n = 0
        for c in self.k['cases']:
            for p in c['propositions']:
                if p.get('quote'):
                    n += 1
                    self.assertIn(norm(p['quote']), norm(' '.join(self.entries[p['ref']]['text'])), p['id'])
        self.assertGreater(n, 20)

    def test_invented_quotation_is_caught(self):
        def invent(k):
            k['cases'][0]['propositions'][0]['quote'] = 'words that no pope ever wrote'
            k['cases'][0]['propositions'][0]['ref'] = '1092'
        self.assertTrue(any('not found word for word' in p for p in self.problems_after(invent)))

    def test_hand_typed_denzinger_number_is_caught(self):
        def typed(k):
            k['cases'][0]['summary'] += ' See DS 9999.'
        self.assertTrue(any('DS 9999' in p for p in self.problems_after(typed)))

    def test_unknown_label_is_caught(self):
        def label(k):
            k['cases'][0]['propositions'][0]['evidence'] = 'X'
        self.assertTrue(any('unknown evidence label' in p for p in self.problems_after(label)))

    def test_regression_subset_keeps_the_ten_earlier_cases(self):
        self.assertEqual(len(self.k['regression']), 10)
        disputed = {q['id'] for q in self.data['disputed']}
        for r in self.k['regression']:
            self.assertIn(r['disputed'], disputed)

    def test_every_principle_maps_to_an_earlier_one(self):
        herm = {p['id'] for p in self.data['herm']['principles']}
        for p in self.k['principles']:
            self.assertTrue(p['old'] and set(p['old']) <= herm, p['id'])

    def test_layer_is_labelled_as_not_church_teaching(self):
        self.assertIn('not teaching of the Catholic Church', self.k['meta']['notice'])
        self.assertIn('not his judgment', self.k['benedict']['inference_note'])

    def test_doctrinal_grade_and_legal_force_are_separate_fields(self):
        for c in self.k['cases']:
            for p in c['propositions']:
                self.assertIn('assent', p)
                self.assertIn('binding_status', p)

    def test_audio_summary_answers_the_three_questions(self):
        for c in self.k['cases']:
            self.assertEqual(set(c['audio']), {'taught', 'authority', 'permanence'}, c['id'])

    def test_protocol_change_keeps_the_earlier_wording(self):
        self.assertEqual(self.k['meta']['changes'][0]['version'], self.k['meta']['version'])
        h = [x for x in self.k['gate'].get('history', []) if x['n'] == 4]
        self.assertTrue(h and h[0]['version'] == '0.2' and 'Specify who discerns' in h[0]['text'])

    def test_d1_shows_its_verdict_under_each_protocol(self):
        case = self.cases['D1']
        history = case['verdict_history']
        self.assertEqual(history[0]['protocol'], '0.2')
        self.assertEqual(history[0]['verdict'], 'unresolved_tension')
        self.assertEqual(history[1]['protocol'], '0.3')
        self.assertEqual(history[1]['confidence'], 'low')
        self.assertEqual(history[-1]['protocol'], self.k['meta']['version'])
        self.assertEqual(history[-1]['verdict'], case['verdict'])
        self.assertEqual(history[-1]['confidence'], case['confidence'])

    def test_d1_rejects_confidence_out_of_sync_with_history(self):
        def change_confidence(k):
            history = next(c for c in k['cases'] if c['id'] == 'D1')['verdict_history']
            history[-1]['confidence'] = 'high'

        self.assertTrue(any('must match the current verdict and confidence' in p
                            for p in self.problems_after(change_confidence)))

    def test_d1_tests_every_papal_line(self):
        rows = self.cases['D1']['counterfactuals']['rows']
        self.assertEqual([r['id'] for r in rows], ['A', 'B', 'C', 'D'])
        joined = ' '.join(r['label'] for r in rows)
        for line in ('Roman', 'Pisan', 'Avignon'):
            self.assertIn(line, joined)


if __name__ == '__main__':
    unittest.main()
