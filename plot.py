import csv
import os
import statistics
import matplotlib.pyplot as plt

PASTAS = [
    "ackley-genetico/resultados",
    "ackley-pso/resultados",
]
PASTA_SAIDA = "ackley-graficos"
LIMIAR_SUCESSO = 1e-2

# Ordem e rótulos amigáveis para a legenda
ORDEM = [
    ("Genetico", "Genético (1.596 aval.)"),
    ("Genetico-Boosted", "Genético-Boosted (51.405 aval.)"),
    ("PSO_sem_migracao", "PSO sem migração (10.200 aval.)"),
    ("PSO_anel", "PSO anel (10.200 aval.)"),
]


def carregar_curvas():
    curvas = {}
    for pasta in PASTAS:
        if not os.path.isdir(pasta):
            continue
        for arq in os.listdir(pasta):
            if arq.startswith("curvas_") and arq.endswith(".csv"):
                nome = arq[len("curvas_"):-len(".csv")]
                caminho = os.path.join(pasta, arq)
                with open(caminho, newline="") as f:
                    linhas = list(csv.DictReader(f))
                curvas[nome] = {
                    "avaliacoes": [int(l["avaliacoes"]) for l in linhas],
                    "media": [float(l["media"]) for l in linhas],
                    "mediana": [float(l["mediana"]) for l in linhas],
                    "desvio": [float(l["desvio"]) if l.get("desvio") not in (None, "") else 0.0 for l in linhas],
                }
    return curvas


def carregar_resultados():
    resultados = {}
    for pasta in PASTAS:
        if not os.path.isdir(pasta):
            continue
        for arq in os.listdir(pasta):
            if arq.startswith("resultados_") and arq.endswith(".csv"):
                nome = arq[len("resultados_"):-len(".csv")]
                caminho = os.path.join(pasta, arq)
                with open(caminho, newline="") as f:
                    linhas = list(csv.DictReader(f))
                resultados[nome] = {
                    "fitness": [float(l["fitness"]) for l in linhas],
                    "avaliacoes": int(linhas[0]["avaliacoes"]),
                    "aval_ate_limiar": [int(l["aval_ate_limiar"]) for l in linhas if l["aval_ate_limiar"] != ""],
                    "total_runs": len(linhas),
                }
    return resultados


def chaves_ordenadas(dicionario):
    conhecidas = [k for k, _ in ORDEM if k in dicionario]
    extras = sorted(k for k in dicionario if k not in conhecidas)
    return conhecidas + extras


def rotulo(nome):
    mapa = dict(ORDEM)
    return mapa.get(nome, nome)


def plotar_convergencia(curvas):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), dpi=150)
    cores = ["#d95f02", "#1b9e77", "#7570b3", "#e7298a"]

    for idx, nome in enumerate(chaves_ordenadas(curvas)):
        c = curvas[nome]
        cor = cores[idx % len(cores)]
        x = c["avaliacoes"]
        y = c["media"]
        s = c["desvio"]
        inf = [max(0.0, m - d) for m, d in zip(y, s)]
        sup = [m + d for m, d in zip(y, s)]

        # Painel 1: Trajetória completa (eixo X até o máximo de cada algoritmo)
        ax1.plot(x, y, label=rotulo(nome), color=cor, linewidth=2)
        if any(v > 0 for v in s):
            ax1.fill_between(x, inf, sup, color=cor, alpha=0.16)

        # Painel 2: Zoom nas primeiras 10.500 avaliações (comparação justa de ritmo)
        pares = [(xi, yi, ii, si) for xi, yi, ii, si in zip(x, y, inf, sup) if xi <= 10500]
        if pares:
            xz, yz, iz, sz = zip(*pares)
            ax2.plot(xz, yz, label=rotulo(nome), color=cor, linewidth=2)
            if any(v > 0 for v in s):
                ax2.fill_between(xz, iz, sz, color=cor, alpha=0.16)

    for ax, titulo in [
        (ax1, "Convergência Completa (todas as avaliações)"),
        (ax2, "Zoom até 10.500 Avaliações (ritmo de convergência)"),
    ]:
        ax.axhline(LIMIAR_SUCESSO, color="gray", linestyle="--", linewidth=1.1, label=f"Limiar ({LIMIAR_SUCESSO})")
        ax.set_yscale("symlog", linthresh=1e-4)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Avaliações da função objetivo")
        ax.set_ylabel("Melhor fitness (média ± desvio)")
        ax.set_title(titulo)
        ax.grid(True, which="both", linestyle=":", alpha=0.5)

    ax1.legend(loc="upper right", fontsize=8.5)
    plt.tight_layout()
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    saida = os.path.join(PASTA_SAIDA, "1_convergencia.png")
    plt.savefig(saida)
    plt.close(fig)
    print(f"Salvo: {saida}")


