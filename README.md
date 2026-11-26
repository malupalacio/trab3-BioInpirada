**codigo do genetico**: rastrigin-genetico/main.py

**codigo do PSO**: rastrigin-pso/main.py

**como rodar**:
1. python3 rastrigin-genetico/main.py
2. python3 rastrigin-pso/main.py
3. python3 comparar.py
4. python3 plot.py (graficos são salvos em ./graficos/ )

**Obs.:** Daria pra pegar outras funções continuas para comparar os algoritmos, não ficar só na rastringin:

- **Sphere**: mede velocidade pura de explotação/refinamento local (https://www.sfu.ca/~ssurjano/spheref.html).

- **Rosenbrock**: pune algoritmos que não conseguem coordenar movimentos nas duas dimensões simultaneamente (https://www.sfu.ca/~ssurjano/rosen.html).

- **Ackley**: meio que parece um Rastringin mas com otimos globais masi espaçados (https://www.sfu.ca/~ssurjano/ackley.html).