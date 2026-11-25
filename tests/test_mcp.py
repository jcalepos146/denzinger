"""The MCP server (tools/mcp/server.py): the protocol, the tools and the references people cite.

Runs on a small sample of the published data, so it needs neither a build nor the network.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(os.path.dirname(HERE), 'tools', 'mcp', 'server.py')
sys.path.insert(0, os.path.dirname(SERVER))
import server as S  # noqa: E402

ENTRIES = [
    {'id': '1839', 'ds': ['3073', '3074'], 'era': 'The Vatican Council', 'year': 1870, 'session': 'Session IV (July 18, 1870)',
     'topic': 'The Infallible "Magisterium" of the Roman Pontiff', 'source': None, 'weight': 'conc-def', 'grade': 'dogma',
     'gradeStatus': 'editorial assessment', 'gradeNote': 'The definition of papal infallibility.', 'kinds': ['definition'],
     'text': ['the Roman Pontiff, when he speaks ex cathedra, ... is possessed of that infallibility'],
     'documentId': 'pastor-aeternus', 'refersTo': [], 'citedBy': ['LG25'], 'supplement': False},
    {'id': 'LG25', 'ds': [], 'era': 'The Second Vatican Council', 'year': 1964, 'session': '',
     'topic': 'On the Episcopate', 'source': '[From the Dogmatic Constitution on the Church, "Lumen Gentium," Nov. 21, 1964]',
     'weight': 'conc-decree', 'grade': 'authentic', 'text': ['religious submission of mind and will ... even when he is not speaking ex cathedra'],
     'documentId': 'lg', 'refersTo': ['1839'], 'citedBy': [], 'supplement': False},
    {'id': '299', 'ds': ['580'], 'era': 'Leo IX', 'year': 1053, 'session': '', 'topic': 'Error', 'source': None,
     'weight': 'condemned', 'grade': 'condemned-heresy', 'censure': ['heretical'], 'text': ['A condemned error.'],
     'documentId': None, 'refersTo': [], 'citedBy': [], 'supplement': False},
    {'id': 'S1', 'ds': [], 'era': 'Constance', 'year': 1415, 'session': 'Session 5', 'topic': 'Haec sancta', 'source': None,
     'weight': 'supplement', 'grade': 'disputed', 'text': ['This holy synod ...'], 'documentId': None, 'refersTo': [],
     'citedBy': [], 'supplement': True},
]
DATA = {
    'entries.json': ENTRIES,
    'latin.json': {'3074': 'Romanum Pontificem, cum ex cathedra loquitur ...'},
    'guides.json': {'hermeneutics': {'principles': [{'id': 'same-sense', 'title': 'Development in the same sense',
                                                     'rule': 'Doctrine grows in the same sense.'}]},
                    'threads': [{'id': 'papacy', 'title': 'The papacy', 'steps': [{'refs': ['1839']}]}]},
    'continuity.json': {
        'benedict': {'source': 'Benedict XVI, 22 December 2005', 'status': 'An address.'},
        'principles': [{'id': 'P1', 'title': 'Precision', 'rule': 'Same sense, same subject.'}],
        'levels': [{'id': 'logical', 'title': 'Logical'}],
        'groups': {'B': 'Vatican II against earlier formulations'},
        'vocab': {k: {'x': 'X: an example.'} for k in ('formal_object', 'assent', 'binding_status', 'evidence', 'matrix_result')}
        | {'verdict': {'plausible_concord': 'Plausible concord: a substantial case.'}},
        'cases': [{'id': 'B6', 'group': 'B', 'title': 'Pastor aeternus and Lumen Gentium 22', 'question': 'Q?',
                   'verdict': 'plausible_concord', 'confidence': 'high', 'source_verified': False, 'summary': 'S.',
                   'texts': [{'label': 'Pastor aeternus', 'refs': ['1839'], 'local': 'excerpt', 'verified': True}],
                   'propositions': [{'id': 'b6-p1', 'ref': '1839', 'year': 1870, 'says': 'The pope is infallible ex cathedra.',
                                     'formal_object': 'revealed', 'assent': 'faith', 'binding_status': 'not_juridical', 'evidence': 'D'}],
                   'matrix': [{'a': 'b6-p1', 'b': 'b6-p2', 'level': 'doctrinal', 'result': 'no_conflict', 'why': 'W.'}],
                   'gaps': [{'what': 'The relatio', 'source': 'Acta', 'settles': 'Scope'}]},
                  {'id': 'B9', 'group': 'B', 'title': 'A sealed case', 'sealed': True}]},
    'documents.json': {'records': [{'id': 'lg', 'title': 'Lumen Gentium', 'coverage': 'excerpts',
                                    'sourceLinks': [{'url': 'https://www.vatican.va/lg.html', 'scope': 'full-document'}]}],
                       'relations': [{'from': 'LG25', 'to': '1839', 'kind': 'reaffirms', 'status': 'editorial relationship',
                                      'note': 'N.', 'evidence': [{'entry': 'LG25', 'quote': 'irreformable'}]}]},
}


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        for name, obj in DATA.items():
            with open(os.path.join(cls.tmp.name, name), 'w', encoding='utf-8') as f:
                json.dump(obj, f)
        cls.D = S.Data(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class References(Fixture):
    def test_numbers_people_cite(self):
        for ref, want in [('1839', ['1839']), ('n. 1839', ['1839']), ('DS 3074', ['1839']), ('DH 3073', ['1839']),
                          ('LG 25', ['LG25']), ('lg25', ['LG25']), ('Suppl. S1', ['S1']), ('S1', ['S1']), ('XYZ 1', [])]:
            self.assertEqual(self.D.resolve(ref), want, ref)

    def test_labels_and_pages(self):
        self.assertEqual([self.D.label(i) for i in ('1839', 'LG25', 'S1')], ['n. 1839', 'LG 25', 'Suppl. S1'])
        self.assertTrue(self.D.url('88*').endswith('/n/88_s/'))


class Tools(Fixture):
    def test_entry_carries_its_weight(self):
        t = S.tool_get_entry(self.D, 'DS 3074', latin=True)
        self.assertIn('Conciliar definition', t)
        self.assertIn('Defined dogma', t)
        self.assertIn('Romanum Pontificem', t)
        self.assertIn('Cited by: LG 25', t)
        self.assertIn('Censure: heretical', S.tool_get_entry(self.D, '299'))
        self.assertIsNone(S.tool_get_entry(self.D, 'nothing'))

    def test_search(self):
        t = S.tool_search(self.D, '"ex cathedra"')
        self.assertIn('2 entries match', t)
        self.assertIn('n. 1839', S.tool_search(self.D, 'infallibility'))
        self.assertNotIn('n. 1839', S.tool_search(self.D, '"ex cathedra"', year_from=1900))
        self.assertIn('No entries match', S.tool_search(self.D, 'zzzz'))

    def test_related_and_cases(self):
        t = S.tool_related(self.D, '1839')
        self.assertIn('reaffirms', t)
        self.assertIn('The papacy', t)
        self.assertIn('Continuity case B6', t)
        c = S.tool_get_case(self.D, 'b6', 'all')
        self.assertIn('research case, not Church teaching', c)
        self.assertIn('assent: faith', c)
        self.assertIn('The relatio', c)
        self.assertIn('B6 Pastor aeternus', S.tool_list_cases(self.D))

    def test_sealed_case_is_never_described(self):
        self.assertIn('B9 A sealed case: sealed', S.tool_list_cases(self.D))
        with self.assertRaises(LookupError):
            S.tool_get_case(self.D, 'B9', 'all')
        self.assertNotIn('B9', S.tool_related(self.D, '1839'))

    def test_citations_follow_the_numbering(self):
        self.assertIn('Deferrari', S.tool_cite(self.D, '1839'))
        lg = S.tool_cite(self.D, 'LG 25')
        self.assertNotIn('Deferrari', lg)
        self.assertIn('Lumen Gentium," Nov. 21, 1964, LG 25', lg)

    def test_rules(self):
        t = S.rules_text(self.D)
        self.assertIn('Development in the same sense', t)
        self.assertIn('P1 Precision', t)


class Protocol(Fixture):
    def test_handshake_and_errors(self):
        srv = S.Server(self.tmp.name)
        r = srv.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}})
        self.assertEqual(r['result']['protocolVersion'], '2025-06-18')
        r = srv.handle({'jsonrpc': '2.0', 'id': 2, 'method': 'initialize', 'params': {'protocolVersion': '1999-01-01'}})
        self.assertEqual(r['result']['protocolVersion'], S.PROTOCOLS[0])
        self.assertIsNone(srv.handle({'jsonrpc': '2.0', 'method': 'notifications/initialized'}))
        self.assertEqual(srv.handle({'jsonrpc': '2.0', 'id': 3, 'method': 'nope'})['error']['code'], -32601)
        r = srv.handle({'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'get_entry', 'arguments': {'ref': 'none'}}})
        self.assertTrue(r['result']['isError'])
        r = srv.handle({'jsonrpc': '2.0', 'id': 5, 'method': 'prompts/get', 'params': {'name': 'test_continuity',
                                                                                     'arguments': {'first': '1839', 'second': 'LG 25'}}})
        self.assertIn('1839 and LG 25', r['result']['messages'][0]['content']['text'])

    def test_every_tool_is_read_only_and_described(self):
        for t in S.TOOLS:
            self.assertTrue(t['annotations']['readOnlyHint'], t['name'])
            self.assertGreater(len(t['description']), 40, t['name'])

    def test_over_stdio(self):
        msgs = [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}},
                {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': 'get_entry', 'arguments': {'ref': 'LG 25'}}}]
        out = subprocess.run([sys.executable, SERVER, '--data', self.tmp.name], input='\n'.join(json.dumps(m) for m in msgs) + '\n',
                             capture_output=True, text=True, encoding='utf-8', timeout=60).stdout.splitlines()
        self.assertEqual(len(out), 2)  # nothing but replies on standard output
        self.assertIn('On the Episcopate', json.loads(out[1])['result']['content'][0]['text'])


if __name__ == '__main__':
    unittest.main()
