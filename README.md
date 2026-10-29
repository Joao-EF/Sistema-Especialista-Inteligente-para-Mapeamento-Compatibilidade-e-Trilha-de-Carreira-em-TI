# Sistema Especialista de Carreiras em TI

Consultor de carreiras baseado em regras com pontuação ponderada (UNIPAC - Inteligência Artificial).
Analisa o perfil do usuário em escala Likert, calcula a compatibilidade com 10 trilhas de TI,
identifica lacunas de competências (skill gaps) e gera um roadmap personalizado.

## Estrutura

- `data/Regras_Carreiras.json` - base de conhecimento (perguntas, pesos, trilhas, níveis)
- `src/motor.py` - motor de inferência (pontuação, ranking, nível e lacunas)
- `src/recomendacao.py` - justificativas, empates parciais e roadmap
- `app.py` - interface web em etapas (Streamlit)

## Como executar

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Para a versão em terminal: `python src/motor.py`

## Fluxo da interface

1. Perfil pessoal → 2. Afinidades técnicas → 3. Objetivos de carreira
4. Resultado (Top 3, gráficos de barras/radar e justificativas)
5. Avaliação de nível na trilha escolhida → 6. Plano de ação (lacunas, roadmap e download)


## Regras de cálculo e interpretação

- Afinidade de 1 a 5 é convertida em -2, -1, 0, 1 e 2. Cada valor multiplica o peso da pergunta para cada trilha. Pesos negativos representam conflitos de perfil.
- A aderência é a soma ponderada positiva dividida pela maior soma possível da trilha, em percentual. Pontuações negativas aparecem como 0%. Esse índice não representa uma probabilidade de contratação ou sucesso.
- O resultado mostra o Top 3. Empates dentro de 5 pontos percentuais são informados; trilhas empatadas na nota de corte ou próximas da primeira também podem ser escolhidas para aprofundamento.
- Quando todas as pontuações são zero, o sistema informa que não identificou afinidade e permite explorar qualquer uma das 10 trilhas. A ordem alfabética não representa preferência nesse caso.
- Júnior, pleno e sênior exigem pelo menos 65% dos requisitos do respectivo nível e aprovação nos níveis anteriores. A análise de lacunas cobre todas as competências de júnior abaixo da experiência mínima, conforme o enunciado.
- O campo `estudos_por_competencia` relaciona cada competência de júnior aos estudos prioritários. Essas relações ficam no JSON, junto com tecnologias, certificações e projetos. Certificações e projetos são sugestões por trilha; a prioridade dos estudos depende das lacunas individuais.

## Testes

Na pasta do projeto, execute:

```bash
python -m unittest discover -s tests -v
```

A suíte verifica a base, 1.000 perfis reproduzíveis, perfis ideais e opostos, perfil misto de dados e web, neutralidade, empates, justificativas, níveis, lacunas, prioridade dos estudos, conteúdo exportado e execução em terminal. Os testes de integração do Streamlit percorrem as seis etapas, todas as 10 trilhas, retorno às etapas, troca de trilha, reinício e resultados de iniciante e sênior.


