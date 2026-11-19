# Versão PSO do modelo de ilhas — função Rastrigin

 A versão mantém o mesmo problema (minimização da função Rastrigin em duas dimensões) e a estrutura geral do modelo de ilhas. Foram alteradas somente as operações que dependiam de reprodução e mutação para utilizar o mecanismo do PSO.

## 1. O que foi mantido

| Elemento | Como ficou na versão PSO |
|---|---|
| Função objetivo | Rastrigin 2D, com domínio `[-5.12, 5.12]` em cada dimensão |
| Quantidade de ilhas | 4 |
| Grade de cada ilha | 10 x 10 posições |
| Número de gerações | 50 |
| Dinâmica logística | `R_INICIAL`, `R_FINAL`, `X_INICIAL` e `D` |
| Migração adaptativa | Mesmas regras, limites, limiares e cálculo por estagnação/diversidade |
| Atualização da população | Mesma regra de crescimento/redução da grade |
| Turnover | Substituição de 10% da população, como no original |
| Saída no terminal | Resumo por geração, resumo por ilha, melhor global e histórico final |

O código original percorre e atualiza as ilhas sequencialmente em um único processo Python. Esta versão preserva esse comportamento e não adiciona paralelismo por processos.

## 2. Alterações necessárias para o PSO

### Representação da solução

O indivíduo evolutivo armazenava posição (`x`), `sigma` e fitness. No PSO, cada partícula armazena:

- x: posiçãoatual;
- velocidade`: deslocamento da partícula em cada dimensão;
- fitness: avaliação da posição atual;
- pbest_x: melhor posição já visitada pela própria partícula;
- pbest_fitness: fitness da melhor posição pessoal;
- historico: trajetória da partícula, incluindo atualizações e migrações.

O sigma foi removido porque controlava a mutação gaussiana do algoritmo evolutivo e não participa da equação de movimento do PSO. Para preservar a diferença de intensidade de exploração que existia entre as ilhas, SIGMAS_BASE foi substituído por VELOCIDADES_INICIAIS, que define a amplitude da velocidade inicial de cada ilha.

### Movimento das partículas

A função de reprodução foi substituída por atualizar_enxame, que atualiza velocidade e posição conforme a equação do PSO:

```text
v[k] = w * v[k]
       + c1 * r1 * (pbest_x[k] - x[k])
       + c2 * r2 * (gbest_x[k] - x[k])

x[k] = x[k] + v[k]
```

`w` é a inércia; `c1` controla a atração pelo melhor pessoal (`pBest`); `c2` controla a atração pelo melhor da própria ilha (`gBest`); e `r1` e `r2` são valores aleatórios entre 0 e 1.

Cada ilha mantém seu próprio gBest. Assim, as partículas de uma ilha compartilham informação localmente, enquanto a troca entre ilhas continua sendo feita pela migração adaptativa.

### Parâmetros específicos do PSO

| Parâmetro | Valor | Função |
|---|---:|---|
| `INERCIA_INICIAL` | 0.9 | Inércia no início da execução |
| `INERCIA_FINAL` | 0.4 | Inércia no final da execução |
| `C1` | 2.0 | Influência do melhor pessoal |
| `C2` | 2.0 | Influência do melhor da ilha |
| `VMAX_FRACAO` | 0.20 | Limite da velocidade em relação à largura do domínio |
| `FATOR_REBOTE` | 0.5 | Amortece e inverte a velocidade quando a partícula alcança um limite |

A inércia diminui linearmente de 0.9 para 0.4 ao longo das 50 gerações. A velocidade é limitada e a posição é mantida dentro do domínio da Rastrigin.

### Melhor pessoal e melhor da ilha

Após cada movimento, o fitness atual é comparado com `pbest_fitness`. Quando a posição atual é melhor, a memória pessoal é atualizada. O melhor da ilha (`gBest`) é a melhor memória pessoal entre suas partículas.

Por isso, a diversidade entre ilhas e a contagem de estagnação passam a considerar as posições e os fitness `pBest`, e não apenas as posições atuais.

### Migração

A taxa adaptativa e o momento em que novas partículas são criadas foram mantidos. Como o PSO não realiza cruzamento entre pais, quando ocorre migração a nova partícula recebe a melhor posição pessoal de uma ilha externa e começa com velocidade zero. Quando não ocorre migração, a nova partícula é inicializada aleatoriamente.

A regra de migração, portanto, continua controlando a entrada de soluções externas, mas a operação de reprodução entre dois pais foi substituída pela transferência de uma partícula.


## 3. Resumo das substituições

| Algoritmo evolutivo original | Versão PSO |
|---|---|
| Indivíduo com posição e `sigma` | Partícula com posição, velocidade e `pBest` |
| Cruzamento entre dois pais | Atração cognitiva (`pBest`) e social (`gBest`) |
| Mutação gaussiana | Atualização da velocidade e posição |
| `sigma` adaptativo | Inércia, coeficientes `C1`/`C2` e limite de velocidade |
| Reprodução local ou entre ilhas | Inicialização de partículas ou migração de uma partícula |
| Linhagem genética | Histórico da trajetória da partícula |