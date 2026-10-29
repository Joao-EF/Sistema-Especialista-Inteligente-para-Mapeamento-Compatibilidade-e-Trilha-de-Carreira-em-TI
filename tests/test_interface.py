"""Teste de integracao da interface usando os controles reais do Streamlit."""
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

class InterfaceTests(unittest.TestCase):
    def iniciar(self, valor=5):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertTrue(next(b for b in at.button if b.label=='Avançar ▶').disabled)
        for _ in range(3):
            for r in at.radio:r.set_value(valor)
            at.run()
            next(b for b in at.button if b.label=='Avançar ▶').click().run()
            self.assertFalse(at.exception)
        return at

    def test_fluxo_dez_trilhas_e_reinicio(self):
        at=self.iniciar(3)
        self.assertEqual(len(at.radio[0].options),10)
        self.assertTrue(at.info)
        base=__import__('json').loads((Path(__file__).resolve().parents[1]/'data/Regras_Carreiras.json').read_text(encoding='utf-8'))
        for trilha in base['trilhas']:
            at.radio[0].set_value(trilha).run()
            next(b for b in at.button if b.label=='Avaliar meu nível ▶').click().run()
            self.assertEqual(len(at.radio),10)
            self.assertTrue(next(b for b in at.button if b.label=='Gerar plano de ação ▶').disabled)
            for r in at.radio:r.set_value(0)
            at.run()
            next(b for b in at.button if b.label=='Gerar plano de ação ▶').click().run()
            self.assertFalse(at.exception)
            self.assertEqual(at.metric[1].value,'Iniciante')
            self.assertEqual(at.metric[2].value,'6')
            self.assertTrue(at.get('download_button'))
            next(b for b in at.button if b.label=='◀ Voltar').click().run()
            self.assertTrue(all(r.value==0 for r in at.radio))
            next(b for b in at.button if b.label=='◀ Voltar').click().run()
        next(b for b in at.button if b.label=='🔄 Reiniciar').click().run()
        self.assertTrue(all(r.value is None for r in at.radio))
        self.assertEqual(at.session_state['respostas'],{})

    def test_perfil_positivo_e_nivel_senior(self):
        at=self.iniciar(5)
        next(b for b in at.button if b.label=='Avaliar meu nível ▶').click().run()
        for r in at.radio:r.set_value(4)
        at.run()
        next(b for b in at.button if b.label=='Gerar plano de ação ▶').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[1].value,'Sênior')
        self.assertEqual(at.metric[2].value,'0')

if __name__=='__main__':unittest.main()
