import argparse
import csv
import math
import os
import re
import statistics
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

LIMIAR_SUCESSO = 1e-2


def carregar_dados_dimensoes(pasta):
    """Lê resultados_PSO_anel_D{d}.csv e curvas_PSO_anel_D{d}.csv ordenados por dimensão."""
    por_dim = {}
    padrao_res = re.compile(r"^resultados_PSO_anel_D(\d+)\.csv$")
    padrao_curva = re.compile(r"^curvas_PSO_anel_D(\d+)\.csv$")

    if not os.path.isdir(pasta):
        raise SystemExit(f"Pasta '{pasta}' não encontrada.")

    for arq in os.listdir(pasta):
        m_res = padrao_res.match(arq)
        if m_res:
            dim = int(m_res.group(1))
            por_dim.setdefault(dim, {})
            with open(os.path.join(pasta, arq), newline="") as f:
                linhas = list(csv.DictReader(f))
            fits = [float(l["fitness"]) for l in linhas]
            avals_lim = [int(l["aval_ate_limiar"]) for l in linhas if l["aval_ate_limiar"] != ""]
            por_dim[dim]["fitness"] = fits
            por_dim[dim]["aval_ate_limiar"] = avals_lim
            por_dim[dim]["total_runs"] = len(linhas)

        m_curva = padrao_curva.match(arq)
        if m_curva:
            dim = int(m_curva.group(1))
            por_dim.setdefault(dim, {})
            with open(os.path.join(pasta, arq), newline="") as f:
                linhas = list(csv.DictReader(f))
            por_dim[dim]["curva_aval"] = [int(l["avaliacoes"]) for l in linhas]
            por_dim[dim]["curva_media"] = [float(l["media"]) for l in linhas]

    if not por_dim:
        raise SystemExit(f"Nenhum arquivo *_PSO_anel_D*.csv encontrado em '{pasta}'.")

    return dict(sorted(por_dim.items()))


def percentil(valores_ordenados, p):
    if not valores_ordenados:
        return 0.0
    idx = (len(valores_ordenados) - 1) * p
    baixo = math.floor(idx)
    alto = math.ceil(idx)
    if baixo == alto:
        return valores_ordenados[baixo]
    return valores_ordenados[baixo] * (alto - idx) + valores_ordenados[alto] * (idx - baixo)


