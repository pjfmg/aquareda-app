"""Run with python -m unittest test_faq.py; exercises the real Streamlit UI."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class FaqTests(unittest.TestCase):
    def test_complete_bilingual_faq_before_upload_and_on_rerun(self):
        app = AppTest.from_file(str(Path(__file__).with_name('REDA_InterfaceGrafica_Streamlit.py'))).run()
        expected = [
            ('Que ficheiro posso carregar?', 'What file can I upload?'),
            ('Que campos posso editar?', 'Which fields can I edit?'),
            ('Como guardo as alterações?', 'How do I save my changes?'),
            ('O que faço se o carregamento falhar?', 'What should I do if the upload fails?'),
            ('Esta ajuda aplica-se à app Apple?', 'Does this help apply to the Apple app?'),
        ]
        for _ in range(2):
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.header[0].value, 'Perguntas frequentes / Frequently asked questions')
            self.assertEqual(len(app.expander), 5)
            for expander, (pt, en) in zip(app.expander, expected):
                self.assertEqual(expander.label, f'{pt} / {en}')
                self.assertEqual(len(expander.markdown), 2)
                self.assertTrue(all(item.value.strip() for item in expander.markdown))
            self.assertIn('TÍTULO, AUTOR/FONTE, ORGANIZAÇÃO, DURAÇÃO DO VÍDEO', app.expander[0].markdown[1].value)
            self.assertIn('does not overwrite the original file', app.expander[2].markdown[1].value)
            self.assertIn('does not describe features of an Apple version', app.expander[4].markdown[1].value)
            self.assertEqual(len(app.get('file_uploader')), 1)
            self.assertEqual(len(app.get('download_button')), 0)
            app.run()


if __name__ == '__main__':
    unittest.main()
