# Comparação das estratégias de migração

Foram feitas 10 execuções de 50 gerações para cada configuração. A função de
Rastrigin é minimizada: quanto menor o fitness, melhor; o ótimo global é `0`.

| Estratégia | Melhor fitness | Fitness médio | Leitura rápida |
| --- | ---: | ---: | --- |
| Padrão (`D = 0,20`) | 0,029574 | **0,230130** | Melhor resultado médio. |
| Torneio com 3 candidatos | 0,046290 | 0,346314 | Menos consistente. |
| Torneio com 6 candidatos | 0,021197 | 0,252822 | Melhor que o torneio com 3, mas não supera a média da padrão. |
| Adaptativa | **0,002014** | 0,266598 | Encontrou a solução mais próxima do ótimo. |

## Estratégias avaliadas

- **Padrão:** a taxa de migração é fixa em 20% e o pai externo é sorteado.
- **Torneio por fitness:** o pai externo é escolhido entre os melhores de uma
  amostra de 3 ou 6 indivíduos.
- **Adaptativa:** a taxa de cada ilha aumenta quando ela estagna e diminui
  quando as ilhas ficam muito parecidas.

## Conclusão

A estratégia **adaptativa** encontrou a melhor solução individual (`0,002014`),
muito próxima do ótimo global. Porém, a estratégia **padrão** foi a mais
consistente, pois apresentou o menor fitness médio nas 10 execuções.

O torneio por fitness não trouxe ganho claro neste experimento. Para buscar a
melhor solução possível, a estratégia adaptativa é a opção mais promissora. Para
resultados mais estáveis, a estratégia padrão é a melhor escolha entre as
configurações testadas.

Os logs usados estão em `rastrigin/result/`.
