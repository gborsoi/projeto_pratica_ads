# TST-006 · Fechamento sem divergência

**Caso de uso** UC-006 — Fechar caixa  
**Origem** `Caso de teste de Fechamento de Caixa.xlsx`

## Pré-condições

- Use o ambiente do [TST-001](tst-001-login.md). Cadastre um produto a R$ 50,00 com pelo menos 23 unidades vendáveis.
- Como operador, abra um turno novo com fundo de R$ 0,00. Registre quatro vendas em **Dinheiro**, de 4, 10, 6 e 3 unidades, recebendo exatamente R$ 200,00, R$ 500,00, R$ 300,00 e R$ 150,00, respectivamente. Confirme cada pagamento simulado. Deixe o carrinho vazio e mantenha o turno aberto.

## Passos e resultados esperados

1. Em **PDV / Caixa**, abra **Fechamento → Conferir valores do turno**. Confira o esperado de R$ 1.150,00 em **Dinheiro** e R$ 0,00 nos cinco demais meios.
2. Informe `1150,00` em **Dinheiro** e `0,00` em **PIX**, **Débito**, **Crédito**, **Vale-alimentação** e **Vale-refeição**.
3. Clique em **Confirmar fechamento** e confirme o diálogo do navegador.
4. Na tela **Conferência de caixa**, confira R$ 1.150,00 nas colunas **Esperado** e **Informado** para dinheiro e R$ 0,00 na coluna **Diferença** para todos os meios. Confira o horário de fechamento.
5. Volte a **PDV / Caixa**. Deve aparecer **Abertura de caixa**, e o turno encerrado deve constar em **Turnos recentes**.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
