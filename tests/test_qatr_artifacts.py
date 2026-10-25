import copy
import unittest
from tools.check_qatr_artifacts import check_bindings


class QatrArtifactTests(unittest.TestCase):
    def setUp(self):
        self.word=dict(address=[5,1,1],csv_rows=[99,100],text_sha256='a'*64,qatr='noun:damma',case='raf')
        self.examples=[dict(split='test',words=[self.word])]
        self.record=dict(address=[5,1,1],csv_rows=[99,100],text_sha256='a'*64,gold_reading='noun:damma',
                         gold_case='raf',reading='noun:damma',case_ranking='raf',authority='NONE')
        self.teacher=dict(queries=[dict(kind='noun',mark='damma',rows=[dict(id=1)])])

    def test_all_source_identity_fields_are_checked(self):
        self.assertEqual(check_bindings(self.examples,[self.record],self.teacher),1)
        for key,value in [('address',[5,1,2]),('csv_rows',[100,101]),('text_sha256','b'*64),
                          ('gold_reading','noun:kasra'),('gold_case','nasb'),('authority','LEAN_ACCEPTED')]:
            changed=copy.deepcopy(self.record);changed[key]=value
            with self.assertRaisesRegex(ValueError,'source binding'):
                check_bindings(self.examples,[changed],self.teacher)

    def test_boolean_identity_not_integer_alias(self):
        changed=copy.deepcopy(self.record);changed['address'][1]=True
        with self.assertRaisesRegex(ValueError,'integer'):
            check_bindings(self.examples,[changed],self.teacher)

    def test_missing_occurrence_or_unknown_output_rejected(self):
        with self.assertRaisesRegex(ValueError,'denominator'):
            check_bindings(self.examples,[],self.teacher)
        changed=copy.deepcopy(self.record);changed['reading']='noun:invented'
        with self.assertRaisesRegex(ValueError,'unknown reading'):
            check_bindings(self.examples,[changed],self.teacher)
