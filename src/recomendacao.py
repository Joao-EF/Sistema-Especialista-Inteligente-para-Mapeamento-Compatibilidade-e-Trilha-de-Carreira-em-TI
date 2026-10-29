"""Funções de apoio à interface: justificativas, empates parciais e roadmap.

Tudo aqui é calculado a partir da base de conhecimento (JSON) e das respostas
do usuário; nenhuma regra de carreira fica fixa no código.
"""


def detectar_empate(ranking, base):
    """Retorna as trilhas (além da 1ª) cuja pontuação está dentro da margem de empate."""
    margem = base["parametros"]["margem_empate_pct"]
    if len(ranking) < 2:
        return []
    topo = ranking[0]["percentual"]
    return [r for r in ranking[1:] if topo - r["percentual"] <= margem]


def justificar_trilha(trilha, respostas, base, n=3):
    """Lista as respostas que mais ajudaram e as que mais penalizaram uma trilha."""
    escala = base["escala_respostas"]
    contribuicoes = []

    for pergunta in base["perguntas"]:
        id_pergunta = pergunta["id"]
        if id_pergunta not in respostas or trilha not in pergunta["pesos"]:
            continue
        pontos = escala[str(respostas[id_pergunta])] * pergunta["pesos"][trilha]
        if pontos != 0:
            contribuicoes.append(
                {
                    "id": id_pergunta,
                    "texto": pergunta["texto"],
                    "resposta": respostas[id_pergunta],
                    "pontos": pontos,
                }
            )

    a_favor = sorted((c for c in contribuicoes if c["pontos"] > 0), key=lambda c: -c["pontos"])[:n]
    contra = sorted((c for c in contribuicoes if c["pontos"] < 0), key=lambda c: c["pontos"])[:n]
    return a_favor, contra


def gerar_roadmap(trilha, lacunas, base):
    """Prioriza estudos por relações explícitas na base de conhecimento."""
    info = base["trilhas"][trilha]
    estudos = []
    for pergunta in info["avaliacao_nivel"]:
        if pergunta.get("skill") in lacunas:
            estudos.extend(info["estudos_por_competencia"].get(pergunta["id"], [pergunta["skill"]]))
    priorizadas = list(dict.fromkeys(estudos))
    return {
        "estudar_primeiro": list(lacunas),
        "tecnologias": priorizadas + [t for t in info["tecnologias"] if t not in priorizadas],
        "certificacoes": info["certificacoes"],
        "projetos": info["projetos_portfolio"],
    }


def plano_em_markdown(trilha, nivel, percentuais, lacunas, roadmap, base, pct_compatibilidade):
    """Monta o plano de ação em Markdown para download."""
    info = base["trilhas"][trilha]
    nomes_tiers = {item["tier"]: item["nome"] for item in base["niveis"][1:]}
    nome_junior = base["niveis"][1]["nome"]

    linhas = [
        f"# Plano de ação - {info['nome']}",
        "",
        info["descricao"],
        "",
        f"- **Compatibilidade com a trilha:** {pct_compatibilidade}%",
        f"- **Nível estimado:** {nivel}",
    ]
    for tier, pct in percentuais.items():
        linhas.append(f"- Requisitos de {nomes_tiers[tier]} atendidos: {pct}%")

    linhas += ["", f"## Lacunas para o nível {nome_junior}", ""]
    if lacunas:
        linhas += [f"- {skill}" for skill in lacunas]
    else:
        linhas.append(f"Nenhuma lacuna nas competências de nível {nome_junior}.")

    linhas += ["", "## Tecnologias para estudar (em ordem de prioridade)", ""]
    linhas += [f"{i}. {t}" for i, t in enumerate(roadmap["tecnologias"], start=1)]

    linhas += ["", "## Certificações", ""]
    linhas += [f"- {c}" for c in roadmap["certificacoes"]]

    linhas += ["", "## Projetos para o portfólio no GitHub", ""]
    linhas += [f"- {p}" for p in roadmap["projetos"]]

    return "\n".join(linhas) + "\n"

