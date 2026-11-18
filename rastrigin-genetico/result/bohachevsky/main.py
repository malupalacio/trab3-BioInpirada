import random
import math

# --- CONFIGURAÇÕES E PARÂMETROS ---
N_ILHAS = 4
TEMP_SIMULACAO = 1000      # Número de gerações
TAMANHO_GRADE = 10         # Grade 10x10 = 100 posições por ilha
DIMENSOES = 2              # Função 2D (x1, x2)
LIMITES = (-100, 100)      # Limites do domínio da Bohachevsky

R = [2.2, 2.25, 2.5, 2.75]
D = 0.2                     # Taxa de migração
X_INICIAL = [0.5, 0.5, 0.5, 0.5]
SIGMAS_BASE = [0.01, 0.1, 0.5, 1.5]


# --- FUNÇÃO DE BOHACHEVSKY ---
def bohachevsky(x):
    x1 = x[0]
    x2 = x[1]

    term1 = x1**2
    term2 = 2 * x2**2
    term3 = -0.3 * math.cos(3 * math.pi * x1)
    term4 = -0.4 * math.cos(4 * math.pi * x2)

    return term1 + term2 + term3 + term4 + 0.7


def criar_individuo(ilha):
    posicao = [
        random.uniform(LIMITES[0], LIMITES[1])
        for _ in range(DIMENSOES)
    ]

    sigma = SIGMAS_BASE[ilha] * random.uniform(0.8, 1.2)
    fit = bohachevsky(posicao)

    ind = {
        "x": posicao,
        "sigma": sigma,
        "fitness": fit,
        "historico": [{
            "geracao": 0,
            "ilha_origem": ilha,
            "pais": "Ancestral Inicial",
            "x": posicao.copy(),
            "sigma": sigma,
            "fitness": fit
        }]
    }

    return ind


def criar_grade():
    return [
        [None for _ in range(TAMANHO_GRADE)]
        for _ in range(TAMANHO_GRADE)
    ]


def obter_posicoes_ocupadas(grade):
    return [
        (i, j)
        for i in range(TAMANHO_GRADE)
        for j in range(TAMANHO_GRADE)
        if grade[i][j] is not None
    ]


def obter_posicoes_vazias(grade):
    return [
        (i, j)
        for i in range(TAMANHO_GRADE)
        for j in range(TAMANHO_GRADE)
        if grade[i][j] is None
    ]


# --- REPRODUÇÃO COM RASTREAMENTO DETALHADO ---
def reproduzir(
    pai1,
    pai2,
    ilha_p1,
    ilha_p2,
    ilha_filho,
    geracao_atual
):
    novo_x = [
        0.5 * (p1 + p2)
        for p1, p2 in zip(pai1["x"], pai2["x"])
    ]

    novo_sigma = (
        0.5 * (pai1["sigma"] + pai2["sigma"])
        * math.exp(random.gauss(0, 0.1))
    )

    for k in range(DIMENSOES):
        novo_x[k] += random.gauss(0, novo_sigma)

        novo_x[k] = max(
            LIMITES[0],
            min(LIMITES[1], novo_x[k])
        )

    fit = bohachevsky(novo_x)

    # Seleciona o histórico do pai mais apto
    pai_principal = (
        pai1
        if pai1["fitness"] < pai2["fitness"]
        else pai2
    )

    novo_historico = [
        dict(passo)
        for passo in pai_principal["historico"]
    ]

    # Registra o cruzamento atual
    origem_str = (
        f"Ilha {ilha_p1} x Ilha {ilha_p2}"
        if ilha_p1 != ilha_p2
        else f"Ilha {ilha_p1} (Local)"
    )

    novo_historico.append({
        "geracao": geracao_atual,
        "ilha_origem": ilha_filho,
        "pais": origem_str,
        "x": novo_x.copy(),
        "sigma": novo_sigma,
        "fitness": fit
    })

    return {
        "x": novo_x,
        "sigma": novo_sigma,
        "fitness": fit,
        "historico": novo_historico
    }


def nascer_individuos(
    grade,
    ilha,
    quantidade,
    grades,
    geracao_atual
):
    vazios = random.sample(
        obter_posicoes_vazias(grade),
        quantidade
    )

    for i, j in vazios:

        eh_migracao = random.random() < D

        if eh_migracao:

            outras = [
                k for k in range(N_ILHAS)
                if k != ilha
            ]

            ilha_ext = random.choice(outras)

            ocupados_ext = obter_posicoes_ocupadas(
                grades[ilha_ext]
            )

            ocupados_loc = obter_posicoes_ocupadas(
                grade
            )

            if ocupados_loc and ocupados_ext:

                pos_loc = random.choice(ocupados_loc)
                pos_ext = random.choice(ocupados_ext)

                p_loc = grade[
                    pos_loc[0]
                ][
                    pos_loc[1]
                ]

                p_ext = grades[ilha_ext][
                    pos_ext[0]
                ][
                    pos_ext[1]
                ]

                if p_loc is not None and p_ext is not None:

                    grade[i][j] = reproduzir(
                        p_loc,
                        p_ext,
                        ilha,
                        ilha_ext,
                        ilha,
                        geracao_atual
                    )

                else:
                    grade[i][j] = criar_individuo(ilha)

            else:
                grade[i][j] = criar_individuo(ilha)

        else:

            ocupados = obter_posicoes_ocupadas(grade)

            if len(ocupados) >= 2:

                p1_pos, p2_pos = random.sample(
                    ocupados,
                    2
                )

                p1 = grade[
                    p1_pos[0]
                ][
                    p1_pos[1]
                ]

                p2 = grade[
                    p2_pos[0]
                ][
                    p2_pos[1]
                ]

                if p1 is not None and p2 is not None:

                    grade[i][j] = reproduzir(
                        p1,
                        p2,
                        ilha,
                        ilha,
                        ilha,
                        geracao_atual
                    )

                else:
                    grade[i][j] = criar_individuo(ilha)

            else:
                grade[i][j] = criar_individuo(ilha)


