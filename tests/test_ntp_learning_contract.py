"""Source isolation and reusable A116 differentiation contracts."""
from copy import deepcopy
import importlib.util
import unittest
from unittest.mock import patch

from nabt.errors import NabtError
from tools.lexical_training import ntp_recursive as net, train_ntp_recursive as training


class RecursiveContract(unittest.TestCase):
    def test_text_limit_precedes_reader_and_preserves_exact_boundary(self):
        for text in ('كَ' * 65, 'x' * 257):
            with patch.object(net, 'parse_word', side_effect=AssertionError('reader reached')):
                with self.assertRaises(ValueError):
                    net.source({'text': text})
        text, cells, _ = net.source({'text': 'كَ' * 64})
        self.assertEqual(len(text.encode()), net.MAX_TEXT_BYTES)
        self.assertEqual(len(cells), net.MAX_CELLS)
        self.assertEqual(net.render_word(cells), text)

    def test_scores_do_not_silently_truncate_invalid_tensors(self):
        model = net.load()
        for key, value in (('bits', [[]] * net.DIM), ('bias', [True] * net.DIM)):
            changed = deepcopy(model)
            changed['parameters'][key] = value
            with self.assertRaises(ValueError):
                net.scores(changed, [84, 8, 4])
        changed = deepcopy(model)
        changed['parameters']['bits'][0][0] = 10 ** 1000
        with self.assertRaises(ValueError):
            net.validate_model(changed)
        for value in (None, True, 'A' * 64, '0' * 63):
            changed = deepcopy(model)
            changed['protocol_sha256'] = value
            with self.assertRaises(ValueError):
                net.validate_model(changed)

    def test_protocol_types_and_paths_are_not_inferred(self):
        protocol, _ = training.inputs()
        for key, value in (('seed', True), ('dimension', True), ('epochs', True),
                           ('learning_rate', True), ('learning_rate', float('nan')),
                           ('source', '/tmp/other-data.json'), ('authority', 'APPROVED')):
            changed = deepcopy(protocol)
            changed[key] = value
            with self.assertRaises(ValueError, msg=key):
                training.validate_protocol(changed)

    def test_duplicate_sources_unknown_labels_and_root_leaks_rejected(self):
        protocol, splits = training.inputs()
        rows = [row for split in splits.values() for row in split]
        mutations = []
        duplicated = deepcopy(rows)
        duplicated.append(deepcopy(rows[0]))
        mutations.append((protocol, duplicated))
        unknown = deepcopy(rows)
        unknown[0]['labels']['reading'] = 'unreviewed'
        mutations.append((protocol, unknown))
        missing = deepcopy(rows)
        del missing[0]['labels']['attachment']
        mutations.append((protocol, missing))
        boolean_cell = deepcopy(rows)
        boolean_cell[0]['cells'][0] = True
        mutations.append((protocol, boolean_cell))
        leaked = deepcopy(protocol)
        leaked['test_roots'].append(leaked['train_roots'][0])
        mutations.append((leaked, rows))
        for candidate_protocol, candidate_rows in mutations:
            with self.assertRaises((ValueError, NabtError)):
                training.validate_rows(candidate_rows, candidate_protocol)

    def test_fit_admits_only_exact_retained_training_rows(self):
        protocol, splits = training.inputs()
        invalid = [splits['test'], splits['development'], splits['train'][:-1],
                   list(reversed(splits['train'])), splits['train'] + splits['test'][:1]]
        altered = deepcopy(splits['train'])
        altered[0]['labels']['reading'] = 'fuila_marks'
        invalid.append(altered)
        with patch.object(training, 'initialize', side_effect=AssertionError('fit started')):
            for rows in invalid:
                with self.assertRaises(ValueError):
                    training.fit(protocol, rows)
            changed = dict(protocol, epochs=1)
            with self.assertRaises(ValueError):
                training.fit(changed, splits['train'])


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'training-only NumPy required')
class SharedDifferentiation(unittest.TestCase):
    def test_model_export_does_not_mutate_label_contract(self):
        protocol, _ = training.inputs()
        p = training.initialize(protocol['seed'])
        expected = deepcopy(net.LABELS)
        exported = training.model(p, protocol)
        exported['labels']['reading'][0] = 'changed'
        self.assertEqual(net.LABELS, expected)
        self.assertEqual(training.model(p, protocol)['labels'], expected)

    def test_portable_word_and_group_composition_match_numpy(self):
        import numpy as np
        p = training.initialize(116)
        portable = {k: v.tolist() for k, v in p.items()}
        groups = [[100, 91], [88, 111, 44]]
        words = [net.encode_state(portable, cells) for cells in groups]
        expected = net.join_states(portable, words[0], words[1])
        actual, _ = training.group_tape(p, groups)
        self.assertLess(float(np.max(np.abs(actual - expected))), 1e-13)
        reversed_state, _ = training.group_tape(p, list(reversed(groups)))
        self.assertGreater(float(np.linalg.norm(actual - reversed_state)), 1e-6)
        for cells in ([], [True], [-1], [116], [0] * 65):
            with self.assertRaises((ValueError, NabtError)):
                training.encode_tape({}, cells)


if __name__ == '__main__':
    unittest.main()
