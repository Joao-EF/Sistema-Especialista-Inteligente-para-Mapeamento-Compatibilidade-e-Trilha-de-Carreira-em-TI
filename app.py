"""Fase 4 - Interface web (Streamlit) em formato wizard.

Executar com:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import motor, recomendacao

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="centered")

ROTULOS_PADRAO = {"1": "Nada", "2": "Pouco", "3": "Neutro", "4": "Bastante", "5": "Muito"}
NOMES_ETAPAS_FINAIS = ["Resultado", "Avaliação de nível", "Plano de ação"]


# ----------------------------------------------------------------------------
# Base de conhecimento
# ----------------------------------------------------------------------------
def localizar_base():
    """Acha o JSON em data/ ignorando maiúsculas/minúsculas (Windows x Linux)."""
    pasta = Path(__file__).resolve().parent / "data"
    for arquivo in pasta.glob("*.json"):
        if arquivo.name.lower() == "regras_carreiras.json":
            return arquivo
    raise FileNotFoundError(f"regras_carreiras.json não encontrado em {pasta}")


@st.cache_data
def carregar_base(caminho):
    return motor.carregar_base(caminho)


# ----------------------------------------------------------------------------
# Estado e navegação
# ----------------------------------------------------------------------------
def iniciar_estado():
    st.session_state.setdefault("etapa", 0)
    st.session_state.setdefault("respostas", {})
    st.session_state.setdefault("trilha", None)
    st.session_state.setdefault("exp", {})
    st.session_state.setdefault("exp_trilha", None)


def ir_para(etapa):
    st.session_state.etapa = etapa


def reiniciar():
    for chave in list(st.session_state.keys()):
        del st.session_state[chave]


def salvar_resposta(chave_widget, destino, id_pergunta):
    st.session_state[destino][id_pergunta] = st.session_state[chave_widget]


def salvar_trilha(chave_widget):
    st.session_state.trilha = st.session_state[chave_widget]


def navegacao(pode_avancar, rotulo_avancar="Avançar ▶"):
    etapa = st.session_state.etapa
    esquerda, direita = st.columns(2)
    with esquerda:
        if etapa > 0:
            st.button("◀ Voltar", on_click=ir_para, args=(etapa - 1,))
    with direita:
        st.button(rotulo_avancar, type="primary", disabled=not pode_avancar, on_click=ir_para, args=(etapa + 1,))
    if not pode_avancar:
        st.caption("Responda todas as perguntas para continuar.")


def pergunta_escala(destino, id_pergunta, texto, opcoes, rotulos, horizontal=True):
    atual = st.session_state[destino].get(id_pergunta)
    chave = f"{destino}_{id_pergunta}"
    st.radio(
        f"**{id_pergunta}.** {texto}",
        options=opcoes,
        index=opcoes.index(atual) if atual is not None else None,
        format_func=lambda v: f"{v} · {rotulos.get(str(v), v)}",
        horizontal=horizontal,
        key=chave,
        on_change=salvar_resposta,
        args=(chave, destino, id_pergunta),
    )


# ----------------------------------------------------------------------------
# Gráficos
# ----------------------------------------------------------------------------
def grafico_barras(ranking, n_destaque):
    ordenado = list(reversed(ranking))
    cores = ["#1f77b4" if r["posicao"] <= n_destaque else "#b0b7c3" for r in ordenado]
    fig = go.Figure(
        go.Bar(
            x=[r["percentual"] for r in ordenado],
            y=[r["nome"] for r in ordenado],
            orientation="h",
            marker_color=cores,
            text=[f"{r['percentual']}%" for r in ordenado],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Compatibilidade (%)"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
    )
    return fig


def grafico_radar(ranking):
    nomes = [r["nome"] for r in ranking]
    valores = [r["percentual"] for r in ranking]
    fig = go.Figure(
        go.Scatterpolar(r=valores + valores[:1], theta=nomes + nomes[:1], fill="toself", name="Compatibilidade")
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=460,
    )
    return fig


# ----------------------------------------------------------------------------
# Etapas
# ----------------------------------------------------------------------------
def etapa_questionario(base, id_grupo):
    escala = sorted(int(k) for k in base["escala_respostas"])
    rotulos = base.get("rotulos_escala", ROTULOS_PADRAO)
    st.caption(f"Responda de {escala[0]} a {escala[-1]} ({escala[0]} = {rotulos.get(str(escala[0]), '')}, "
               f"{escala[-1]} = {rotulos.get(str(escala[-1]), '')}).")

    perguntas = [p for p in base["perguntas"] if p["grupo"] == id_grupo]
    for pergunta in perguntas:
        pergunta_escala("respostas", pergunta["id"], pergunta["texto"], escala, rotulos)

    respondidas = all(p["id"] in st.session_state.respostas for p in perguntas)
    navegacao(respondidas)


def etapa_resultado(base):
    n = base["parametros"]["top_n"]
    respostas = st.session_state.respostas
    ranking = motor.gerar_ranking(respostas, base)
    for posicao, item in enumerate(ranking, start=1):
        item["posicao"] = posicao
    melhores = motor.top_n(ranking, n)

    sem_afinidade = ranking[0]["percentual"] == 0
    st.subheader("Resultado sem afinidade identificada" if sem_afinidade else f"Suas {n} trilhas mais compatíveis")
    st.caption("Percentuais são índices de aderência às regras, não probabilidades de sucesso profissional.")
    if sem_afinidade:
        st.info("Nenhuma trilha obteve pontuação positiva. A ordem abaixo é apenas alfabética; escolha uma área para explorar ou revise suas respostas.")
    colunas = st.columns(n)
    for coluna, item in zip(colunas, melhores):
        coluna.metric(f"{item['posicao']}º lugar", f"{item['percentual']}%", item["nome"], delta_color="off")

    # tratamento de empates parciais e de perfis pouco definidos
    empatadas = recomendacao.detectar_empate(ranking, base)
    if empatadas:
        nomes = ", ".join(r["nome"] for r in empatadas)
        st.info(
            f"**Empate parcial:** {ranking[0]['nome']} está a no máximo "
            f"{base['parametros']['margem_empate_pct']} pontos percentuais de {nomes}. "
            "Seu perfil combina características dessas trilhas, vale explorar todas."
        )
    if ranking[0]["percentual"] < base["parametros"]["limiar_recomendacao_pct"]:
        st.warning(
            "Nenhuma trilha passou de "
            f"{base['parametros']['limiar_recomendacao_pct']}% de compatibilidade. "
            "Seu perfil é bastante variado; considere revisar suas respostas ou testar mais de uma área."
        )

    aba_barras, aba_radar, aba_tabela = st.tabs(["📊 Barras", "🕸️ Radar", "📋 Tabela"])
    with aba_barras:
        st.plotly_chart(grafico_barras(ranking, n))
    with aba_radar:
        st.plotly_chart(grafico_radar(ranking))
    with aba_tabela:
        tabela = pd.DataFrame(
            {
                "Posição": [r["posicao"] for r in ranking],
                "Trilha": [r["nome"] for r in ranking],
                "Compatibilidade": [r["percentual"] for r in ranking],
                "Pontos": [r["pontos"] for r in ranking],
            }
        )
        st.dataframe(
            tabela,
            hide_index=True,
            column_config={
                "Compatibilidade": st.column_config.ProgressColumn(
                    "Compatibilidade", min_value=0, max_value=100, format="%.1f%%"
                )
            },
        )

    st.subheader("Por que essas trilhas?")
    for item in melhores:
        with st.expander(f"{item['posicao']}º · {item['nome']} ({item['percentual']}%)"):
            st.write(base["trilhas"][item["trilha"]]["descricao"])
            a_favor, contra = recomendacao.justificar_trilha(item["trilha"], respostas, base)
            if a_favor:
                st.markdown("**✅ O que mais pesou a favor:**")
                for c in a_favor:
                    st.markdown(f"- {c['texto']} *(sua resposta: {c['resposta']})*")
            if contra:
                st.markdown("**⚠️ O que mais pesou contra:**")
                for c in contra:
                    st.markdown(f"- {c['texto']} *(sua resposta: {c['resposta']})*")

    # escolha da trilha para a avaliação de nível
    corte = melhores[-1]["percentual"]
    candidatas = ranking if sem_afinidade else [r for r in ranking if r["percentual"] >= corte or r in empatadas]
    ids_melhores = [m["trilha"] for m in candidatas]
    if st.session_state.trilha not in ids_melhores:
        st.session_state.trilha = ids_melhores[0]
        st.session_state.exp = {}
    nomes_por_id = {m["trilha"]: f"{m['nome']} - {m['percentual']}%" for m in candidatas}

    st.subheader("Qual trilha você quer aprofundar?")
    st.radio(
        "Trilha para avaliar seu nível",
        options=ids_melhores,
        index=ids_melhores.index(st.session_state.trilha),
        format_func=lambda t: nomes_por_id[t],
        key="widget_trilha",
        on_change=salvar_trilha,
        args=("widget_trilha",),
    )
    navegacao(True, "Avaliar meu nível ▶")


def etapa_avaliacao(base):
    trilha = st.session_state.trilha
    info = base["trilhas"][trilha]

    # os ids E01..E10 se repetem entre trilhas, então o estado é reiniciado ao trocar de trilha
    if st.session_state.exp_trilha != trilha:
        st.session_state.exp = {}
        st.session_state.exp_trilha = trilha

    st.subheader(f"Avaliação de nível: {info['nome']}")
    escala = sorted(int(k) for k in base["escala_experiencia"])
    rotulos = base["escala_experiencia"]
    st.caption("Informe sua experiência real em cada competência. Seja honesto: o plano de ação depende disso.")

    perguntas = info["avaliacao_nivel"]
    for item in base["niveis"][1:]:
        do_nivel = [p for p in perguntas if p["nivel"] == item["tier"]]
        if not do_nivel:
            continue
        st.markdown(f"#### Nível {item['nome']}")
        for pergunta in do_nivel:
            texto = pergunta["texto"]
            if "skill" in pergunta:
                texto = f"**{pergunta['skill']}** — {texto}"
            chave_estado = f"exp_{trilha}"
            atual = st.session_state.exp.get(pergunta["id"])
            chave = f"{chave_estado}_{pergunta['id']}"
            st.radio(
                texto,
                options=escala,
                index=escala.index(atual) if atual is not None else None,
                format_func=lambda v: f"{v} · {rotulos[str(v)]}",
                key=chave,
                on_change=salvar_resposta,
                args=(chave, "exp", pergunta["id"]),
            )

    respondidas = all(p["id"] in st.session_state.exp for p in perguntas)
    navegacao(respondidas, "Gerar plano de ação ▶")


def etapa_plano(base):
    trilha = st.session_state.trilha
    info = base["trilhas"][trilha]
    respostas_exp = st.session_state.exp

    ranking = motor.gerar_ranking(st.session_state.respostas, base)
    pct_trilha = next(r["percentual"] for r in ranking if r["trilha"] == trilha)

    nivel, percentuais = motor.calcular_nivel(trilha, respostas_exp, base)
    lacunas = motor.identificar_lacunas(trilha, respostas_exp, base)
    roadmap = recomendacao.gerar_roadmap(trilha, lacunas, base)
    nomes_tiers = {item["tier"]: item["nome"] for item in base["niveis"][1:]}
    nome_junior = base["niveis"][1]["nome"]

    st.subheader(f"Seu plano de ação em {info['nome']}")
    st.write(info["descricao"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Compatibilidade", f"{pct_trilha}%")
    c2.metric("Nível estimado", nivel)
    c3.metric(f"Lacunas p/ {nome_junior}", len(lacunas))

    st.markdown("#### Requisitos atendidos por nível")
    for tier, pct in percentuais.items():
        st.progress(min(pct, 100.0) / 100, text=f"{nomes_tiers[tier]}: {pct}%")

    st.markdown(f"#### Análise de lacunas (nível {nome_junior})")
    minimo = base["niveis"][1]["experiencia_minima"]
    linhas = [
        {
            "Competência": p["skill"],
            "Sua experiência": respostas_exp[p["id"]],
            "Mínimo esperado": minimo,
            "Situação": "✅ Atendida" if respostas_exp[p["id"]] >= minimo else "❌ Lacuna",
        }
        for p in info["avaliacao_nivel"]
        if p["nivel"] == base["niveis"][1]["tier"]
    ]
    st.dataframe(pd.DataFrame(linhas), hide_index=True)

    if lacunas:
        st.warning(f"Você tem {len(lacunas)} lacuna(s) para chegar ao nível {nome_junior}. Comece por elas.")
    else:
        st.success(f"Você já atende todas as competências de nível {nome_junior}!")

    st.markdown("#### Roadmap personalizado")
    aba_estudo, aba_cert, aba_portfolio = st.tabs(["📚 O que estudar", "🎓 Certificações", "💻 Portfólio no GitHub"])
    with aba_estudo:
        if roadmap["estudar_primeiro"]:
            st.markdown("**Estude primeiro (suas lacunas):**")
            for skill in roadmap["estudar_primeiro"]:
                st.markdown(f"- {skill}")
        st.markdown("**Tecnologias da trilha (em ordem de prioridade):**")
        for i, tecnologia in enumerate(roadmap["tecnologias"], start=1):
            st.markdown(f"{i}. {tecnologia}")
    with aba_cert:
        for certificacao in roadmap["certificacoes"]:
            st.markdown(f"- {certificacao}")
    with aba_portfolio:
        st.markdown("**Projetos para colocar no seu GitHub:**")
        for projeto in roadmap["projetos"]:
            st.markdown(f"- {projeto}")

    st.download_button(
        "⬇️ Baixar plano em Markdown",
        data=recomendacao.plano_em_markdown(trilha, nivel, percentuais, lacunas, roadmap, base, pct_trilha),
        file_name=f"plano_{trilha}.md",
        mime="text/markdown",
    )

    esquerda, direita = st.columns(2)
    with esquerda:
        st.button("◀ Voltar", on_click=ir_para, args=(st.session_state.etapa - 1,))
    with direita:
        st.button("🔄 Refazer o teste", on_click=reiniciar)


# ----------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------
def main():
    try:
        base = carregar_base(str(localizar_base()))
    except (FileNotFoundError, ValueError, KeyError) as erro:
        st.error(str(erro))
        st.stop()

    iniciar_estado()

    grupos = sorted(base["grupos"].items(), key=lambda g: g[1]["ordem"])
    titulos = [info["titulo"] for _, info in grupos] + NOMES_ETAPAS_FINAIS
    etapa = min(st.session_state.etapa, len(titulos) - 1)

    st.title("🧭 Consultor de Carreiras em TI")
    st.progress((etapa + 1) / len(titulos), text=f"Etapa {etapa + 1} de {len(titulos)}")
    st.header(titulos[etapa])

    with st.sidebar:
        st.markdown("### Sobre")
        st.write(
            "Sistema especialista baseado em regras com pontuação ponderada. "
            "Seu perfil é comparado com 10 trilhas de TI e gera um plano de ação."
        )
        st.button("🔄 Reiniciar", on_click=reiniciar, key="reiniciar_lateral")

    if etapa < len(grupos):
        etapa_questionario(base, grupos[etapa][0])
    elif etapa == len(grupos):
        etapa_resultado(base)
    elif etapa == len(grupos) + 1:
        etapa_avaliacao(base)
    else:
        etapa_plano(base)


main()
