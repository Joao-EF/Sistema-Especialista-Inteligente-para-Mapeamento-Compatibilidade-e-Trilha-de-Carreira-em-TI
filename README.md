# Sistema Especialista de Carreiras em TI

Consultor de carreiras baseado em regras com pontuação ponderada (UNIPAC - Inteligência Artificial).
Analisa o perfil do usuário em escala Likert, calcula a compatibilidade com 10 trilhas de TI,
identifica lacunas de competências (skill gaps) e gera um roadmap personalizado.

## Estrutura

- `data/regras_carreiras.json` - base de conhecimento (perguntas, pesos, trilhas, níveis)
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