def plotar_escalabilidade(dados, pasta_saida):
    dims = list(dados.keys())
    medianas, q25, q75, minimos, maximos = [], [], [], [], []
    taxas_sucesso, media_aval_limiar, dims_com_sucesso = [], [], []

    for d in dims:
        fits = sorted(dados[d]["fitness"])
        medianas.append(statistics.median(fits))
        q25.append(percentil(fits, 0.25))
        q75.append(percentil(fits, 0.75))
        minimos.append(fits[0])
        maximos.append(fits[-1])

        sucessos = dados[d]["aval_ate_limiar"]
        total = dados[d]["total_runs"]
        taxas_sucesso.append(100.0 * len(sucessos) / total)
        if sucessos:
            dims_com_sucesso.append(d)
            media_aval_limiar.append(statistics.mean(sucessos))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.4), dpi=150)

    # --- Painel 1: Degradação do Fitness Final (Mediana + IQR + Min-Max) ---
    cor_fit = "#1f78b4"
    ax1.fill_between(dims, minimos, maximos, color=cor_fit, alpha=0.12, label="Mínimo – Máximo")
    ax1.fill_between(dims, q25, q75, color=cor_fit, alpha=0.28, label="Intervalo Interquartil (25%–75%)")
    ax1.plot(dims, medianas, color=cor_fit, marker="o", linewidth=2.2, label="Mediana (50 execuções)")
    ax1.axhline(LIMIAR_SUCESSO, color="#d95f02", linestyle="--", linewidth=1.2, label=f"Limiar de sucesso ({LIMIAR_SUCESSO})")

    ax1.set_yscale("symlog", linthresh=1e-3)
    ax1.set_ylim(bottom=0)
    ax1.set_xticks(dims)
    ax1.set_xticklabels([f"{d}D" for d in dims])
    ax1.set_xlabel("Dimensionalidade do problema")
    ax1.set_ylabel("Fitness final (menor é melhor)")
    ax1.set_title("Degradação da Qualidade da Solução (2D → 10D)")
    ax1.grid(True, which="both", linestyle=":", alpha=0.5)
    ax1.legend(loc="upper left", fontsize=8.5)

    # --- Painel 2: Taxa de Sucesso (%) e Avaliações até o Limiar ---
    cor_bar = "#33a02c"
    barras = ax2.bar(dims, taxas_sucesso, color=cor_bar, alpha=0.65, width=0.55, label="Taxa de sucesso (%)")
    for bar, taxa in zip(barras, taxas_sucesso):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            taxa + 2.0,
            f"{taxa:.0f}%",
            ha="center",
            va="bottom",
            fontsize=8.5,
            color="#1b5e20",
            fontweight="bold",
        )

    ax2.set_ylim(0, 115)
    ax2.set_xticks(dims)
    ax2.set_xticklabels([f"{d}D" for d in dims])
    ax2.set_xlabel("Dimensionalidade do problema")
    ax2.set_ylabel("Taxa de sucesso (fitness ≤ 0.01) [%]", color="#1b5e20")
    ax2.tick_params(axis="y", labelcolor="#1b5e20")
    ax2.set_title("Taxa de Sucesso e Custo de Convergência")
    ax2.grid(True, axis="y", linestyle=":", alpha=0.5)

    if dims_com_sucesso:
        ax2_dir = ax2.twinx()
        cor_linha = "#6a3d9a"
        ax2_dir.plot(
            dims_com_sucesso,
            media_aval_limiar,
            color=cor_linha,
            marker="s",
            linewidth=2.2,
            label="Média de avaliações até o limiar",
        )
        ax2_dir.set_ylim(0, max(media_aval_limiar) * 1.25)
        ax2_dir.set_ylabel("Avaliações até atingir ≤ 0.01 (média)", color=cor_linha)
        ax2_dir.tick_params(axis="y", labelcolor=cor_linha)

        # Legenda unificada dos dois eixos
        h1, l1 = ax2.get_legend_handles_labels()
        h2, l2 = ax2_dir.get_legend_handles_labels()
        ax2.legend(h1 + h2, l1 + l2, loc="upper right", fontsize=8.5)

    plt.tight_layout()
    os.makedirs(pasta_saida, exist_ok=True)
    saida = os.path.join(pasta_saida, "1_escalabilidade_dimensoes.png")
    plt.savefig(saida)
    plt.close(fig)
    print(f"Salvo: {saida}")


def plotar_heatmap_convergencia(dados, pasta_saida):
    dims = [d for d in dados if "curva_media" in dados[d]]
    if not dims:
        return

    eixo_x = dados[dims[0]]["curva_aval"]
    matriz = [dados[d]["curva_media"] for d in dims]

    # Evita zero exato para escala logarítmica de cores
    piso = 1e-4
    matriz_log = [[max(v, piso) for v in linha] for linha in matriz]
    vmax = max(max(linha) for linha in matriz_log)

    fig, ax = plt.subplots(figsize=(12.5, 4.8), dpi=150)
    im = ax.imshow(
        matriz_log,
        aspect="auto",
        origin="lower",
        cmap="viridis_r",
        norm=mcolors.LogNorm(vmin=piso, vmax=vmax),
    )

    # Marcações limpas no eixo X (a cada ~1000 avaliações)
    indices_x = [i for i, val in enumerate(eixo_x) if val % 1000 == 0 or i == 0 or i == len(eixo_x) - 1]
    ax.set_xticks(indices_x)
    ax.set_xticklabels([str(eixo_x[i]) for i in indices_x])

    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels([f"{d}D" for d in dims])

    ax.set_xlabel("Avaliações da função objetivo")
    ax.set_ylabel("Dimensionalidade")
    ax.set_title("Mapa de Convergência do PSO_anel na Rastrigin (Fitness Médio por Dimensão)")

    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Melhor fitness médio (escala log)")

    plt.tight_layout()
    os.makedirs(pasta_saida, exist_ok=True)
    saida = os.path.join(pasta_saida, "2_mapa_calor_convergencia.png")
    plt.savefig(saida)
    plt.close(fig)
    print(f"Salvo: {saida}")


def main():
    ap = argparse.ArgumentParser(description="Plots de escalabilidade dimensional (PSO_anel)")
    ap.add_argument("--pasta", default="resultados_dimensoes", help="pasta com os CSVs por dimensão")
    ap.add_argument("--saida", default="graficos_dimensoes", help="pasta de saída das imagens")
    args = ap.parse_args()

    dados = carregar_dados_dimensoes(args.pasta)
    plotar_escalabilidade(dados, args.saida)
    plotar_heatmap_convergencia(dados, args.saida)


if __name__ == "__main__":
    main()