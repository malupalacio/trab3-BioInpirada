"""
PSO multi-enxame (4 enxames com perfis diferentes) para a função de Rastrigin 2D.

Diferenças em relação ao EA em ilhas (de propósito):
  - Enxames de tamanho FIXO: as partículas persistem, pois o conhecimento do PSO
    está em velocidade + pBest.
  - Sem grade, sem mapa logístico, sem turnover, sem histórico de linhagem.
  - Os enxames diferem em hiperparâmetros do PSO (w, c1, c2, vmax).
  - Migração é opcional e simples: periódica, topologia em anel.

O que é igual ao protocolo do EA (para comparação justa):
  - Mesma função e mesmos limites.
  - Contagem de avaliações da função objetivo (orçamento).
  - Múltiplas execuções com sementes e estatísticas.

Uso:
  python pso_ilhas.py                        # 30 execuções, compara sem/com migração
  python pso_ilhas.py --runs 10 --seed 123
  python pso_ilhas.py --verbose              # imprime o progresso de 1 execução
  python pso_ilhas.py --csv curvas.csv       # salva curva de convergência média
"""
import argparse
import math
import random
import statistics

# --- PROBLEMA ---
DIMENSOES = 2
LIMITES = (-5.12, 5.12)
LIMIAR_SUCESSO = 1e-2     # fitness <= limiar conta como "sucesso"

# --- ORÇAMENTO ---
N_ENXAMES = 4
N_PARTICULAS = 50         # por enxame (fixo)
ITERACOES = 50
# Avaliações totais = N_ENXAMES * N_PARTICULAS * (ITERACOES + 1)  (+1 = inicialização)
# Ajuste N_PARTICULAS/ITERACOES para igualar ao nº real de avaliações do EA.

# --- MIGRAÇÃO (variante com migração) ---
INTERVALO_MIGRACAO = 10   # a cada K iterações
N_MIGRANTES = 1           # quantos migrantes cada enxame envia ao vizinho

# --- PERFIS DOS ENXAMES ---
# w_ini -> w_fim: inércia (decai linearmente; iguais = constante)
PERFIS = [
    {"nome": "Exploitativo", "w_ini": 0.4, "w_fim": 0.4, "c1": 1.0, "c2": 2.5, "vmax": 0.10},
    {"nome": "Balanceado",   "w_ini": 0.7, "w_fim": 0.7, "c1": 1.5, "c2": 1.5, "vmax": 0.20},
    {"nome": "Exploratório", "w_ini": 0.9, "w_fim": 0.9, "c1": 2.5, "c2": 1.0, "vmax": 0.30},
    {"nome": "Adaptativo",   "w_ini": 0.9, "w_fim": 0.4, "c1": 2.0, "c2": 2.0, "vmax": 0.20},
]


def rastrigin(x):
    A = 10
    return A * len(x) + sum(xi ** 2 - A * math.cos(2 * math.pi * xi) for xi in x)


class Contador:
    """Conta avaliações da função objetivo e registra quando o limiar é atingido."""

    def __init__(self):
        self.n = 0
        self.melhor = float("inf")
        self.aval_ate_limiar = None

    def avaliar(self, x):
        self.n += 1
        f = rastrigin(x)
        if f < self.melhor:
            self.melhor = f
            if self.aval_ate_limiar is None and f <= LIMIAR_SUCESSO:
                self.aval_ate_limiar = self.n
        return f


def criar_enxame(perfil, rng, cont):
    largura = LIMITES[1] - LIMITES[0]
    vmax = perfil["vmax"] * largura
    particulas = []
    for _ in range(N_PARTICULAS):
        x = [rng.uniform(*LIMITES) for _ in range(DIMENSOES)]
        v = [rng.uniform(-vmax, vmax) for _ in range(DIMENSOES)]
        f = cont.avaliar(x)
        particulas.append({"x": x, "v": v, "pbest_x": x.copy(), "pbest_f": f})
    return particulas


def melhor_pbest(enxame):
    return min(enxame, key=lambda p: p["pbest_f"])


def passo_pso(enxame, perfil, w, rng, cont):
    largura = LIMITES[1] - LIMITES[0]
    vmax = perfil["vmax"] * largura
    gbest = melhor_pbest(enxame)["pbest_x"].copy()  # gBest fixo durante a iteração

    for p in enxame:
        for k in range(DIMENSOES):
            r1, r2 = rng.random(), rng.random()
            v = (w * p["v"][k]
                 + perfil["c1"] * r1 * (p["pbest_x"][k] - p["x"][k])
                 + perfil["c2"] * r2 * (gbest[k] - p["x"][k]))
            v = max(-vmax, min(vmax, v))
            x = p["x"][k] + v
            if x < LIMITES[0] or x > LIMITES[1]:  # limite: trava e inverte/amortece
                x = max(LIMITES[0], min(LIMITES[1], x))
                v = -0.5 * v
            p["v"][k] = v
            p["x"][k] = x

        f = cont.avaliar(p["x"])
        if f < p["pbest_f"]:
            p["pbest_f"] = f
            p["pbest_x"] = p["x"].copy()


