"""
Escalabilidade dimensional do PSO multi-enxame em anel (PSO_anel) na Rastrigin (2D a 10D).
"""
import csv
import os
import random
import statistics

from comum import LIMIAR_SUCESSO, LIMITES, Contador, criar_parser, rodar_varias

N_ENXAMES = 4
N_PARTICULAS = 50
ITERACOES = 50

INTERVALO_MIGRACAO = 10
N_MIGRANTES = 1

PERFIS = [
    {"nome": "Exploitativo", "w_ini": 0.4, "w_fim": 0.4, "c1": 1.0, "c2": 2.5, "vmax": 0.10},
    {"nome": "Balanceado",   "w_ini": 0.7, "w_fim": 0.7, "c1": 1.5, "c2": 1.5, "vmax": 0.20},
    {"nome": "Exploratório", "w_ini": 0.9, "w_fim": 0.9, "c1": 2.5, "c2": 1.0, "vmax": 0.30},
    {"nome": "Adaptativo",   "w_ini": 0.9, "w_fim": 0.4, "c1": 2.0, "c2": 2.0, "vmax": 0.20},
]


def criar_enxame(perfil, rng, cont, n_part, dim):
    vmax = perfil["vmax"] * (LIMITES[1] - LIMITES[0])
    enxame = []
    for _ in range(n_part):
        x = [rng.uniform(*LIMITES) for _ in range(dim)]
        v = [rng.uniform(-vmax, vmax) for _ in range(dim)]
        f = cont.avaliar(x)
        enxame.append({"x": x, "v": v, "pbest_x": x.copy(), "pbest_f": f})
    return enxame


def melhor_pbest(enxame):
    return min(enxame, key=lambda p: p["pbest_f"])


def passo_pso(enxame, perfil, w, rng, cont, dim):
    vmax = perfil["vmax"] * (LIMITES[1] - LIMITES[0])
    gbest = melhor_pbest(enxame)["pbest_x"].copy()

    for p in enxame:
        for k in range(dim):
            r1, r2 = rng.random(), rng.random()
            v = (
                w * p["v"][k]
                + perfil["c1"] * r1 * (p["pbest_x"][k] - p["x"][k])
                + perfil["c2"] * r2 * (gbest[k] - p["x"][k])
            )
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


def migrar_anel(enxames, dim):
    n = len(enxames)
    envios = []
    for e in enxames:
        melhores = sorted(e, key=lambda p: p["pbest_f"])[:N_MIGRANTES]
        envios.append([(m["pbest_x"].copy(), m["pbest_f"]) for m in melhores])

    for i in range(n):
        destino = enxames[(i + 1) % n]
        piores = sorted(range(len(destino)), key=lambda j: destino[j]["pbest_f"], reverse=True)
        for (x, f), idx in zip(envios[i], piores):
            destino[idx] = {"x": x.copy(), "v": [0.0] * dim, "pbest_x": x.copy(), "pbest_f": f}


def executar(seed, dim, n_part=N_PARTICULAS, iteracoes=ITERACOES, verbose=False):
    rng = random.Random(seed)
    cont = Contador()
    enxames = [criar_enxame(perfil, rng, cont, n_part, dim) for perfil in PERFIS]

    for it in range(iteracoes):
        fator = it / (iteracoes - 1) if iteracoes > 1 else 1.0
        for e, perfil in zip(enxames, PERFIS):
            w = perfil["w_ini"] - (perfil["w_ini"] - perfil["w_fim"]) * fator
            passo_pso(e, perfil, w, rng, cont, dim)

        if (it + 1) % INTERVALO_MIGRACAO == 0 and it + 1 < iteracoes:
            migrar_anel(enxames, dim)

        if verbose:
            print(f"\n--- DIM={dim} | ITERAÇÃO {it + 1:02d} (avaliações={cont.n}) ---")
            for perfil, e in zip(PERFIS, enxames):
                print(f"  {perfil['nome']:<13}: melhor pBest = {melhor_pbest(e)['pbest_f']:.6f}")
            print(f"-> Melhor global: {cont.melhor:.6f}")

    return cont.resultado(seed)


def salvar_resumo_dimensoes(caminho, linhas_resumo):
    with open(caminho, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "dimensoes",
            "runs",
            "avaliacoes",
            "fitness_media",
            "fitness_desvio",
            "fitness_mediana",
            "fitness_melhor",
            "fitness_pior",
            "sucessos",
            "taxa_sucesso",
            "aval_limiar_media",
            "tempo_melhor_media_s",
            "tempo_total_media_s",
        ])
        for row in linhas_resumo:
            w.writerow(row)


def main():
    ap = criar_parser("Escalabilidade do PSO_anel na Rastrigin (2D a 10D)")
    args = ap.parse_args()

    if args.verbose:
        executar(args.seed, args.dim_min, verbose=True)
        return

    resumo_geral = []
    for dim in range(args.dim_min, args.dim_max + 1):
        nome = f"PSO_anel_D{dim}"
        resultados = rodar_varias(nome, lambda s, d=dim: executar(s, d), args)

        fits = [r["fitness"] for r in resultados]
        sucessos = [r["aval_ate_limiar"] for r in resultados if r["aval_ate_limiar"] is not None]
        aval_limiar = f"{statistics.mean(sucessos):.2f}" if sucessos else ""

        resumo_geral.append([
            dim,
            len(resultados),
            resultados[0]["avaliacoes"],
            f"{statistics.mean(fits):.10f}",
            f"{statistics.pstdev(fits):.10f}",
            f"{statistics.median(fits):.10f}",
            f"{min(fits):.10f}",
            f"{max(fits):.10f}",
            len(sucessos),
            f"{len(sucessos) / len(resultados):.4f}",
            aval_limiar,
            f"{statistics.mean(r['tempo_melhor'] for r in resultados):.6f}",
            f"{statistics.mean(r['tempo_total'] for r in resultados):.6f}",
        ])

    caminho_resumo = os.path.join(args.pasta, "resumo_dimensoes_PSO_anel.csv")
    salvar_resumo_dimensoes(caminho_resumo, resumo_geral)
    print(f"\nResumo consolidado salvo em: {caminho_resumo}")


if __name__ == "__main__":
    main()