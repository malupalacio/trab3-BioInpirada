import random
import math
import sys
from copy import deepcopy

# --- CONFIGURAÇÕES E PARÂMETROS ---
N_ILHAS = 4
TEMP_SIMULACAO = 50       # Número de gerações/iterações
TAMANHO_GRADE = 10        # Grade 10x10 = 100 posições por ilha
DIMENSOES = 2             # Função 2D (x1, x2)
LIMITES = (-5.12, 5.12)   # Limites do domínio da Rastrigin

R_INICIAL = [2.8, 2.9, 3.0, 3.1]  # Promove oscilação e renovação nas primeiras gerações
R_FINAL = [1.8, 2.0, 2.2, 2.3]    # Promove estabilidade e convergência no final
D = 0.2  # Taxa de migração
X_INICIAL = [0.5, 0.5, 0.5, 0.5]

# Parâmetros específicos do PSO
INERCIA_INICIAL = 0.9
INERCIA_FINAL = 0.4
C1 = 2.0                  # Influência do melhor pessoal (pBest)
C2 = 2.0                  # Influência do melhor da ilha (gBest)
VMAX_FRACAO = 0.20        # Velocidade máxima como fração da largura do domínio
FATOR_REBOTE = 0.5        # Redução da velocidade ao atingir os limites

# Mantem a diferença de intensidade entre ilhas que existia com SIGMAS_BASE
# e agora os valores definem a amplitude da velocidade inicial de cada ilha
VELOCIDADES_INICIAIS = [0.01, 0.1, 0.5, 1.5]

# Migração adaptativa: cada ilha recebe uma taxa própria a cada geração.
D_MIN = 0.05
D_MAX = 0.40
GERACOES_PARA_MIGRACAO_MAXIMA = 5
LIMIAR_MELHORA = 1e-3
LIMIAR_SEMELHANCA = 0.50
FATOR_REDUCAO_SEMELHANCA = 0.50


def rastrigin(x):
    A = 10
    return A * len(x) + sum([(xi**2 - A * math.cos(2 * math.pi * xi)) for xi in x])


def velocidade_maxima():
    return (LIMITES[1] - LIMITES[0]) * VMAX_FRACAO


def criar_particula(ilha):
    posicao = [random.uniform(LIMITES[0], LIMITES[1]) for _ in range(DIMENSOES)]
    amplitude = VELOCIDADES_INICIAIS[ilha]
    velocidade = [random.uniform(-amplitude, amplitude) for _ in range(DIMENSOES)]
    fit = rastrigin(posicao)

    particula = {
        "x": posicao,
        "velocidade": velocidade,
        "fitness": fit,
        "pbest_x": posicao.copy(),
        "pbest_fitness": fit,
        "historico": [{
            "geracao": 0,
            "ilha_origem": ilha,
            "evento": "Inicialização",
            "x": posicao.copy(),
            "fitness": fit,
            "pbest_x": posicao.copy(),
            "pbest_fitness": fit,
            "velocidade": velocidade.copy()
        }]
    }
    return particula


def criar_grade():
    return [[None for _ in range(TAMANHO_GRADE)] for _ in range(TAMANHO_GRADE)]


def obter_posicoes_ocupadas(grade):
    return [(i, j) for i in range(TAMANHO_GRADE) for j in range(TAMANHO_GRADE) if grade[i][j] is not None]


def obter_posicoes_vazias(grade):
    return [(i, j) for i in range(TAMANHO_GRADE) for j in range(TAMANHO_GRADE) if grade[i][j] is None]


def melhor_individuo(grade):
    ocupados = obter_posicoes_ocupadas(grade)
    if not ocupados:
        return None
    return min(
        (grade[i][j] for i, j in ocupados),
        key=lambda particula: particula["pbest_fitness"]
    )


def diversidade_entre_ilhas(grades):
    """Calcula a distância média entre os melhores pBest das ilhas."""
    melhores = [melhor_individuo(grade) for grade in grades]
    melhores = [particula for particula in melhores if particula is not None]
    if len(melhores) < 2:
        return float("inf")

    distancias = []
    for i in range(len(melhores)):
        for j in range(i + 1, len(melhores)):
            distancia = math.sqrt(sum(
                (a - b) ** 2
                for a, b in zip(melhores[i]["pbest_x"], melhores[j]["pbest_x"])
            ))
            distancias.append(distancia)
    return sum(distancias) / len(distancias)


def calcular_taxas_migracao(estagnacoes, diversidade):
    """Aumenta a migração em ilhas estagnadas e a reduz quando há pouca diversidade."""
    taxas = []
    for estagnacao in estagnacoes:
        progresso_estagnacao = min(1.0, estagnacao / GERACOES_PARA_MIGRACAO_MAXIMA)
        taxa = D_MIN + (D_MAX - D_MIN) * progresso_estagnacao

        if diversidade <= LIMIAR_SEMELHANCA:
            taxa = D_MIN + (taxa - D_MIN) * FATOR_REDUCAO_SEMELHANCA
        taxas.append(taxa)
    return taxas


