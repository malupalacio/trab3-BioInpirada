import random
import math
import sys

# --- CONFIGURAÇÕES E PARÂMETROS ---
N_ILHAS = 4
TEMP_SIMULACAO = 50       # Número de gerações
TAMANHO_GRADE = 10        # Grade 10x10 = 100 posições por ilha
DIMENSOES = 2             # Função 2D (x1, x2)
LIMITES = (-100, 100)     # Limites do domínio Bohachevsky

R_INICIAL = [2.8, 2.9, 3.0, 3.1]  # Promove oscilação e renovação nas primeiras gerações
R_FINAL = [1.8, 2.0, 2.2, 2.3]    # Promove estabilidade e convergência no final
D = 0.2  # Taxa de migração
X_INICIAL = [0.5, 0.5, 0.5, 0.5]
SIGMAS_BASE = [0.01, 0.1, 0.5, 1.5]

# Migração adaptativa: cada ilha recebe uma taxa própria a cada geração.
D_MIN = 0.05
D_MAX = 0.40
GERACOES_PARA_MIGRACAO_MAXIMA = 5
LIMIAR_MELHORA = 1e-3
LIMIAR_SEMELHANCA = 0.50
FATOR_REDUCAO_SEMELHANCA = 0.50

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
    posicao = [random.uniform(LIMITES[0], LIMITES[1]) for _ in range(DIMENSOES)]
    sigma = [SIGMAS_BASE[ilha] * random.uniform(0.8, 1.2) for _ in range(DIMENSOES)]
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
    return [[None for _ in range(TAMANHO_GRADE)] for _ in range(TAMANHO_GRADE)]

def obter_posicoes_ocupadas(grade):
    return [(i, j) for i in range(TAMANHO_GRADE) for j in range(TAMANHO_GRADE) if grade[i][j] is not None]

def obter_posicoes_vazias(grade):
    return [(i, j) for i in range(TAMANHO_GRADE) for j in range(TAMANHO_GRADE) if grade[i][j] is None]


def melhor_individuo(grade):
    ocupados = obter_posicoes_ocupadas(grade)
    if not ocupados:
        return None
    return min((grade[i][j] for i, j in ocupados), key=lambda individuo: individuo["fitness"])

