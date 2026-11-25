"""Sealed research: the public files hold only placeholders, and the encryption round-trips.

The encryption test runs Node (tools/seal/seal.mjs) when it is installed, with a test password and a
reduced iteration count; it never touches private/ or src/data/sealed.json.
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import sealed as S  # noqa: E402


def load(name):
    with open(os.path.join(ROOT, 'src', 'data', name), encoding='utf-8') as f:
        return json.load(f)


class PublicFiles(unittest.TestCase):
    def setUp(self):
        self.k = load('continuity.json')
        self.m = self.k['sealed']

    def test_sealed_cases_are_placeholders(self):
        for c in self.k['cases']:
            if c.get('sealed'):
                self.assertLessEqual(set(c), {'id', 'group', 'title', 'sealed', 'hard_gate'}, c['id'])
        self.assertEqual(self.k['gate'], {'sealed': True})

    def test_nothing_sealed_is_left_in_public_lists(self):
        disputed = {q['id'] for q in load('disputed.json')}
        for q in self.m['disputed']:
            self.assertNotIn(q['id'], disputed)
        self.assertFalse({b['id'] for b in self.k['backlog']} & set(self.m['backlog']))

    def test_merge_restores_the_whole_layer(self):
        bundle = {'continuity': {'cases': [{'id': 'D1', 'group': 'D', 'title': 'x', 'verdict': 'plausible_concord'}],
                                 'gate': {'theory': 't', 'conditions': list(range(7))},
                                 'backlog': [{'id': 'BL1', 'cases': ['D1']}], 'meta_changes': {'0.3': 'full text'}},
                  'disputed': [{'id': 'sealed-q', 'refs': []}], 'disputed_related': {}}
        d = {'continuity': json.loads(json.dumps(self.k)), 'disputed': load('disputed.json')}
        S.merge_sealed(d, bundle)
        self.assertEqual(next(c for c in d['continuity']['cases'] if c['id'] == 'D1')['verdict'], 'plausible_concord')
        self.assertEqual(d['continuity']['gate']['theory'], 't')
        self.assertEqual(d['continuity']['backlog'][0]['id'], 'BL1')
        self.assertNotIn('sealed', d['continuity'])
        self.assertIn('sealed-q', {q['id'] for q in d['disputed']})

    def test_a_leaked_field_is_refused(self):
        class P(list):
            def add(self, where, msg):
                self.append(f'{where}: {msg}')
        k = json.loads(json.dumps(self.k))
        next(c for c in k['cases'] if c.get('sealed'))['summary'] = 'leaked'
        problems = P()
        S.validate_sealed({'continuity': k, 'disputed': load('disputed.json')}, problems)
        self.assertTrue(any('only its id' in p for p in problems))


@unittest.skipUnless(shutil.which('node'), 'Node is not installed')
class Encryption(unittest.TestCase):
    SCRIPT = r'''
import { seal, open } from './tools/seal/seal.mjs';
const bundle = { continuity: { cases: [{ id: 'T1', note: 'Haec Sancta, test only' }] }, docs: { 'a.md': '# test' } };
const file = seal(bundle, 'correct horse battery staple, test only', 1000);
const back = open(file, 'correct horse battery staple, test only');
let wrong = 'opened';
try { open(file, 'not the password, test only'); } catch (e) { wrong = e.message; }
console.log(JSON.stringify({ same: JSON.stringify(back) === JSON.stringify(bundle), wrong, readable: JSON.stringify(file).includes('Haec'), keys: Object.keys(file) }));
'''

    def test_round_trip_and_wrong_password(self):
        out = subprocess.run(['node', '--input-type=module', '-e', self.SCRIPT], cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        r = json.loads(out.stdout)
        self.assertTrue(r['same'])
        self.assertEqual(r['wrong'], 'wrong password')
        self.assertFalse(r['readable'])  # nothing of the plaintext is visible in the sealed file
        self.assertNotIn('password', ' '.join(r['keys']))


if __name__ == '__main__':
    unittest.main()