def atualizar_estagnacoes(grades, melhores_anteriores, estagnacoes):
    """Conta gerações sem melhora relevante do melhor pBest de cada ilha."""
    for i, grade in enumerate(grades):
        melhor = melhor_individuo(grade)
        if melhor is None:
            continue

        if melhor["pbest_fitness"] < melhores_anteriores[i] - LIMIAR_MELHORA:
            estagnacoes[i] = 0
        else:
            estagnacoes[i] += 1
        melhores_anteriores[i] = melhor["pbest_fitness"]


# --- ATUALIZAÇÃO DAS PARTÍCULAS (PSO) ---
def atualizar_enxame(grade, ilha, geracao, inercia):
    melhor_ilha = melhor_individuo(grade)
    if melhor_ilha is None:
        return

    # Todas as partículas usam o mesmo gBest nesta iteração.
    gbest_x = melhor_ilha["pbest_x"].copy()
    vmax = velocidade_maxima()
    ocupados = obter_posicoes_ocupadas(grade)

    for i, j in ocupados:
        particula = grade[i][j]

        for k in range(DIMENSOES):
            r1 = random.random()
            r2 = random.random()

            velocidade = (
                inercia * particula["velocidade"][k]
                + C1 * r1 * (particula["pbest_x"][k] - particula["x"][k])
                + C2 * r2 * (gbest_x[k] - particula["x"][k])
            )
            velocidade = max(-vmax, min(vmax, velocidade))
            x_novo = particula["x"][k] + velocidade

            # Mantém a partícula dentro dos limites do domínio.
            if x_novo < LIMITES[0]:
                x_novo = LIMITES[0]
                velocidade = -FATOR_REBOTE * velocidade
            elif x_novo > LIMITES[1]:
                x_novo = LIMITES[1]
                velocidade = -FATOR_REBOTE * velocidade

            particula["velocidade"][k] = velocidade
            particula["x"][k] = x_novo

        particula["fitness"] = rastrigin(particula["x"])

        # Atualiza o melhor pessoal da partícula.
        if particula["fitness"] < particula["pbest_fitness"]:
            particula["pbest_fitness"] = particula["fitness"]
            particula["pbest_x"] = particula["x"].copy()

        particula["historico"].append({
            "geracao": geracao,
            "ilha_origem": ilha,
            "evento": "Atualização PSO",
            "x": particula["x"].copy(),
            "fitness": particula["fitness"],
            "pbest_x": particula["pbest_x"].copy(),
            "pbest_fitness": particula["pbest_fitness"],
            "velocidade": particula["velocidade"].copy()
        })


def nascer_particulas(grade, ilha, quantidade, grades, geracao_atual, taxa_migracao):
    vazios = random.sample(obter_posicoes_vazias(grade), quantidade)

    for i, j in vazios:
        eh_migracao = random.random() < taxa_migracao

        if eh_migracao:
            outras = [k for k in range(N_ILHAS) if k != ilha]
            ilha_ext = random.choice(outras)
            ocupados_ext = obter_posicoes_ocupadas(grades[ilha_ext])

            if ocupados_ext:
                # Migra a melhor memória pessoal de uma ilha externa.
                p_ext = melhor_individuo(grades[ilha_ext])
                posicao = p_ext["pbest_x"].copy()
                fit = rastrigin(posicao)
                velocidade = [0.0 for _ in range(DIMENSOES)]

                historico = deepcopy(p_ext["historico"])
                historico.append({
                    "geracao": geracao_atual,
                    "ilha_origem": ilha,
                    "evento": f"Migração da Ilha {ilha_ext}",
                    "x": posicao.copy(),
                    "fitness": fit,
                    "pbest_x": posicao.copy(),
                    "pbest_fitness": fit,
                    "velocidade": velocidade.copy()
                })

                grade[i][j] = {
                    "x": posicao,
                    "velocidade": velocidade,
                    "fitness": fit,
                    "pbest_x": posicao.copy(),
                    "pbest_fitness": fit,
                    "historico": historico
                }
            else:
                grade[i][j] = criar_particula(ilha)
        else:
            grade[i][j] = criar_particula(ilha)


def remover_individuos(grade, quantidade):
    ocupados = obter_posicoes_ocupadas(grade)
    ocupados.sort(
        key=lambda pos: grade[pos[0]][pos[1]]["pbest_fitness"],
        reverse=True
    )
    for i, j in ocupados[:quantidade]:
        grade[i][j] = None


def atualizar_grade(grade, x_novo, ilha, grades, geracao_atual, taxa_migracao):
    esperados = round(x_novo * TAMANHO_GRADE * TAMANHO_GRADE)
    atuais = len(obter_posicoes_ocupadas(grade))
    dif = esperados - atuais

    if dif > 0:
        nascer_particulas(grade, ilha, dif, grades, geracao_atual, taxa_migracao)
    elif dif < 0:
        remover_individuos(grade, abs(dif))

    # Turnover Geracional (10%)
    ocupados = obter_posicoes_ocupadas(grade)
    if len(ocupados) > 5:
        qtd_turnover = max(1, int(len(ocupados) * 0.10))
        remover_individuos(grade, qtd_turnover)
        nascer_particulas(grade, ilha, qtd_turnover, grades, geracao_atual, taxa_migracao)


