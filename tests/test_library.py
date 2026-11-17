import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build'))
from build import load_all, check, compact, Problems
from library import source_key, validate_library, validate_relations

class SourceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_all()
        cls.order, problems = check(cls.data)
        assert not problems, problems
        compact(cls.data, cls.order)
        cls.library = cls.data['library']
        cls.records = {r['id']:r for r in cls.library['records']}

    def test_every_entry_has_exactly_one_source(self):
        all_ids = [eid for r in self.records.values() for eid in r['entryIds']]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertEqual(set(all_ids), set(self.order))

    def test_abbreviations_do_not_merge_pontificates(self):
        a = {'id':'DCE6','era':122}
        b = {'id':'DCE1','era':123}
        self.assertNotEqual(source_key(a), source_key(b))
        self.assertNotEqual(self.library['entryMap']['DCE6'], self.library['entryMap']['DCE1'])

    def test_dated_addresses_stay_separate(self):
        self.assertNotEqual(source_key({'id':'AD19790128','era':122}), source_key({'id':'AD19810221','era':122}))

    def test_all_vatican_ii_documents_have_sources_without_inventing_text(self):
        records = [r for r in self.records.values() if r['collection']=='Vatican II']
        self.assertEqual(len(records),16)
        for rid in ['cd','pc','ot','ge','im']:
            self.assertEqual(self.records[rid]['entryIds'],[])
            self.assertEqual(self.records[rid]['coverage'],'none')
        self.assertIn('LGNP',self.records['lg']['entryIds'])

    def test_unknown_extent_is_not_presented_as_complete(self):
        self.assertTrue(all(r['coverage'] != 'full-text' for r in self.records.values()))
        self.assertTrue(all(r['review']['status']=='unreviewed' for r in self.records.values() if r['grouping']=='inferred'))

    def test_full_text_requires_evidence(self):
        data=copy.deepcopy(self.data)
        data['document_metadata'][0]['coverage']='full-text'
        problems=Problems();validate_library(data,self.order,problems)
        self.assertTrue(any('completenessEvidence' in p for p in problems))

    def test_full_text_cannot_use_a_bare_verified_flag(self):
        data=copy.deepcopy(self.data)
        data['document_metadata'][0].update(coverage='full-text',completenessEvidence={'verified':True})
        problems=Problems();validate_library(data,self.order,problems)
        self.assertTrue(any('completenessEvidence' in p for p in problems))

    def test_duplicate_and_missing_references_fail_validation(self):
        data=copy.deepcopy(self.data)
        data['document_metadata'][1]['entryIds'] += [data['document_metadata'][0]['entryIds'][0], 'MISSING-ID']
        problems=Problems();validate_library(data,self.order,problems)
        self.assertEqual(sum('entry missing or assigned twice' in p for p in problems),2)

    def test_unsafe_source_urls_fail_validation(self):
        data=copy.deepcopy(self.data)
        data['document_metadata'][0]['sourceLinks'][0]['url']='javascript:alert(1)'
        problems=Problems();validate_library(data,self.order,problems)
        self.assertTrue(any('HTTPS' in p for p in problems))

class RelationshipTests(unittest.TestCase):
    def test_changed_quotation_fails(self):
        data=load_all();order,_=check(data)
        data['relations'][0]['evidence'][0]['quote']='An invented quotation.'
        problems=Problems();validate_relations(data,order,problems)
        self.assertTrue(any('not present' in p for p in problems))

    def test_both_endpoints_require_evidence(self):
        data=load_all();order,_=check(data)
        data['relations'][0]['evidence']=data['relations'][0]['evidence'][:1]
        problems=Problems();validate_relations(data,order,problems)
        self.assertTrue(any('both endpoints' in p for p in problems))

    def test_no_self_relationships(self):
        data=load_all();order,_=check(data)
        data['relations'][0]['to']=data['relations'][0]['from']
        problems=Problems();validate_relations(data,order,problems)
        self.assertTrue(any('distinct existing entries' in p for p in problems))

if __name__=='__main__':unittest.main()