def migrar_anel(enxames):
    """O melhor pBest do enxame i substitui a pior partícula do enxame i+1.
    Os envios usam um snapshot, para que todos migrem 'ao mesmo tempo'.
    Migrantes já têm fitness conhecido, então não custam avaliações."""
    n = len(enxames)
    envios = []
    for e in enxames:
        melhores = sorted(e, key=lambda p: p["pbest_f"])[:N_MIGRANTES]
        envios.append([(m["pbest_x"].copy(), m["pbest_f"]) for m in melhores])

    for i in range(n):
        destino = enxames[(i + 1) % n]
        piores = sorted(range(len(destino)), key=lambda j: destino[j]["pbest_f"], reverse=True)
        for (x, f), idx in zip(envios[i], piores):
            destino[idx] = {"x": x.copy(), "v": [0.0] * DIMENSOES,
                            "pbest_x": x.copy(), "pbest_f": f}


def executar(seed, migracao, verbose=False):
    rng = random.Random(seed)
    cont = Contador()
    enxames = [criar_enxame(perfil, rng, cont) for perfil in PERFIS]

    curva = []  # melhor global ao fim de cada iteração
    for it in range(ITERACOES):
        fator = it / (ITERACOES - 1) if ITERACOES > 1 else 1.0
        for e, perfil in zip(enxames, PERFIS):
            w = perfil["w_ini"] - (perfil["w_ini"] - perfil["w_fim"]) * fator
            passo_pso(e, perfil, w, rng, cont)

        if migracao and (it + 1) % INTERVALO_MIGRACAO == 0 and it + 1 < ITERACOES:
            migrar_anel(enxames)

        melhores = [melhor_pbest(e) for e in enxames]
        melhor = min(melhores, key=lambda p: p["pbest_f"])
        curva.append(melhor["pbest_f"])

        if verbose:
            print(f"\n--- ITERAÇÃO {it + 1:02d} (avaliações={cont.n}) ---")
            for perfil, m in zip(PERFIS, melhores):
                print(f"  {perfil['nome']:<13}: melhor pBest = {m['pbest_f']:.6f}")
            print(f"-> Melhor global: {melhor['pbest_f']:.6f}")

    melhor = min((melhor_pbest(e) for e in enxames), key=lambda p: p["pbest_f"])
    return {
        "fitness": melhor["pbest_f"],
        "x": melhor["pbest_x"],
        "avaliacoes": cont.n,
        "aval_ate_limiar": cont.aval_ate_limiar,
        "curva": curva,
        "por_enxame": [melhor_pbest(e)["pbest_f"] for e in enxames],
    }


def resumir(nome, resultados):
    fits = [r["fitness"] for r in resultados]
    sucessos = [r["aval_ate_limiar"] for r in resultados if r["aval_ate_limiar"] is not None]
    print(f"\n[{nome}]")
    print(f"  Avaliações por execução : {resultados[0]['avaliacoes']}")
    print(f"  Fitness final  média    : {statistics.mean(fits):.6f}")
    print(f"                 desvio   : {statistics.pstdev(fits):.6f}")
    print(f"                 mediana  : {statistics.median(fits):.6f}")
    print(f"                 melhor   : {min(fits):.6f}")
    print(f"                 pior     : {max(fits):.6f}")
    print(f"  Taxa de sucesso (<= {LIMIAR_SUCESSO}): {len(sucessos)}/{len(resultados)}")
    if sucessos:
        print(f"  Avaliações até o limiar (média dos sucessos): {statistics.mean(sucessos):.0f}")
    medias_enxame = [statistics.mean(r["por_enxame"][i] for r in resultados) for i in range(N_ENXAMES)]
    print("  Melhor fitness médio por enxame:")
    for perfil, m in zip(PERFIS, medias_enxame):
        print(f"    {perfil['nome']:<13}: {m:.6f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0, help="semente base (run i usa seed+i)")
    ap.add_argument("--verbose", action="store_true", help="1 execução detalhada (sem migração)")
    ap.add_argument("--csv", type=str, default=None, help="salva curvas médias de convergência")
    args = ap.parse_args()

    if args.verbose:
        r = executar(args.seed, migracao=False, verbose=True)
        print(f"\nFitness final: {r['fitness']:.6f} em x={[round(v, 4) for v in r['x']]}")
        return

    variantes = {"Sem migração": False, "Migração em anel": True}
    todos = {}
    for nome, mig in variantes.items():
        # mesmas sementes nas duas variantes -> comparação pareada
        todos[nome] = [executar(args.seed + i, mig) for i in range(args.runs)]
        resumir(nome, todos[nome])

    # Teste de Wilcoxon pareado (opcional, requer scipy)
    try:
        from scipy.stats import wilcoxon
        a = [r["fitness"] for r in todos["Sem migração"]]
        b = [r["fitness"] for r in todos["Migração em anel"]]
        stat, p = wilcoxon(a, b)
        print(f"\nWilcoxon pareado (sem vs com migração): p = {p:.4f}")
    except ImportError:
        print("\n(scipy não instalado: pulei o Wilcoxon. Use: pip install scipy)")
    except ValueError as e:
        print(f"\nWilcoxon não aplicável: {e}")

    if args.csv:
        with open(args.csv, "w") as f:
            f.write("iteracao," + ",".join(f"{n}" for n in variantes) + "\n")
            for it in range(ITERACOES):
                linha = [str(it + 1)]
                for nome in variantes:
                    linha.append(f"{statistics.mean(r['curva'][it] for r in todos[nome]):.8f}")
                f.write(",".join(linha) + "\n")
        print(f"Curvas médias salvas em {args.csv}")


if __name__ == "__main__":
    main()
