# Métricas dos Testes

## Contagem de cenários e testes

O escopo desta medição são os 10 cenários planejados para a suíte manual da V1, identificados de TST-001 a TST-010. Eles estão vinculados a 9 casos de uso. O UC-001 tem dois cenários, login inicial e login após sair.

Na rodada de 18/11/2026, Gustavo registrou os 10 cenários como **Executado**, todos com **Resultado positivo**. A contagem considera esses registros como sucesso.

| Símbolo | Indicador | Total atual |
| --- | --- | ---: |
| $R_{ft}$ | Cenários planejados para teste | 10 |
| $T_i$ | Cenários com roteiro implementado em Markdown | 10 |
| $T_x$ | Cenários executados com resultado de sucesso ou falha | 10 |
| $T_s$ | Cenários executados com sucesso | 10 |
| $T_f$ | Cenários executados com falha | 0 |
| $T_n$ | Cenários não executados | 0 |
| $T_c$ | Cenários com execução cancelada | 0 |

## Cobertura

| Métrica | Fórmula | Resultado atual |
| --- | --- | ---: |
| Cobertura de testes implementados | $\frac{T_i}{R_{ft}} \times 100\%$ | $\frac{10}{10} \times 100\% = 100\%$ |
| Cobertura de testes executados | $\frac{T_x}{R_{ft}} \times 100\%$ | $\frac{10}{10} \times 100\% = 100\%$ |
| Cobertura de testes bem-sucedidos | $\frac{T_s}{R_{ft}} \times 100\%$ | $\frac{10}{10} \times 100\% = 100\%$ |
| Taxa de sucesso entre os executados | $\frac{T_s}{T_x} \times 100\%$ | $\frac{10}{10} \times 100\% = 100\%$ |

## Como atualizar

1. Registre o resultado de cada roteiro no campo **Status**, usando **Sucesso**, **Falha**, **Não executado** ou **Cancelado**. Para cada ciclo, conte um status por cenário.
2. Some os testes com sucesso e com falha para obter o total de executados ($T_x = T_s + T_f$). Confira se $T_i = T_x + T_n + T_c$.
3. Recalcule os percentuais usando as fórmulas da tabela. Se o escopo mudar, atualize também a quantidade de cenários planejados ($R_{ft}$).
