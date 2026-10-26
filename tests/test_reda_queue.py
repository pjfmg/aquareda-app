from datetime import date
from io import BytesIO
import unittest
import pandas as pd
from openpyxl import load_workbook as open_xlsx
from reda_queue import load_workbook, new_notes, queue_view, export_workbook, parse_request_date


def workbook(frame):
    output = BytesIO()
    frame.to_excel(output, index=False)
    return output.getvalue()


class QueueTests(unittest.TestCase):
    def test_missing_fields_are_reported_not_invented(self):
        source, notes, mapping, missing = load_workbook(workbook(pd.DataFrame({'Outro': ['X', None]})))
        self.assertEqual(len(missing), 5)
        self.assertEqual(mapping, {})
        self.assertEqual(list(source.columns), ['Outro'])
        self.assertTrue(notes['ESTADO LOCAL'].eq('').all())
        self.assertTrue(notes['PRIORIDADE LOCAL'].eq('').all())
        self.assertEqual(notes['ID LOCAL'].nunique(), len(source))

    def test_normalized_headers_and_incomplete_values(self):
        source, notes, mapping, missing = load_workbook(workbook(pd.DataFrame({' titulo ': ['A', None], 'Autor/Fonte': [None, 'B'], 'Outra': [1, 2]})))
        self.assertEqual(mapping['TÍTULO'], ' titulo ')
        view = queue_view(source, notes, mapping)
        self.assertIn('AUTOR/FONTE', view.loc[0, 'CAMPOS POR COMPLETAR / CONFIRMAR'])
        self.assertIn('Sem título', view.loc[1, 'TÍTULO / REFERÊNCIA'])
        self.assertEqual(source.loc[0, 'Outra'], 1)

    def test_priority_then_age_then_original_order(self):
        source = pd.DataFrame({'Data': ['01/01/2026', '01/10/2026', None, '01/01/2025', '01/10/2026']})
        notes = new_notes(5)
        notes['PRIORIDADE LOCAL'] = ['Normal', 'Urgente', 'Urgente', '', 'Urgente']
        result = queue_view(source, notes, {}, 'Data', today=date(2026, 10, 26))
        self.assertEqual(list(result.index), [1, 4, 2, 0, 3])
        self.assertEqual(result.loc[0, 'PEDIDO ANTIGO'], 'Sim')
        self.assertEqual(result.loc[2, 'PEDIDO ANTIGO'], 'Por confirmar')

    def test_dates_unknown_invalid_future_and_numeric(self):
        source = pd.DataFrame({'Data': ['31/02/2026', 46000, '2027-01-01', '', '2026-10-25']})
        view = queue_view(source, new_notes(5), {}, 'Data', today=date(2026, 10, 26))
        self.assertTrue(view.loc[0:3, 'DIAS EM ESPERA'].isna().all())
        self.assertEqual(view.loc[4, 'DIAS EM ESPERA'], 1)
        self.assertEqual(parse_request_date(date(2026, 1, 1))[0], date(2026, 1, 1))

    def test_export_restore_preserves_source_notes_ids_and_extra_columns(self):
        source = pd.DataFrame({'TÍTULO': ['Mesmo', 'Mesmo'], 'Extra': ['a', 'b']})
        notes = new_notes(2)
        notes.loc[1, ['BLOQUEIOS', 'PRÓXIMO PASSO']] = ['Falta licença', 'Consultar autor']
        view = queue_view(source, notes, {})
        result = export_workbook(source, notes, view)
        restored, saved, _, _ = load_workbook(result, 'Recursos', True)
        pd.testing.assert_frame_equal(restored, source, check_dtype=False)
        pd.testing.assert_frame_equal(saved, notes, check_dtype=False)
        _, fresh, _, _ = load_workbook(result, 'Recursos', False)
        self.assertTrue(fresh['BLOQUEIOS'].eq('').all())

    def test_source_state_never_becomes_local_state(self):
        source = pd.DataFrame({'Estado': ['Aprovado', 'Pendente']})
        notes = new_notes(2)
        view = queue_view(source, notes, {}, state_column='Estado')
        self.assertEqual(list(view['ESTADO NA FONTE']), ['Aprovado', 'Pendente'])
        self.assertTrue(view['ESTADO LOCAL'].eq('').all())

    def test_invalid_workbook_and_invalid_saved_queue(self):
        with self.assertRaises(Exception):
            load_workbook(b'not excel')
        with self.assertRaises(ValueError):
            load_workbook(workbook(pd.DataFrame({'A': [1]})), 0, True)

    def test_empty_sheet(self):
        source, notes, mapping, _ = load_workbook(workbook(pd.DataFrame(columns=['TÍTULO'])))
        self.assertTrue(queue_view(source, notes, mapping).empty)

    def test_export_does_not_create_formulas(self):
        source = pd.DataFrame({'TÍTULO': ['=1+1']})
        notes = new_notes(1)
        raw = export_workbook(source, notes, queue_view(source, notes, {}))
        self.assertEqual(open_xlsx(BytesIO(raw))['Recursos']['A2'].data_type, 's')