def main():
    X = X_INICIAL.copy()
    grades = [criar_grade() for _ in range(N_ILHAS)]

    for i in range(N_ILHAS):
        qtd = round(X[i] * TAMANHO_GRADE * TAMANHO_GRADE)
        posicoes = random.sample(
            [(r, c) for r in range(TAMANHO_GRADE) for c in range(TAMANHO_GRADE)],
            qtd
        )
        for r, c in posicoes:
            grades[i][r][c] = criar_particula(i)

    melhor_global = None
    melhores_anteriores = [float("inf")] * N_ILHAS
    estagnacoes = [0] * N_ILHAS

    for g in range(TEMP_SIMULACAO):
        # Redução linear da inércia ao longo das gerações.
        fator = g / (TEMP_SIMULACAO - 1) if TEMP_SIMULACAO > 1 else 1
        inercia = INERCIA_INICIAL - (INERCIA_INICIAL - INERCIA_FINAL) * fator

        # Calcula o R atual para esta geração específica.
        R_atual = [R_INICIAL[i] - (R_INICIAL[i] - R_FINAL[i]) * fator for i in range(N_ILHAS)]

        # Cálculo da taxa de migração adaptativa.
        atualizar_estagnacoes(grades, melhores_anteriores, estagnacoes)
        diversidade = diversidade_entre_ilhas(grades)
        taxas_migracao = calcular_taxas_migracao(estagnacoes, diversidade)

        crescimento = [R_atual[i] * X[i] * (1 - X[i]) for i in range(N_ILHAS)]
        X_novo = []
        for i in range(N_ILHAS):
            imigrantes = sum(crescimento[j] for j in range(N_ILHAS) if j != i)
            taxa = taxas_migracao[i]
            xi_novo = (1 - D) * crescimento[i] + (D / (N_ILHAS - 1)) * imigrantes
            X_novo.append(max(0.01, min(0.99, xi_novo)))
        X = X_novo

        # Mantém a atualização do tamanho das ilhas e substitui reprodução
        # pelo movimento PSO das partículas.
        for i in range(N_ILHAS):
            atualizar_grade(grades[i], X[i], i, grades, g + 1, taxas_migracao[i])

        for i in range(N_ILHAS):
            atualizar_enxame(grades[i], i, g + 1, inercia)

        print(f"\n--- GERAÇÃO {g+1:02d} ---")
        print(
            f"  Diversidade entre ilhas={diversidade:.3f} | "
            f"Taxas de migração={[f'{taxa:.2f}' for taxa in taxas_migracao]}"
        )
        for i in range(N_ILHAS):
            pos_ocupadas = obter_posicoes_ocupadas(grades[i])
            if not pos_ocupadas:
                continue

            melhor_ilha = melhor_individuo(grades[i])

            if melhor_global is None or melhor_ilha["pbest_fitness"] < melhor_global["fitness"]:
                melhor_global = {
                    "x": melhor_ilha["pbest_x"].copy(),
                    "fitness": melhor_ilha["pbest_fitness"],
                    "historico": deepcopy(melhor_ilha["historico"])
                }

            velocidades_str = ", ".join(
                [f"{v:.4f}" for v in melhor_ilha["velocidade"]]
            )

            print(
                f"Ilha {i} (R={R_atual[i]:.3f}): Pop={len(pos_ocupadas):02d} | "
                f"Melhor Fitness={melhor_ilha['pbest_fitness']:.4f} | "
                f"Velocidade=[{velocidades_str}]"
            )

        print(f"-> Melhor Global até agora: {melhor_global['fitness']:.6f}")

    # --- IMPRESSÃO DO HISTÓRICO DA MELHOR PARTÍCULA ---
    print("\n===================================================================================")
    print("                HISTÓRICO DA MELHOR SOLUÇÃO ENCONTRADA")
    print("===================================================================================")
    print(f"Fitness Final: {melhor_global['fitness']:.6f}\n")
    print(f"{'Gen':<5} | {'Ilha':<10} | {'Evento':<22} | {'Posição (x1, x2)':<22} | {'Fitness':<10}")
    print("-" * 83)

    for passo in melhor_global["historico"]:
        pos_str = f"[{passo['x'][0]:.3f}, {passo['x'][1]:.3f}]"
        ilha_str = f"Ilha {passo['ilha_origem']}"
        evento_str = passo["evento"][:22]
        print(
            f"{passo['geracao']:<5} | {ilha_str:<10} | {evento_str:<22} | "
            f"{pos_str:<22} | {passo['fitness']:<10.4f}"
        )


if __name__ == "__main__":
    main()
