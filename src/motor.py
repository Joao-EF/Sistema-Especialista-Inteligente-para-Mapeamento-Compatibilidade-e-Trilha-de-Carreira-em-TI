import json
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "regras_carreiras.json"


def carregar_base(caminho=CAMINHO_PADRAO):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def perguntar(base):
    escala = base["escala_respostas"]
    opcoes = sorted(int(k) for k in escala)
    respostas = {}

    grupos = sorted(base["grupos"].items(), key=lambda g: g[1]["ordem"])
    for id_grupo, info_grupo in grupos:
        print(f"\n=== {info_grupo['titulo']} ===")
        print(f"Responda de {opcoes[0]} a {opcoes[-1]} ({opcoes[0]} = nada, {opcoes[-1]} = muito)\n")

        for pergunta in base["perguntas"]:
            if pergunta["grupo"] != id_grupo:
                continue

            while True:
                entrada = input(f"[{pergunta['id']}] {pergunta['texto']}\n> ").strip()
                if entrada.isdigit() and int(entrada) in opcoes:
                    respostas[pergunta["id"]] = int(entrada)
                    break
                print(f"Resposta inválida. Digite um número de {opcoes[0]} a {opcoes[-1]}.\n")

    return respostas


def calcular_pontuacoes(respostas, base):
    escala = base["escala_respostas"]
    pontuacoes = {trilha: 0 for trilha in base["trilhas"]}

    for pergunta in base["perguntas"]:
        if pergunta["id"] not in respostas:
            continue

        chave = str(respostas[pergunta["id"]])
        if chave not in escala:
            raise ValueError(f"Resposta inválida em {pergunta['id']}: {respostas[pergunta['id']]}")
        valor = escala[chave]

        for trilha, peso in pergunta["pesos"].items():
            pontuacoes[trilha] += valor * peso

    return pontuacoes


def calcular_maximos(base):
    valores = base["escala_respostas"].values()
    maximos = {trilha: 0 for trilha in base["trilhas"]}

    for pergunta in base["perguntas"]:
        for trilha, peso in pergunta["pesos"].items():
            maximos[trilha] += max(v * peso for v in valores)

    return maximos


def normalizar(pontuacoes, maximos):
    percentuais = {}
    for trilha, pontos in pontuacoes.items():
        maximo = maximos[trilha]
        percentuais[trilha] = round(max(0, pontos) / maximo * 100, 1) if maximo > 0 else 0.0
    return percentuais


def gerar_ranking(respostas, base):
    pontuacoes = calcular_pontuacoes(respostas, base)
    percentuais = normalizar(pontuacoes, calcular_maximos(base))

    ranking = [
        {"trilha": t, "nome": base["trilhas"][t]["nome"], "percentual": pct, "pontos": pontuacoes[t]}
        for t, pct in percentuais.items()
    ]
    return sorted(ranking, key=lambda r: (-r["percentual"], r["nome"]))


def top_n(ranking, n):
    return ranking[:n]


def escolher_trilha(melhores):
    print("\nEscolha a trilha para avaliar o seu nível (Enter = 1ª opção):")
    for i, item in enumerate(melhores, start=1):
        print(f"{i}) {item['nome']} - {item['percentual']}%")

    while True:
        entrada = input("> ").strip()
        if entrada == "":
            return melhores[0]["trilha"]
        if entrada.isdigit() and 1 <= int(entrada) <= len(melhores):
            return melhores[int(entrada) - 1]["trilha"]
        print(f"Opção inválida. Digite um número de 1 a {len(melhores)} ou pressione Enter.")


def perguntar_experiencia(trilha, base):
    escala = base["escala_experiencia"]
    opcoes = sorted(int(k) for k in escala)
    respostas = {}

    print(f"\n=== Avaliação de nível: {base['trilhas'][trilha]['nome']} ===")
    for chave in sorted(escala, key=int):
        print(f"  {chave} = {escala[chave]}")

    for pergunta in base["trilhas"][trilha]["avaliacao_nivel"]:
        while True:
            entrada = input(f"\n[{pergunta['id']}] {pergunta['texto']}\n> ").strip()
            if entrada.isdigit() and int(entrada) in opcoes:
                respostas[pergunta["id"]] = int(entrada)
                break
            print(f"Resposta inválida. Digite um número de {opcoes[0]} a {opcoes[-1]}.")

    return respostas


def calcular_nivel(trilha, respostas_exp, base):
    niveis = base["niveis"]
    minimas = {item["tier"]: item["experiencia_minima"] for item in niveis[1:]}
    total = {}
    atendidas = {}

    for pergunta in base["trilhas"][trilha]["avaliacao_nivel"]:
        tier = pergunta["nivel"]
        total[tier] = total.get(tier, 0) + 1
        if respostas_exp[pergunta["id"]] >= minimas[tier]:
            atendidas[tier] = atendidas.get(tier, 0) + 1

    percentuais = {tier: round(atendidas.get(tier, 0) / total[tier] * 100, 1) for tier in total}

    nivel_atual = niveis[0]["nome"]
    for item in niveis[1:]:
        if percentuais.get(item["tier"], 0) >= item["minimo_pct"]:
            nivel_atual = item["nome"]
        else:
            break

    return nivel_atual, percentuais


def identificar_lacunas(trilha, respostas_exp, base):
    nivel_junior = base["niveis"][1]

    return [
        pergunta["skill"]
        for pergunta in base["trilhas"][trilha]["avaliacao_nivel"]
        if pergunta["nivel"] == nivel_junior["tier"]
        and respostas_exp[pergunta["id"]] < nivel_junior["experiencia_minima"]
    ]


if __name__ == "__main__":
    base = carregar_base()
    n = base["parametros"]["top_n"]

    print("Sistema Especialista de Carreiras em TI")
    respostas = perguntar(base)

    melhores = top_n(gerar_ranking(respostas, base), n)
    print(f"\n=== Suas {n} trilhas mais compatíveis ===")
    for i, item in enumerate(melhores, start=1):
        print(f"{i}º {item['nome']} - {item['percentual']}%")

    trilha = escolher_trilha(melhores)
    respostas_exp = perguntar_experiencia(trilha, base)
    nivel, percentuais = calcular_nivel(trilha, respostas_exp, base)
    lacunas = identificar_lacunas(trilha, respostas_exp, base)

    nomes_tiers = {item["tier"]: item["nome"] for item in base["niveis"][1:]}
    print(f"\n=== Resultado em {base['trilhas'][trilha]['nome']} ===")
    print(f"Nível estimado: {nivel}")
    for tier, pct in percentuais.items():
        print(f"  Requisitos de {nomes_tiers[tier]} atendidos: {pct}%")

    nome_junior = base["niveis"][1]["nome"]
    if lacunas:
        print(f"\nLacunas para o nível {nome_junior}:")
        for skill in lacunas:
            print(f"  - {skill}")
    else:
        print(f"\nNenhuma lacuna nas competências de nível {nome_junior}.")
