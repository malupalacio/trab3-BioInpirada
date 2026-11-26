"""
Código compartilhado entre o Genetico (main_alterado_para_comparacao_com_PSO.py) e 
o PSO (../main_alterado_para_comparacao_com_genetico.py).

fazendo isso a gente tem certeza que os dois algoritmos usam o mesmo problema, o mesmo contador
de avaliações, as mesmas métricas e o mesmo formato de CSV.
"""
import argparse
import csv
import math
import os
import statistics
import time

# --- DEFINIÇÕES DO PROBLEMA ---
DIMENSOES = 2
LIMITES = (-5.12, 5.12)
LIMIAR_SUCESSO = 1e-2     # fiz fitness <= limiar contar como "sucesso"
PASSO_CURVA = 100         # a curva de convergência é salva a cada 100 avaliações


def rastrigin(x):
    A = 10
    return A * len(x) + sum(xi ** 2 - A * math.cos(2 * math.pi * xi) for xi in x)


class Contador:
    """Toda avaliação da função objetivo passa por aqui. Ent fiz uma lógica de
    contador, pra gente saber em que momento cada estratégia chegou no seu "ótimo global"
    e quantas iterações ela demorou.

    Guarda: nº de avaliações, melhor fitness já avaliado, em qual avaliação o
    limiar foi atingido e o melhor fitness após cada avaliação (para a curva).
    """

    def __init__(self):
        self.n = 0
        self.melhor = float("inf")
        self.aval_ate_limiar = None
        self.trajetoria = []
        self.t0 = time.perf_counter()   # o relógio começa quando a execução cria o Contador
        self.tempo_melhor = 0.0         # instante (s) em que o melhor fitness final foi encontrado

    def avaliar(self, x):
        self.n += 1
        f = rastrigin(x)
        if f < self.melhor:
            self.melhor = f
            self.tempo_melhor = time.perf_counter() - self.t0
            if self.aval_ate_limiar is None and f <= LIMIAR_SUCESSO:
                self.aval_ate_limiar = self.n
        self.trajetoria.append(self.melhor)
        return f

    def resultado(self, seed):
        return {
            "seed": seed,
            "fitness": self.melhor,
            "avaliacoes": self.n,
            "aval_ate_limiar": self.aval_ate_limiar,
            "tempo_melhor": self.tempo_melhor,
            "tempo_total": time.perf_counter() - self.t0,
            "trajetoria": self.trajetoria,
        }

def criar_parser(descricao):
    ap = argparse.ArgumentParser(description=descricao)
    ap.add_argument("--runs", type=int, default=50, help="nº de execuções (padrão 30)")
    ap.add_argument("--seed", type=int, default=0, help="semente base: a execução i usa seed+i")
    ap.add_argument("--pasta", type=str, default="resultados", help="pasta de saída dos CSVs")
    ap.add_argument("--verbose", action="store_true", help="1 execução detalhada, sem salvar CSV")
    return ap


def salvar_resultados(caminho, resultados):
    with open(caminho, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "fitness", "avaliacoes", "aval_ate_limiar", "tempo_melhor_s", "tempo_total_s"])
        for r in resultados:
            aut = "" if r["aval_ate_limiar"] is None else r["aval_ate_limiar"]
            w.writerow([r["seed"], f"{r['fitness']:.10f}", r["avaliacoes"], aut,
                        f"{r['tempo_melhor']:.6f}", f"{r['tempo_total']:.6f}"])


def salvar_curvas(caminho, resultados):
    """Melhor fitness (média, mediana e desvio entre as execuções) a cada PASSO_CURVA avaliações."""
    n_min = min(len(r["trajetoria"]) for r in resultados)
    pontos = list(range(PASSO_CURVA, n_min + 1, PASSO_CURVA))
    if not pontos or pontos[-1] != n_min:
        pontos.append(n_min)
    with open(caminho, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["avaliacoes", "media", "mediana", "desvio"])
        for k in pontos:
            vals = [r["trajetoria"][k - 1] for r in resultados]
            desvio = statistics.pstdev(vals) if len(vals) > 1 else 0.0
            w.writerow([
                k,
                f"{statistics.mean(vals):.8f}",
                f"{statistics.median(vals):.8f}",
                f"{desvio:.8f}",
            ])


def resumir(nome, resultados):
    fits = [r["fitness"] for r in resultados]
    sucessos = [r["aval_ate_limiar"] for r in resultados if r["aval_ate_limiar"] is not None]
    print(f"\n[{nome}]  ({len(resultados)} execuções)")
    print(f"  Avaliações por execução : {resultados[0]['avaliacoes']}")
    print(f"  Fitness final  média    : {statistics.mean(fits):.6f}")
    print(f"                 desvio   : {statistics.pstdev(fits):.6f}")
    print(f"                 mediana  : {statistics.median(fits):.6f}")
    print(f"                 melhor   : {min(fits):.6f}")
    print(f"                 pior     : {max(fits):.6f}")
    print(f"  Taxa de sucesso (<= {LIMIAR_SUCESSO}): {len(sucessos)}/{len(resultados)}")
    if sucessos:
        print(f"  Avaliações até o limiar (média dos sucessos): {statistics.mean(sucessos):.0f}")
    tm = [r["tempo_melhor"] for r in resultados]
    tt = [r["tempo_total"] for r in resultados]
    print(f"  Tempo até o melhor resultado (s): média {statistics.mean(tm):.4f} | "
          f"mediana {statistics.median(tm):.4f} | desvio {statistics.pstdev(tm):.4f}")
    print(f"  Tempo total de execução   (s): média {statistics.mean(tt):.4f} | "
          f"mediana {statistics.median(tt):.4f} | desvio {statistics.pstdev(tt):.4f}")


def rodar_varias(nome, executar, args):
    """Roda executar(seed) para 'seeds' de 'seed' até 'seed+runs-1', dai printa o resumo e salva os CSVs."""
    resultados = [executar(args.seed + i) for i in range(args.runs)]
    resumir(nome, resultados)
    os.makedirs(args.pasta, exist_ok=True)
    saida = os.path.join(args.pasta, f"resultados_{nome}.csv")
    curvas = os.path.join(args.pasta, f"curvas_{nome}.csv")
    salvar_resultados(saida, resultados)
    salvar_curvas(curvas, resultados)
    print(f"  Salvo: {saida} e {curvas}")
    return resultados