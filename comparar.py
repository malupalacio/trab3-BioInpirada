import argparse
import csv
import itertools
import os
import statistics

LIMIAR_SUCESSO = 1e-2


def ler(caminho):
    with open(caminho, newline="") as f:
        linhas = list(csv.DictReader(f))
    return {
        "fitness": [float(l["fitness"]) for l in linhas],
        "avaliacoes": int(linhas[0]["avaliacoes"]),
        "aval_ate_limiar": [int(l["aval_ate_limiar"]) for l in linhas if l["aval_ate_limiar"] != ""],
        "tempo_melhor": [float(l["tempo_melhor_s"]) for l in linhas if l.get("tempo_melhor_s")],
        "tempo_total": [float(l["tempo_total_s"]) for l in linhas if l.get("tempo_total_s")],
    }


def coletar_arquivos(pastas):
    arquivos = []
    for pasta in pastas:
        if not os.path.isdir(pasta):
            continue
        for nome_arq in sorted(os.listdir(pasta)):
            if nome_arq.startswith("resultados_") and nome_arq.endswith(".csv"):
                arquivos.append(os.path.join(pasta, nome_arq))
    return sorted(arquivos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pastas",
        nargs="+",
        default=["rastrigin-genetico/resultados", "rastrigin-pso/resultados", "resultados"],
        help="pastas onde buscar resultados_*.csv",
    )
    args = ap.parse_args()

    arquivos = coletar_arquivos(args.pastas)
    if not arquivos:
        raise SystemExit(f"Nenhum resultados_*.csv encontrado em: {args.pastas}")

    dados = {}
    for a in arquivos:
        nome = os.path.basename(a)[len("resultados_"):-len(".csv")]
        dados[nome] = ler(a)

    cab = (f"{'Algoritmo':<18}{'Runs':>5}{'Aval.':>7}{'Média':>11}{'Desvio':>11}"
           f"{'Mediana':>11}{'Melhor':>11}{'Pior':>11}{'Sucesso':>9}{'Aval→limiar':>13}")
    print(f"\nFitness final (menor é melhor; sucesso = fitness <= {LIMIAR_SUCESSO})")
    print(cab)
    print("-" * len(cab))
    for nome, d in dados.items():
        f = d["fitness"]
        s = d["aval_ate_limiar"]
        media_aval = f"{statistics.mean(s):.0f}" if s else "-"
        print(f"{nome:<18}{len(f):>5}{d['avaliacoes']:>7}{statistics.mean(f):>11.5f}"
              f"{statistics.pstdev(f):>11.5f}{statistics.median(f):>11.5f}{min(f):>11.5f}"
              f"{max(f):>11.5f}{f'{len(s)}/{len(f)}':>9}{media_aval:>13}")
    print("(Aval→limiar = média de avaliações até atingir o limiar, só entre as execuções que atingiram)")

    if all(d["tempo_total"] for d in dados.values()):
        cab_t = (f"{'Algoritmo':<18}{'Melhor: média':>15}{'mediana':>10}"
                 f"{'Total: média':>15}{'mediana':>10}")
        print("\nTempo de execução (segundos)")
        print(cab_t)
        print("-" * len(cab_t))
        for nome, d in dados.items():
            tm, tt = d["tempo_melhor"], d["tempo_total"]
            print(f"{nome:<18}{statistics.mean(tm):>15.4f}{statistics.median(tm):>10.4f}"
                  f"{statistics.mean(tt):>15.4f}{statistics.median(tt):>10.4f}")
        print("(Melhor = tempo até encontrar o melhor fitness final; Total = duração da execução inteira)")

    try:
        from scipy.stats import mannwhitneyu
    except ImportError:
        print("\n(scipy não instalado: pulei o teste estatístico. Use: pip install scipy)")
        return

    print("\nTeste de Wilcoxon da soma de postos (Mann-Whitney U), fitness final, bicaudal:")
    for a, b in itertools.combinations(dados, 2):
        try:
            p = mannwhitneyu(dados[a]["fitness"], dados[b]["fitness"], alternative="two-sided").pvalue
            veredito = "diferença significativa" if p < 0.05 else "sem diferença significativa"
            print(f"  {a} vs {b}: p = {p:.4g}  ({veredito} a 5%)")
        except ValueError as e:
            print(f"  {a} vs {b}: não aplicável ({e})")


if __name__ == "__main__":
    main()