def remover_individuos(grade, quantidade):

    ocupados = obter_posicoes_ocupadas(grade)

    ocupados.sort(
        key=lambda pos: grade[pos[0]][pos[1]]["fitness"],
        reverse=True
    )

    for i, j in ocupados[:quantidade]:
        grade[i][j] = None


def atualizar_grade(
    grade,
    x_novo,
    ilha,
    grades,
    geracao_atual
):

    esperados = round(
        x_novo * TAMANHO_GRADE * TAMANHO_GRADE
    )

    atuais = len(
        obter_posicoes_ocupadas(grade)
    )

    dif = esperados - atuais

    if dif > 0:

        nascer_individuos(
            grade,
            ilha,
            dif,
            grades,
            geracao_atual
        )

    elif dif < 0:

        remover_individuos(
            grade,
            abs(dif)
        )

    # Turnover Geracional (10%)
    ocupados = obter_posicoes_ocupadas(grade)

    if len(ocupados) > 5:

        qtd_turnover = max(
            1,
            int(len(ocupados) * 0.10)
        )

        remover_individuos(
            grade,
            qtd_turnover
        )

        nascer_individuos(
            grade,
            ilha,
            qtd_turnover,
            grades,
            geracao_atual
        )


def main():

    X = X_INICIAL.copy()

    grades = [
        criar_grade()
        for _ in range(N_ILHAS)
    ]

    # --- POPULAÇÃO INICIAL ---
    for i in range(N_ILHAS):

        qtd = round(
            X[i] * TAMANHO_GRADE * TAMANHO_GRADE
        )

        posicoes = random.sample(
            [
                (r, c)
                for r in range(TAMANHO_GRADE)
                for c in range(TAMANHO_GRADE)
            ],
            qtd
        )

        for r, c in posicoes:
            grades[i][r][c] = criar_individuo(i)

    melhor_global = None

    # --- SIMULAÇÃO ---
    for g in range(TEMP_SIMULACAO):

        crescimento = [
            R[i] * X[i] * (1 - X[i])
            for i in range(N_ILHAS)
        ]

        X_novo = []

        for i in range(N_ILHAS):

            imigrantes = sum(
                crescimento[j]
                for j in range(N_ILHAS)
                if j != i
            )

            xi_novo = (
                (1 - D) * crescimento[i]
                + (D / (N_ILHAS - 1)) * imigrantes
            )

            X_novo.append(
                max(
                    0.01,
                    min(0.99, xi_novo)
                )
            )

        X = X_novo

        for i in range(N_ILHAS):

            atualizar_grade(
                grades[i],
                X[i],
                i,
                grades,
                g + 1
            )

        print(
            f"\n--- GERAÇÃO {g+1:02d} ---"
        )

        for i in range(N_ILHAS):

            pos_ocupadas = obter_posicoes_ocupadas(
                grades[i]
            )

            if not pos_ocupadas:
                continue

            melhor_ilha = min(
                [
                    grades[i][r][c]
                    for r, c in pos_ocupadas
                ],
                key=lambda ind: ind["fitness"]
            )

            if (
                melhor_global is None
                or melhor_ilha["fitness"]
                < melhor_global["fitness"]
            ):

                melhor_global = {
                    "x": melhor_ilha["x"].copy(),
                    "sigma": melhor_ilha["sigma"],
                    "fitness": melhor_ilha["fitness"],
                    "historico": [
                        dict(p)
                        for p in melhor_ilha["historico"]
                    ]
                }

            print(
                f"  Ilha {i} "
                f"(R={R[i]}): "
                f"Pop={len(pos_ocupadas):02d} | "
                f"Melhor Fitness="
                f"{melhor_ilha['fitness']:.4f} | "
                f"Sigma="
                f"{melhor_ilha['sigma']:.4f}"
            )

        print(
            f"-> Melhor Global até agora: "
            f"{melhor_global['fitness']:.6f}"
        )

    # --- IMPRESSÃO DO HISTÓRICO DA LINHAGEM ---
    print(
        "\n==================================================================================="
    )
    print(
        "                LINHAGEM GENÉTICA DA MELHOR SOLUÇÃO ENCONTRADA"
    )
    print(
        "==================================================================================="
    )

    print(
        f"Fitness Final: "
        f"{melhor_global['fitness']:.6f}\n"
    )

    print(
        f"{'Gen':<5} | "
        f"{'Nascido em':<10} | "
        f"{'Cruzamento (Pais)':<22} | "
        f"{'Posição (x1, x2)':<22} | "
        f"{'Fitness':<10}"
    )

    print("-" * 83)

    for passo in melhor_global["historico"]:

        pos_str = (
            f"[{passo['x'][0]:.3f}, "
            f"{passo['x'][1]:.3f}]"
        )

        ilha_str = (
            f"Ilha {passo['ilha_origem']}"
        )

        print(
            f"{passo['geracao']:<5} | "
            f"{ilha_str:<10} | "
            f"{passo['pais']:<22} | "
            f"{pos_str:<22} | "
            f"{passo['fitness']:<10.4f}"
        )


if __name__ == "__main__":
    main()