def plotar_resultados(resultados):
    chaves = chaves_ordenadas(resultados)
    nomes_curtos = [k.replace("_", "\n") for k in chaves]
    cores = ["#d95f02", "#1b9e77", "#7570b3", "#e7298a"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150)

    # --- Painel 1: Avaliações até atingir o limiar (eficiência) ---
    dados_aval = [resultados[k]["aval_ate_limiar"] for k in chaves]
    bp1 = ax1.boxplot(dados_aval, tick_labels=nomes_curtos, patch_artist=True, widths=0.5)
    for patch, cor in zip(bp1["boxes"], cores):
        patch.set_facecolor(cor)
        patch.set_alpha(0.65)
    for mediana in bp1["medians"]:
        mediana.set_color("black")
        mediana.set_linewidth(1.5)

    # Anota a taxa de sucesso acima de cada caixa
    ymax1 = max((max(v) for v in dados_aval if v), default=1000)
    for i, k in enumerate(chaves, start=1):
        sucessos = len(resultados[k]["aval_ate_limiar"])
        total = resultados[k]["total_runs"]
        topo = max(resultados[k]["aval_ate_limiar"]) if sucessos > 0 else 0
        ax1.text(i, topo + ymax1 * 0.03, f"Sucesso:\n{sucessos}/{total}", ha="center", va="bottom", fontsize=8.5)

    ax1.set_ylim(0, ymax1 * 1.18)
    ax1.set_ylabel("Avaliações até atingir fitness ≤ 0.01")
    ax1.set_title("Eficiência: Avaliações até o Limiar")
    ax1.grid(True, axis="y", linestyle=":", alpha=0.5)

    # --- Painel 2: Distribuição do Fitness Final (robustez) ---
    dados_fit = [resultados[k]["fitness"] for k in chaves]
    bp2 = ax2.boxplot(dados_fit, tick_labels=nomes_curtos, patch_artist=True, widths=0.5)
    for patch, cor in zip(bp2["boxes"], cores):
        patch.set_facecolor(cor)
        patch.set_alpha(0.65)
    for mediana in bp2["medians"]:
        mediana.set_color("black")
        mediana.set_linewidth(1.5)

    ax2.axhline(LIMIAR_SUCESSO, color="gray", linestyle="--", linewidth=1.1, label=f"Limiar ({LIMIAR_SUCESSO})")
    ax2.set_yscale("symlog", linthresh=1e-5)
    ax2.set_ylim(bottom=0)
    ax2.set_ylabel("Fitness final (menor é melhor)")
    ax2.set_title("Qualidade Final (50 execuções)")
    ax2.legend(loc="upper right", fontsize=8.5)
    ax2.grid(True, which="both", linestyle=":", alpha=0.5)

    plt.tight_layout()
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    saida = os.path.join(PASTA_SAIDA, "2_resultados_comparacao.png")
    plt.savefig(saida)
    plt.close(fig)
    print(f"Salvo: {saida}")


def main():
    curvas = carregar_curvas()
    resultados = carregar_resultados()

    if not curvas or not resultados:
        raise SystemExit("CSVs não encontrados nas pastas de resultados.")

    plotar_convergencia(curvas)
    plotar_resultados(resultados)


if __name__ == "__main__":
    main()