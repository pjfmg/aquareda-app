import base64
from io import BytesIO
from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def test_empty_start(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'REDA_InterfaceGrafica_Streamlit.py')).run()
        self.assertFalse(app.exception)

    def test_import_missing_fields_edit_priority_create_columns(self):
        output = BytesIO()
        pd.DataFrame({'Nome': ['Recurso fictício'], 'Data': ['01/10/2026']}).to_excel(output, index=False)
        encoded = base64.b64encode(output.getvalue()).decode()
        code = Path('REDA_InterfaceGrafica_Streamlit.py').read_text()
        code = code.replace("upload = st.file_uploader('Carregar Excel (.xlsx)', type=['xlsx'])", f"import base64\nupload = BytesIO(base64.b64decode('{encoded}'))")
        app = AppTest.from_string(code).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.text_input), 5)
        priority = next(s for s in app.selectbox if s.label == 'PRIORIDADE LOCAL')
        priority.select('Alta').run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['notes'].loc[0, 'PRIORIDADE LOCAL'], 'Alta')
        app.text_area[0].set_value('Confirmar licença').run()
        self.assertEqual(app.session_state['notes'].loc[0, 'BLOQUEIOS'], 'Confirmar licença')


    def test_restore_warning_blocks_legacy_notes(self):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame({'TÍTULO': ['Fictício']}).to_excel(writer, sheet_name='Recursos', index=False)
            pd.DataFrame({'ID LOCAL': ['antigo']}).to_excel(writer, sheet_name='Revisao_local', index=False)
        encoded = base64.b64encode(output.getvalue()).decode()
        code = Path('REDA_InterfaceGrafica_Streamlit.py').read_text()
        code = code.replace("upload = st.file_uploader('Carregar Excel (.xlsx)', type=['xlsx'])", f"import base64\nupload = BytesIO(base64.b64decode('{encoded}'))")
        app = AppTest.from_string(code).run()
        app.checkbox[0].check().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)
        self.assertTrue(app.error)
        self.assertIn('bloqueada', app.error[0].value)
        self.assertEqual(len(app.text_area), 0)
        self.assertTrue(app.session_state['notes']['BLOQUEIOS'].eq('').all())
