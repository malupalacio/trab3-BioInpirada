#!/usr/bin/env python3
"""
Gera 3 gráficos a partir dos logs (rodada_*.log) do algoritmo genético em ilhas:

  1. grafico_1_media_fitness_por_geracao.png  -> linhas: média do melhor fitness de cada ilha por geração
  2. grafico_2_fitness_final_por_rodada.png   -> barras: melhor fitness final encontrado em cada log
  3. grafico_3_boxplot_fitness.png            -> boxplot: fitness final de cada ilha entre as rodadas

Uso:
    python analisar_logs.py -i ./pasta_dos_logs -o ./graficos
    python analisar_logs.py -i ./logs --log      # eixo Y logarítmico no gráfico 1
    python3 analisar_logs.py --todos -i . -o graficos  # todos os casos

Dependências: matplotlib, numpy
"""
import argparse
import glob
import os
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CORES = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
RE_GER = re.compile(r"--- GERAÇÃO (\d+) ---")
RE_ILHA = re.compile(r"Ilha (\d+) \(R=[\d.]+\): Pop=\d+ \| Melhor Fitness=([\d.eE+-]+)")
RE_GLOBAL = re.compile(r"Melhor Global até agora: ([\d.eE+-]+)")


def ler_log(caminho):
    """Retorna ({ilha: [fitness por geração]}, melhor_global_final)."""
    por_ilha, melhor_global = {}, np.nan
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            m = RE_ILHA.search(linha)
            if m:
                por_ilha.setdefault(int(m.group(1)), []).append(float(m.group(2)))
                continue
            m = RE_GLOBAL.search(linha)
            if m:
                melhor_global = float(m.group(1))
    return por_ilha, melhor_global


def carregar(entrada):
    if os.path.isdir(entrada):
        arquivos = sorted(glob.glob(os.path.join(entrada, "rodada_*.log"))) \
            or sorted(glob.glob(os.path.join(entrada, "*.log")))
    else:
        arquivos = sorted(glob.glob(entrada))
    if not arquivos:
        sys.exit(f"Nenhum .log encontrado em: {entrada}")
    arquivos.sort(key=lambda p: [int(s) if s.isdigit() else s for s in re.split(r"(\d+)", p)])

    logs, globais, nomes = [], [], []
    for arq in arquivos:
        por_ilha, mg = ler_log(arq)
        if not por_ilha:
            print(f"[aviso] {arq}: nenhuma geração reconhecida, ignorado.")
            continue
        logs.append(por_ilha); globais.append(mg)
        nomes.append(os.path.splitext(os.path.basename(arq))[0])
    if not logs:
        sys.exit(f"Nenhuma rodada reconhecida em: {entrada}")
    if not np.isfinite(globais).all():
        sys.exit(f"Fitness global final ausente ou inválido em: {entrada}")
    return logs, np.array(globais), nomes


def grafico_media_por_geracao(logs, pasta, usar_log):
    ilhas = sorted(logs[0].keys())
    n_ger = min(len(l[i]) for l in logs for i in ilhas)
    geracoes = np.arange(1, n_ger + 1)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, cor in zip(ilhas, CORES):
        dados = np.array([l[i][:n_ger] for l in logs])   # (rodadas, gerações)
        ax.plot(geracoes, dados.mean(axis=0), color=cor, lw=2, label=f"Ilha {i}")
    if usar_log:
        ax.set_yscale("log")
    ax.set_xlabel("Geração")
    ax.set_ylabel("Média do melhor fitness" + (" (log)" if usar_log else ""))
    ax.set_title(f"Média do melhor fitness por ilha ao longo das gerações ({len(logs)} rodadas)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_1_media_fitness_por_geracao.png"), dpi=160)
    plt.close(fig)


def grafico_barras_final(globais, nomes, pasta):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(nomes))
    barras = ax.bar(x, globais, color="#4c72b0", edgecolor="k", alpha=0.85)
    for b, v in zip(barras, globais):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.4f}", ha="center", va="bottom", fontsize=8)
    ax.axhline(np.mean(globais), color="crimson", ls="--", label=f"média = {np.mean(globais):.4f}")
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("rodada_", "Rodada ") for n in nomes], rotation=45, ha="right")
    ax.set_ylabel("Melhor fitness final")
    ax.set_title("Melhor fitness final encontrado em cada rodada")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_2_fitness_final_por_rodada.png"), dpi=160)
    plt.close(fig)


