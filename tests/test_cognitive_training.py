from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.lexical_training import cognitive_training as c

READY = (importlib.util.find_spec('torch') is not None
         and Path('formal/.lake/build/bin/lexicalDenotation').is_file())
if os.environ.get('NABT_REQUIRE_SHARED_TRAINING') == '1' and not READY:
    raise RuntimeError('Cognitive training requires native definitions and CPU torch')


class ReviewContract(unittest.TestCase):
    def test_reviewed_negatives_bind_exact_bytes_not_unannotated_status(self):
        rows = c.data.dataset()['train']; review = json.loads(c.REVIEW.read_text())
        tokens = c.reviewed_tokens(rows, review)
        self.assertEqual(sum(r['review_status'] == 'UNREVIEWED' for r in tokens), 570)
        self.assertEqual(sum(r['review_status'] == 'REVIEWED_NOT_IN_INSTALLED_INVENTORY' for r in tokens), 78)
        for field, value in [('text_sha256', '0'*64), ('utf8_span', [False, 28]),
                             ('codepoint_span', [12.0, 15]), ('surface', 'بديل')]:
            changed = deepcopy(review); changed['negative_occurrences'][0][field] = value
            with self.assertRaises(ValueError): c.reviewed_tokens(rows, changed)
        changed = deepcopy(rows)
        changed[0]['annotations'][0]['concept_ids'] = ['invented-concept']
        with self.assertRaises(ValueError): c.reviewed_tokens(changed, review)

    def test_positive_cannot_be_relabelled_negative(self):
        rows = c.data.dataset()['train']; review = json.loads(c.REVIEW.read_text())
        row = next(r for r in rows if r['annotations']); annotation = row['annotations'][0]
        review['negative_occurrences'].append({**annotation, 'id': row['id'],
            'status': 'REVIEWED_NOT_IN_INSTALLED_INVENTORY',
            'text_sha256': c.sha256(row['text'].encode()).hexdigest()})
        with self.assertRaises(ValueError): c.reviewed_tokens(rows, review)


@unittest.skipUnless(READY, 'optional CPU training dependencies')
class CognitiveTraining(unittest.TestCase):
    def test_unknown_has_zero_gradient_and_alternatives_share_mass(self):
        import torch
        labels = ['a', 'b', c.runtime.NULL]
        rows = [{'review_status': 'POSITIVE_OR_ACCEPTABLE_ALTERNATIVES', 'gold': ['a', 'b']},
                {'review_status': 'UNREVIEWED', 'gold': [c.runtime.NULL]}]
        logits = torch.tensor([[1., 1., 0.], [100., -100., 200.]], requires_grad=True)
        loss = c.masked_loss(logits, rows, labels); loss.backward()
        self.assertEqual(logits.grad[1].tolist(), [0., 0., 0.])
        expected = -torch.log(torch.softmax(logits.detach()[0], 0)[:2].sum())
        self.assertAlmostEqual(float(loss.detach()), float(expected), places=6)
        altered = logits.detach().clone(); altered[1] *= -100
        self.assertEqual(float(c.masked_loss(altered, rows, labels)), float(loss.detach()))

    def test_projected_gradients_match_geometric_oracle(self):
        import torch
        merged, conflicts, count = c.project_gradients(
            [torch.tensor([1., 0.]), torch.tensor([-1., 1.])], torch.Generator().manual_seed(3))
        # Projections are (1/2,1/2) and (0,1), hence their average (1/4,3/4).
        self.assertTrue(torch.allclose(merged, torch.tensor([.25, .75])))
        self.assertEqual((conflicts, count), (2, 2))
        merged, conflicts, _ = c.project_gradients(
            [torch.tensor([1., 0.]), torch.tensor([0., 1.])], torch.Generator().manual_seed(3))
        self.assertTrue(torch.allclose(merged, torch.tensor([.5, .5])))
        self.assertEqual(conflicts, 0)

    def test_real_encoder_updates_and_portable_parity_without_test_selection(self):
        with tempfile.TemporaryDirectory() as root:
            result = c.train_run(Path(root)/'run', epochs=2)
            protocol = json.loads((Path(root)/'run/protocol.json').read_text())
            for field, path in [('review_sha256', c.REVIEW), ('fresh_sha256', c.FRESH)]:
                self.assertEqual(result[field], c.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(protocol[field], result[field])
        self.assertEqual(result['optimizer_steps'], 2)
        self.assertGreater(result['shared_encoder_delta_l2'], 0)
        self.assertFalse(result['protocol']['test_selection'])
        for evaluation in result['evaluation'].values():
            self.assertLess(evaluation['portable_max_abs_error'], 1e-4)
            self.assertGreater(evaluation['neural']['unreviewed_tokens'], 0)
        self.assertFalse(result['predictions_grant_authority'])

    def test_changed_annotations_cannot_complete_with_rebound_identity(self):
        save = c.previous.save
        for replaced in ('review', 'fresh'):
            with self.subTest(input=replaced), tempfile.TemporaryDirectory() as root:
                paths = {name: Path(root)/(name+'.json') for name in ('review', 'fresh')}
                for name, original in [('review', c.REVIEW), ('fresh', c.FRESH)]:
                    paths[name].write_bytes(original.read_bytes())
                retained = {name: c.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
                def replace_after_protocol(path, value):
                    save(path, value)
                    if path.name == 'protocol.json':
                        # Valid JSON, different bytes: no parser failure may
                        # hide a provenance mismatch after the initial read.
                        with paths[replaced].open('ab') as stream:
                            stream.write(b'\n')
                run = Path(root)/'run'
                with patch.object(c, 'REVIEW', paths['review']), patch.object(c, 'FRESH', paths['fresh']), \
                     patch.object(c.previous, 'save', side_effect=replace_after_protocol):
                    with self.assertRaisesRegex(ValueError, 'Training input changed: '+replaced):
                        c.train_run(run, epochs=1)
                self.assertFalse((run/'FIRST_TEST.json').exists())
                protocol = json.loads((run/'protocol.json').read_text())
                for name, digest in retained.items():
                    self.assertEqual(protocol[name+'_sha256'], digest)


if __name__ == '__main__': unittest.main()
