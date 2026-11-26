**codigos do genetico**: <funcao>-genetico/main.py

**codigos do PSO**: <funcao>-pso/main.py

**como rodar** (ex.: rastrigin):
1. python3 rastrigin-genetico/main.py
2. python3 rastrigin-pso/main.py
3. python3 comparar.py
4. python3 plot.py (graficos são salvos em ./graficos/ )

Eu peguei outras funções continuas para comparar os algoritmos:

- **Sphere**: mede velocidade pura de explotação/refinamento local (https://www.sfu.ca/~ssurjano/spheref.html).

- **Rosenbrock**: pune algoritmos que não conseguem coordenar movimentos nas duas dimensões simultaneamente (https://www.sfu.ca/~ssurjano/rosen.html).

- **Ackley**: meio que parece um Rastringin mas com otimos globais masi espaçados (https://www.sfu.ca/~ssurjano/ackley.html).

Depois, eu vi qual foi o melhor algoritmo (PSO+migracao) e qual das funções era a mais difícil de otimizar (Rastrigin) e fiz execuções aumentando a dimensão do problema (2D até 10D). Para cada dimensão foi feito 50 execuções, das quais tiramos as métricas.
