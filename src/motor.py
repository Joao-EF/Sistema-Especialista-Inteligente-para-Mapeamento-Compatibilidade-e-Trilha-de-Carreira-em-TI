"""Motor de inferência: calcula a compatibilidade (%) entre o perfil do usuário e as trilhas de TI.

O motor não conhece nenhuma carreira. Todo o conhecimento vem do JSON.
"""
import json
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "data" / "regras_carreiras.json"


def carregar_base(caminho=CAMINHO_PADRAO):
    """Lê o JSON da base de conhecimento e devolve um dicionário."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def calcular_pontuacoes(respostas, base):
    """Soma, para cada trilha, (valor da resposta na escala x peso da pergunta).

    respostas: dict {"Q01": 5, "Q02": 1, ...} (números de 1 a 5).
    Perguntas sem resposta são ignoradas (equivale a neutro: contribuem com 0).
    """
    escala = base["escala_respostas"]
    pontuacoes = {trilha: 0 for trilha in base["trilhas"]}

    for pergunta in base["perguntas"]:
        if pergunta["id"] not in respostas:
            continue

        chave = str(respostas[pergunta["id"]])  # JSON só aceita chaves em texto
        if chave not in escala:
            raise ValueError(f"Resposta inválida em {pergunta['id']}: {respostas[pergunta['id']]}")
        valor = escala[chave]

        for trilha, peso in pergunta["pesos"].items():
            pontuacoes[trilha] += valor * peso

    return pontuacoes


def calcular_maximos(base):
    """Pontuação máxima possível de cada trilha.

    Em cada pergunta, escolhe-se a resposta que mais ajuda a trilha:
    peso positivo -> maior valor da escala; peso negativo -> menor valor.
    """
    valores = base["escala_respostas"].values()
    maximos = {trilha: 0 for trilha in base["trilhas"]}

    for pergunta in base["perguntas"]:
        for trilha, peso in pergunta["pesos"].items():
            maximos[trilha] += max(v * peso for v in valores)

    return maximos


def normalizar(pontuacoes, maximos):
    """Converte pontuações em porcentagem (0 a 100) dividindo pelo máximo da trilha.

    Pontuação negativa vira 0%: o perfil é incompatível com a trilha.
    """
    percentuais = {}
    for trilha, pontos in pontuacoes.items():
        maximo = maximos[trilha]
        percentuais[trilha] = round(max(0, pontos) / maximo * 100, 1) if maximo > 0 else 0.0
    return percentuais


def gerar_ranking(respostas, base):
    """Devolve todas as trilhas ordenadas da mais para a menos compatível."""
    pontuacoes = calcular_pontuacoes(respostas, base)
    percentuais = normalizar(pontuacoes, calcular_maximos(base))

    ranking = [
        {"trilha": t, "nome": base["trilhas"][t]["nome"], "percentual": pct, "pontos": pontuacoes[t]}
        for t, pct in percentuais.items()
    ]
    # Desempate: maior percentual primeiro; se igual, ordem alfabética do nome
    return sorted(ranking, key=lambda r: (-r["percentual"], r["nome"]))


def top_n(ranking, n):
    return ranking[:n]


if __name__ == "__main__":
    base = carregar_base()
    n = base["parametros"]["top_n"]

    # Perfil de teste: gosta de dados e matemática, não gosta de interface
    respostas_teste = {"Q01": 5, "Q02": 1, "Q03": 5, "Q04": 5, "Q12": 1, "Q13": 5, "Q14": 4}

    for i, item in enumerate(top_n(gerar_ranking(respostas_teste, base), n), start=1):
        print(f"{i}º {item['nome']} - {item['percentual']}%")