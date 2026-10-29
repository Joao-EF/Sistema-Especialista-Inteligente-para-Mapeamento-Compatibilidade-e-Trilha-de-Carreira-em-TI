import unittest
import random
from src import motor, recomendacao

class MotorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = motor.carregar_base()

    def test_base(self):
        b = self.base
        self.assertEqual(len(b['trilhas']), 10)
        self.assertEqual(len({p['id'] for p in b['perguntas']}), len(b['perguntas']))
        for p in b['perguntas']:
            self.assertIn(p['grupo'], b['grupos'])
            self.assertTrue(set(p['pesos']) <= set(b['trilhas']))
        for info in b['trilhas'].values():
            for p in info['avaliacao_nivel']:
                if p['nivel']=='junior':
                    self.assertTrue(info['estudos_por_competencia'][p['id']])

    def test_perfis_ideais_e_opostos(self):
        b=self.base
        for t in b['trilhas']:
            ideal={p['id']:5 if p['pesos'].get(t,0)>=0 else 1 for p in b['perguntas']}
            oposto={q:6-v for q,v in ideal.items()}
            scores={r['trilha']:r['percentual'] for r in motor.gerar_ranking(ideal,b)}
            self.assertEqual(scores[t],100)
            scores={r['trilha']:r['percentual'] for r in motor.gerar_ranking(oposto,b)}
            self.assertEqual(scores[t],0)

    def test_neutro_empates_e_justificativas(self):
        b=self.base
        respostas={p['id']:3 for p in b['perguntas']}
        ranking=motor.gerar_ranking(respostas,b)
        self.assertTrue(all(r['percentual']==0 for r in ranking))
        self.assertEqual(len(recomendacao.detectar_empate(ranking,b)),9)
        for t in b['trilhas']:
            self.assertEqual(recomendacao.justificar_trilha(t,respostas,b),([],[]))
        synthetic=[{'percentual':80},{'percentual':75},{'percentual':74.9}]
        self.assertEqual(recomendacao.detectar_empate(synthetic,b),synthetic[1:2])

    def test_1000_perfis(self):
        rng=random.Random(42); b=self.base
        for _ in range(1000):
            respostas={p['id']:rng.randint(1,5) for p in b['perguntas']}
            ranking=motor.gerar_ranking(respostas,b)
            self.assertEqual(len(ranking),10)
            self.assertTrue(all(0<=r['percentual']<=100 for r in ranking))
            self.assertEqual([r['percentual'] for r in ranking],sorted([r['percentual'] for r in ranking],reverse=True))
            for t in b['trilhas']:
                favor,contra=recomendacao.justificar_trilha(t,respostas,b)
                self.assertTrue(all(c['pontos']>0 for c in favor))
                self.assertTrue(all(c['pontos']<0 for c in contra))

    def test_niveis_lacunas_e_download(self):
        b=self.base
        for t,info in b['trilhas'].items():
            for valor,esperado in [(0,'Iniciante'),(1,'Iniciante'),(2,'Júnior'),(3,'Pleno'),(4,'Sênior')]:
                respostas={p['id']:valor for p in info['avaliacao_nivel']}
                nivel,pct=motor.calcular_nivel(t,respostas,b)
                self.assertEqual(nivel,esperado)
                lacunas=motor.identificar_lacunas(t,respostas,b)
                self.assertEqual(len(lacunas),6 if valor<2 else 0)
                road=recomendacao.gerar_roadmap(t,lacunas,b)
                doc=recomendacao.plano_em_markdown(t,nivel,pct,lacunas,road,b,80)
                self.assertTrue(all(g in doc for g in lacunas))
                self.assertEqual(len(road['tecnologias']),len(set(road['tecnologias'])))
            # Conhecimentos avancados nao podem dispensar os fundamentos junior.
            respostas={p['id']:0 if p['nivel']=='junior' else 4 for p in info['avaliacao_nivel']}
            self.assertEqual(motor.calcular_nivel(t,respostas,b)[0],'Iniciante')
            for p in info['avaliacao_nivel']:
                if p['nivel']=='junior':
                    road=recomendacao.gerar_roadmap(t,[p['skill']],b)
                    estudos=info['estudos_por_competencia'][p['id']]
                    self.assertEqual(road['tecnologias'][:len(estudos)],estudos)

    def test_perfil_ambiguo_dados_e_web(self):
        b=self.base
        respostas={p["id"]:3 for p in b["perguntas"]}
        for q in ["Q01","Q02","Q03","Q04","Q11","Q12","Q13"]:
            respostas[q]=5
        ranking=motor.gerar_ranking(respostas,b)
        self.assertTrue(any(r["trilha"]=="cientista_dados" for r in ranking[:3]))
        self.assertTrue(any(r["trilha"]=="frontend_ux" for r in ranking[:3]))
        for r in ranking[:3]:
            favor,contra=recomendacao.justificar_trilha(r["trilha"],respostas,b)
            self.assertTrue(favor)
            self.assertTrue(all(c["resposta"]==respostas[c["id"]] for c in favor+contra))

    def test_terminal(self):
        import io, runpy
        from unittest.mock import patch
        # Uma entrada invalida, 27 respostas, escolha padrao e 10 competencias.
        entradas=["invalida"]+["5"]*len(self.base["perguntas"])+[""]+["0"]*10
        with patch("builtins.input",side_effect=entradas),patch("sys.stdout",new_callable=io.StringIO) as saida:
            runpy.run_path("src/motor.py",run_name="__main__")
        self.assertIn("Nível estimado: Iniciante",saida.getvalue())
        self.assertIn("Resposta inválida",saida.getvalue())

    def test_resposta_invalida(self):
        with self.assertRaises(ValueError): motor.calcular_pontuacoes({'Q01':6},self.base)

if __name__=='__main__': unittest.main()
