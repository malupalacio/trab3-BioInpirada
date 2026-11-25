"""
PSO multi-enxame (4 enxames com perfis diferentes) para a Rastrigin 2D.

Enxames de tamanho fixo, sem grade/logística/turnover. A migração é opcional
(topologia em anel, periódica).

"""
import random

from comum import DIMENSOES, LIMITES, Contador, criar_parser, rodar_varias


N_ENXAMES = 4
N_PARTICULAS = 50         # por enxame (fixo)
ITERACOES = 50
# Avaliações totais = N_ENXAMES * N_PARTICULAS * (ITERACOES + 1)  (+1 = inicialização)

# --- MIGRAÇÃO (variante com migração) ---
INTERVALO_MIGRACAO = 10   # a cada K iterações
N_MIGRANTES = 1           # quantos migrantes cada enxame envia ao vizinho

# w_ini -> w_fim: inércia (decai linearmente; iguais = constante). vmax = fração da largura do domínio.
PERFIS = [
    {"nome": "Exploitativo", "w_ini": 0.4, "w_fim": 0.4, "c1": 1.0, "c2": 2.5, "vmax": 0.10},
    {"nome": "Balanceado",   "w_ini": 0.7, "w_fim": 0.7, "c1": 1.5, "c2": 1.5, "vmax": 0.20},
    {"nome": "Exploratório", "w_ini": 0.9, "w_fim": 0.9, "c1": 2.5, "c2": 1.0, "vmax": 0.30},
    {"nome": "Adaptativo",   "w_ini": 0.9, "w_fim": 0.4, "c1": 2.0, "c2": 2.0, "vmax": 0.20},
]


def criar_enxame(perfil, rng, cont, n_part):
    vmax = perfil["vmax"] * (LIMITES[1] - LIMITES[0])
    enxame = []
    for _ in range(n_part):
        x = [rng.uniform(*LIMITES) for _ in range(DIMENSOES)]
        v = [rng.uniform(-vmax, vmax) for _ in range(DIMENSOES)]
        f = cont.avaliar(x)
        enxame.append({"x": x, "v": v, "pbest_x": x.copy(), "pbest_f": f})
    return enxame


def melhor_pbest(enxame):
    return min(enxame, key=lambda p: p["pbest_f"])


def passo_pso(enxame, perfil, w, rng, cont):
    vmax = perfil["vmax"] * (LIMITES[1] - LIMITES[0])
    gbest = melhor_pbest(enxame)["pbest_x"].copy()  # gBest fixo durante a iteração

    for p in enxame:
        for k in range(DIMENSOES):
            r1, r2 = rng.random(), rng.random()
            v = (w * p["v"][k]
                 + perfil["c1"] * r1 * (p["pbest_x"][k] - p["x"][k])
                 + perfil["c2"] * r2 * (gbest[k] - p["x"][k]))
            v = max(-vmax, min(vmax, v))
            x = p["x"][k] + v
            if x < LIMITES[0] or x > LIMITES[1]:
                x = max(LIMITES[0], min(LIMITES[1], x))
                v = -0.5 * v
            p["v"][k] = v
            p["x"][k] = x

        f = cont.avaliar(p["x"])
        if f < p["pbest_f"]:
            p["pbest_f"] = f
            p["pbest_x"] = p["x"].copy()


def migrar_anel(enxames):
    """Melhor pBest do enxame i substitui a pior partícula do enxame i+1 (snapshot simultâneo).
    O fitness do migrante já é conhecido, então não custa avaliação."""
    n = len(enxames)
    envios = []
    for e in enxames:
        melhores = sorted(e, key=lambda p: p["pbest_f"])[:N_MIGRANTES]
        envios.append([(m["pbest_x"].copy(), m["pbest_f"]) for m in melhores])

    for i in range(n):
        destino = enxames[(i + 1) % n]
        piores = sorted(range(len(destino)), key=lambda j: destino[j]["pbest_f"], reverse=True)
        for (x, f), idx in zip(envios[i], piores):
            destino[idx] = {"x": x.copy(), "v": [0.0] * DIMENSOES, "pbest_x": x.copy(), "pbest_f": f}


def executar(seed, migracao, n_part, iteracoes, verbose=False):
    rng = random.Random(seed)
    cont = Contador()
    enxames = [criar_enxame(perfil, rng, cont, n_part) for perfil in PERFIS]

    for it in range(iteracoes):
        fator = it / (iteracoes - 1) if iteracoes > 1 else 1.0
        for e, perfil in zip(enxames, PERFIS):
            w = perfil["w_ini"] - (perfil["w_ini"] - perfil["w_fim"]) * fator
            passo_pso(e, perfil, w, rng, cont)

        if migracao and (it + 1) % INTERVALO_MIGRACAO == 0 and it + 1 < iteracoes:
            migrar_anel(enxames)

        if verbose:
            print(f"\n--- ITERAÇÃO {it + 1:02d} (avaliações={cont.n}) ---")
            for perfil, e in zip(PERFIS, enxames):
                print(f"  {perfil['nome']:<13}: melhor pBest = {melhor_pbest(e)['pbest_f']:.6f}")
            print(f"-> Melhor global: {cont.melhor:.6f}")

    return cont.resultado(seed)


def main():
    ap = criar_parser("PSO multi-enxame na Rastrigin 2D")
    ap.add_argument("--migracao", choices=["nao", "anel", "ambas"], default="ambas")
    args = ap.parse_args()

    if args.verbose:
        executar(args.seed, args.migracao == "anel", N_PARTICULAS, ITERACOES, verbose=True)
        return

    variantes = []
    if args.migracao in ("nao", "ambas"):
        variantes.append(("PSO_sem_migracao", False))
    if args.migracao in ("anel", "ambas"):
        variantes.append(("PSO_anel", True))

    for nome, mig in variantes:
        rodar_varias(nome, lambda s, m=mig: executar(s, m, N_PARTICULAS, ITERACOES), args)


if __name__ == "__main__":
    main()