def diversidade_entre_ilhas(grades):
    """Calcula a distância média entre as melhores soluções das ilhas."""
    melhores = [melhor_individuo(grade) for grade in grades]
    melhores = [individuo for individuo in melhores if individuo is not None]
    if len(melhores) < 2:
        return float("inf")

    distancias = []
    for i in range(len(melhores)):
        for j in range(i + 1, len(melhores)):
            distancia = math.sqrt(sum(
                (a - b) ** 2 for a, b in zip(melhores[i]["x"], melhores[j]["x"])
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
    """Conta gerações sem melhora relevante do melhor indivíduo de cada ilha."""
    for i, grade in enumerate(grades):
        melhor = melhor_individuo(grade)
        if melhor is None:
            continue

        if melhor["fitness"] < melhores_anteriores[i] - LIMIAR_MELHORA:
            estagnacoes[i] = 0
        else:
            estagnacoes[i] += 1
        melhores_anteriores[i] = melhor["fitness"]

# --- REPRODUÇÃO COM RASTREAMENTO DETALHADO ---
def reproduzir(pai1, pai2, ilha_p1, ilha_p2, ilha_filho, geracao_atual):
    # Taxas de aprendizagem dinâmicas baseadas no numero de dimensões
    tau_global = 1.0 / math.sqrt(2 * DIMENSOES)
    tau_local = 1.0 / math.sqrt(2 * math.sqrt(DIMENSOES))
    fator_global = math.exp(random.gauss(0, tau_global))
    
    novo_x = []
    novo_sigma = []
    
    for k in range(DIMENSOES):
        # Media dos sigmas dos pais na dimensão k
        sigma_medio = 0.5 * (pai1["sigma"][k] + pai2["sigma"][k])
        
        # Mutação do Sigma na dimensão k
        sigma_k = sigma_medio * fator_global * math.exp(random.gauss(0, tau_local))
        novo_sigma.append(sigma_k)
        
        # Media da posição dos pais na dimensão k mutada pelo novo sigma
        x_k = 0.5 * (pai1["x"][k] + pai2["x"][k]) + random.gauss(0, sigma_k)
        
        # Garante que não sai dos limites da Bohachevsky
        x_k = max(LIMITES[0], min(LIMITES[1], x_k))
        novo_x.append(x_k)
        
    fit = bohachevsky(novo_x)
    
    # Seleciona o histórico do pai mais apto para continuar a linhagem
    pai_principal = pai1 if pai1["fitness"] < pai2["fitness"] else pai2
    novo_historico = [dict(passo) for passo in pai_principal["historico"]]
    
    # Registra o cruzamento atual
    origem_str = f"Ilha {ilha_p1} x Ilha {ilha_p2}" if ilha_p1 != ilha_p2 else f"Ilha {ilha_p1} (Local)"
    
    novo_historico.append({
        "geracao": geracao_atual,
        "ilha_origem": ilha_filho,
        "pais": origem_str,
        "x": novo_x.copy(),
        "sigma": novo_sigma,
        "fitness": fit
    })
    
    return {"x": novo_x, "sigma": novo_sigma, "fitness": fit, "historico": novo_historico}

def nascer_individuos(grade, ilha, quantidade, grades, geracao_atual, taxa_migracao):
    vazios = random.sample(obter_posicoes_vazias(grade), quantidade)
    
    for i, j in vazios:
        eh_migracao = random.random() < taxa_migracao
        
        if eh_migracao:
            outras = [k for k in range(N_ILHAS) if k != ilha]
            ilha_ext = random.choice(outras)
            ocupados_ext = obter_posicoes_ocupadas(grades[ilha_ext])
            ocupados_loc = obter_posicoes_ocupadas(grade)
            
            if ocupados_loc and ocupados_ext:
                pos_loc = random.choice(ocupados_loc)
                pos_ext = random.choice(ocupados_ext)
                p_loc = grade[pos_loc[0]][pos_loc[1]]
                p_ext = grades[ilha_ext][pos_ext[0]][pos_ext[1]]
                
                if p_loc is not None and p_ext is not None:
                    grade[i][j] = reproduzir(p_loc, p_ext, ilha, ilha_ext, ilha, geracao_atual)
                else:
                    grade[i][j] = criar_individuo(ilha)
            else:
                grade[i][j] = criar_individuo(ilha)
        else:
            ocupados = obter_posicoes_ocupadas(grade)
            if len(ocupados) >= 2:
                p1_pos, p2_pos = random.sample(ocupados, 2)
                p1 = grade[p1_pos[0]][p1_pos[1]]
                p2 = grade[p2_pos[0]][p2_pos[1]]
                
                if p1 is not None and p2 is not None:
                    grade[i][j] = reproduzir(p1, p2, ilha, ilha, ilha, geracao_atual)
                else:
                    grade[i][j] = criar_individuo(ilha)
            else:
                grade[i][j] = criar_individuo(ilha)

def remover_individuos(grade, quantidade):
    ocupados = obter_posicoes_ocupadas(grade)
    ocupados.sort(key=lambda pos: grade[pos[0]][pos[1]]["fitness"], reverse=True)
    for i, j in ocupados[:quantidade]:
        grade[i][j] = None

def atualizar_grade(grade, x_novo, ilha, grades, geracao_atual, taxas_migracao):
    esperados = round(x_novo * TAMANHO_GRADE * TAMANHO_GRADE)
    atuais = len(obter_posicoes_ocupadas(grade))
    dif = esperados - atuais
    
    if dif > 0:
        nascer_individuos(grade, ilha, dif, grades, geracao_atual, taxas_migracao)
    elif dif < 0:
        remover_individuos(grade, abs(dif))
        
    # Turnover Geracional (10%)
    ocupados = obter_posicoes_ocupadas(grade)
    if len(ocupados) > 5:
        qtd_turnover = max(1, int(len(ocupados) * 0.10))
        remover_individuos(grade, qtd_turnover)
        nascer_individuos(grade, ilha, qtd_turnover, grades, geracao_atual, taxas_migracao)

def main():
    X = X_INICIAL.copy()
    grades = [criar_grade() for _ in range(N_ILHAS)]
    
    for i in range(N_ILHAS):
        qtd = round(X[i] * TAMANHO_GRADE * TAMANHO_GRADE)
        posicoes = random.sample([(r, c) for r in range(TAMANHO_GRADE) for c in range(TAMANHO_GRADE)], qtd)
        for r, c in posicoes:
            grades[i][r][c] = criar_individuo(i)

    melhor_global = None
    melhores_anteriores = [float("inf")] * N_ILHAS
    estagnacoes = [0] * N_ILHAS

    for g in range(TEMP_SIMULACAO):
        # Calcula o R atual para esta geração específica
        fator = g / (TEMP_SIMULACAO - 1) if TEMP_SIMULACAO > 1 else 1
        R_atual = [R_INICIAL[i] - (R_INICIAL[i] - R_FINAL[i]) * fator for i in range(N_ILHAS)]

        # calculo de taxa migração adaptativa
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

        for i in range(N_ILHAS):
            atualizar_grade(grades[i], X[i], i, grades, g + 1, taxas_migracao[i])

        print(f"\n--- GERAÇÃO {g+1:02d} ---")
        print(
            f"  Diversidade entre ilhas={diversidade:.3f} | "
            f"Taxas de migração={[f'{taxa:.2f}' for taxa in taxas_migracao]}"
        )
        for i in range(N_ILHAS):
            pos_ocupadas = obter_posicoes_ocupadas(grades[i])
            if not pos_ocupadas:
                continue
                
            melhor_ilha = min([grades[i][r][c] for r, c in pos_ocupadas], key=lambda ind: ind["fitness"])
            
            if melhor_global is None or melhor_ilha["fitness"] < melhor_global["fitness"]:
                melhor_global = {
                    "x": melhor_ilha["x"].copy(),
                    "sigma": melhor_ilha["sigma"],
                    "fitness": melhor_ilha["fitness"],
                    "historico": [dict(p) for p in melhor_ilha["historico"]]
                }

            sigmas_str = ", ".join([f"{s:.4f}" for s in melhor_ilha['sigma']])

            print(f"Ilha {i} (R={R_atual[i]:.3f}): Pop={len(pos_ocupadas):02d} | Melhor Fitness={melhor_ilha['fitness']:.4f} | Sigmas=[{sigmas_str}]")

        print(f"-> Melhor Global até agora: {melhor_global['fitness']:.6f}")

    # --- IMPRESSÃO DO HISTÓRICO DA LINHAGEM ---
    print("\n===================================================================================")
    print("                LINHAGEM GENÉTICA DA MELHOR SOLUÇÃO ENCONTRADA")
    print("===================================================================================")
    print(f"Fitness Final: {melhor_global['fitness']:.6f}\n")
    print(f"{'Gen':<5} | {'Nascido em':<10} | {'Cruzamento (Pais)':<22} | {'Posição (x1, x2)':<22} | {'Fitness':<10}")
    print("-" * 83)
    
    for passo in melhor_global["historico"]:
        pos_str = f"[{passo['x'][0]:.3f}, {passo['x'][1]:.3f}]"
        ilha_str = f"Ilha {passo['ilha_origem']}"
        print(f"{passo['geracao']:<5} | {ilha_str:<10} | {passo['pais']:<22} | {pos_str:<22} | {passo['fitness']:<10.4f}")

if __name__ == "__main__":
    main()
