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


if __name__ == "__main__":
    base = carregar_base()
    n = base["parametros"]["top_n"]

    print("Sistema Especialista de Carreiras em TI")
    respostas = perguntar(base)

    print(f"\n=== Suas {n} trilhas mais compatíveis ===")
    for i, item in enumerate(top_n(gerar_ranking(respostas, base), n), start=1):
        print(f"{i}º {item['nome']} - {item['percentual']}%")