def grafico_boxplot(logs, pasta):
    ilhas = sorted(logs[0].keys())
    dados = [[l[i][-1] for l in logs] for i in ilhas]   # fitness da última geração
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bp = ax.boxplot(dados, patch_artist=True, widths=0.5, showmeans=True)
    for patch, cor in zip(bp["boxes"], CORES):
        patch.set_facecolor(cor); patch.set_alpha(0.35)
    rng = np.random.default_rng(0)
    for k, (v, cor) in enumerate(zip(dados, CORES), start=1):
        ax.scatter(k + rng.uniform(-0.1, 0.1, len(v)), v, color=cor, edgecolor="k", s=35, zorder=3)
    ax.set_xticks(range(1, len(ilhas) + 1))
    ax.set_xticklabels([f"Ilha {i}" for i in ilhas])
    ax.set_ylabel("Fitness final")
    ax.set_title("Distribuição do fitness final por ilha (cada ponto = 1 rodada; △ = média)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(pasta, "grafico_3_boxplot_fitness.png"), dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="3 gráficos comparativos do GA em ilhas")
    ap.add_argument("-i", "--entrada", default=".", help="pasta com rodada_*.log (ou glob)")
    ap.add_argument("-o", "--saida", default="graficos", help="pasta de saída")
    ap.add_argument("--log", action="store_true", help="eixo Y logarítmico no gráfico 1")
    ap.add_argument("--todos", action="store_true", help="descobre casos recursivamente e espelha seus diretórios na saída")
    a = ap.parse_args()

    if a.todos:
        raiz = Path(a.entrada).resolve()
        saida = Path(a.saida).resolve()
        casos = sorted({p.parent for p in raiz.rglob("*.log")
                        if saida not in p.parents
                        and not any(parte.startswith(".") for parte in p.relative_to(raiz).parts)
                        and RE_GER.search(p.read_text(encoding="utf-8"))})
        if not casos:
            sys.exit(f"Nenhum caso encontrado em: {raiz}")
        indice = ["# Gráficos dos casos de teste", "",
                  "Gerados com `python3 analisar_logs.py --todos -i . -o graficos`.", "",
                  "Cada pasta espelha o diretório dos logs de origem. Fitness menor é melhor.", "",
                  "Os gráficos que já existiam na raiz foram preservados em `anteriores/`.", "",
                  "A curva usa a média do melhor fitness de cada ilha por geração; as barras usam o último melhor global registrado; o boxplot usa o fitness de cada ilha na última geração.", "",
                  "| Logs de origem | Rodadas | Gerações | Evolução por ilha | Final por rodada | Boxplot por ilha |",
                  "| --- | ---: | ---: | --- | --- | --- |"]
        for caso in casos:
            relativo = caso.relative_to(raiz)
            destino = saida / relativo
            destino.mkdir(parents=True, exist_ok=True)
            logs, globais, nomes = carregar(str(caso))
            grafico_media_por_geracao(logs, str(destino), a.log)
            grafico_barras_final(globais, nomes, str(destino))
            grafico_boxplot(logs, str(destino))
            geracoes = sorted({len(v) for l in logs for v in l.values()})
            links = [f"[{titulo}](<{relativo.as_posix()}/{arquivo}>)" for titulo, arquivo in [
                ("Evolução", "grafico_1_media_fitness_por_geracao.png"),
                ("Barras", "grafico_2_fitness_final_por_rodada.png"),
                ("Boxplot", "grafico_3_boxplot_fitness.png")]]
            indice.append(f"| `{relativo}` | {len(logs)} | {', '.join(map(str, geracoes))} | {' | '.join(links)} |")
            print(f"{relativo}: {len(logs)} rodadas, 3 gráficos")
        (saida / "README.md").write_text("\n".join(indice) + "\n", encoding="utf-8")
        print(f"{len(casos) * 3} gráficos salvos em: {saida}")
        return

    os.makedirs(a.saida, exist_ok=True)
    logs, globais, nomes = carregar(a.entrada)
    print(f"{len(logs)} rodada(s) lida(s).")

    grafico_media_por_geracao(logs, a.saida, a.log)
    grafico_barras_final(globais, nomes, a.saida)
    grafico_boxplot(logs, a.saida)
    print(f"Gráficos salvos em: {os.path.abspath(a.saida)}")


if __name__ == "__main__":
    main()