class AssociationTests(unittest.TestCase):
    def setUp(self):
        # Títulos repetidos: a associação nunca depende do título.
        self.source = pd.DataFrame({'TÍTULO': ['Mesmo', 'Mesmo', 'Outro'],
                                    'Extra': ['a', 'b', 'c']})
        self.notes = new_notes(3)
        self.notes['BLOQUEIOS'] = ['Nota A', 'Nota B', 'Nota C']
        raw = export_workbook(self.source, self.notes, queue_view(self.source, self.notes, {}))
        self.frames = pd.read_excel(BytesIO(raw), sheet_name=None, dtype=object)

    def raw(self):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for name, frame in self.frames.items():
                frame.to_excel(writer, sheet_name=name, index=False)
        return output.getvalue()

    def restore(self):
        return load_workbook(self.raw(), 'Recursos', True)

    def test_resources_reordered_independently(self):
        self.frames['Recursos'] = self.frames['Recursos'].iloc[[2, 0, 1]]
        source, notes, _, _ = self.restore()
        self.assertEqual(list(source['Extra']), ['c', 'a', 'b'])
        self.assertEqual(list(notes['BLOQUEIOS']), ['Nota C', 'Nota A', 'Nota B'])

    def test_notes_reordered_independently(self):
        self.frames['Revisao_local'] = self.frames['Revisao_local'].iloc[::-1]
        _, notes, _, _ = self.restore()
        pd.testing.assert_frame_equal(notes, self.notes, check_dtype=False)

    def test_both_sheets_differently_reordered(self):
        self.frames['Recursos'] = self.frames['Recursos'].iloc[[1, 2, 0]]
        self.frames['Revisao_local'] = self.frames['Revisao_local'].iloc[[2, 0, 1]]
        source, notes, _, _ = self.restore()
        self.assertEqual(list(zip(source['Extra'], notes['BLOQUEIOS'])),
                         [('b', 'Nota B'), ('c', 'Nota C'), ('a', 'Nota A')])

    def test_duplicate_or_blank_ids_in_either_sheet_block_all_notes(self):
        from reda_queue import RESOURCE_ID
        for sheet, column in [('Recursos', RESOURCE_ID), ('Revisao_local', 'ID LOCAL')]:
            for value in ['', self.frames[sheet].loc[0, column]]:
                with self.subTest(sheet=sheet, value=value):
                    old = self.frames[sheet].loc[1, column]
                    self.frames[sheet].loc[1, column] = value
                    with self.assertRaisesRegex(ValueError, 'bloqueada'):
                        self.restore()
                    self.frames[sheet].loc[1, column] = old

    def test_deletion_in_either_sheet_blocks(self):
        for sheet in ['Recursos', 'Revisao_local']:
            original = self.frames[sheet]
            self.frames[sheet] = original.iloc[:-1]
            with self.subTest(sheet=sheet), self.assertRaisesRegex(ValueError, 'bloqueada'):
                self.restore()
            self.frames[sheet] = original

    def test_insertion_in_either_sheet_blocks(self):
        from reda_queue import RESOURCE_ID
        for sheet, column in [('Recursos', RESOURCE_ID), ('Revisao_local', 'ID LOCAL')]:
            original = self.frames[sheet]
            added = original.iloc[[0]].copy()
            added[column] = 'novo-id-ficticio'
            self.frames[sheet] = pd.concat([original, added], ignore_index=True)
            with self.subTest(sheet=sheet), self.assertRaisesRegex(ValueError, 'bloqueada'):
                self.restore()
            self.frames[sheet] = original

    def test_replacement_with_same_row_count_blocks(self):
        from reda_queue import RESOURCE_ID
        self.frames['Recursos'].loc[0, RESOURCE_ID] = 'outro-id'
        with self.assertRaisesRegex(ValueError, 'bloqueada'):
            self.restore()

    def test_sorting_content_without_ids_blocks(self):
        self.frames['Recursos']['Extra'] = ['b', 'a', 'c']
        with self.assertRaisesRegex(ValueError, 'conteúdo'):
            self.restore()

    def test_external_content_edit_blocks(self):
        self.frames['Recursos'].loc[0, 'TÍTULO'] = 'Substituído'
        with self.assertRaisesRegex(ValueError, 'conteúdo'):
            self.restore()

    def test_legacy_export_is_blocked_but_can_start_fresh(self):
        from reda_queue import RESOURCE_ID, RESOURCE_HASH
        self.frames['Recursos'] = self.frames['Recursos'].drop(columns=RESOURCE_ID)
        self.frames['Revisao_local'] = self.frames['Revisao_local'].drop(columns=RESOURCE_HASH)
        with self.assertRaisesRegex(ValueError, 'antiga'):
            self.restore()
        _, notes, _, _ = load_workbook(self.raw(), 'Recursos', False)
        self.assertTrue(notes['BLOQUEIOS'].eq('').all())

    def test_human_edits_survive_successive_exports(self):
        source, notes, mapping, _ = self.restore()
        source.loc[1, 'TÍTULO'] = 'Edição humana'
        notes.loc[1, 'PRÓXIMO PASSO'] = 'Verificar licença'
        raw = export_workbook(source, notes, queue_view(source, notes, mapping))
        restored, saved, _, _ = load_workbook(raw, 'Recursos', True)
        pd.testing.assert_frame_equal(restored, source, check_dtype=False)
        pd.testing.assert_frame_equal(saved, notes, check_dtype=False)

    def test_excel_types_formulas_blanks_and_empty_catalog_roundtrip(self):
        for source in [pd.DataFrame({'TÍTULO': ['=1+1', 'NA', None],
                                     'Data': [date(2026, 1, 1), None, None],
                                     'Número': [1.0, 2.5, None]}),
                       pd.DataFrame(columns=['TÍTULO'])]:
            notes = new_notes(len(source))
            raw = export_workbook(source, notes, queue_view(source, notes, {}))
            _, restored_notes, _, _ = load_workbook(raw, 'Recursos', True)
            pd.testing.assert_frame_equal(restored_notes, notes, check_dtype=False)
