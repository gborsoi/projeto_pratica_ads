# TST-002 · Venda com pagamento em crédito

**Caso de uso** UC-002 — Realizar venda  
**Origem** `Caso de teste de Venda-1.xlsx`

## Pré-condições

- Use o ambiente descrito no [TST-001](tst-001-login.md).
- Cadastre **Arroz Venda** a R$ 20,00 por unidade e **Feijão Venda** a R$ 10,00 por unidade. Atribua a cada produto um SKU, um código de barras exclusivo e um lote com 10 unidades e validade futura.
- Entre como operador. Em **PDV / Caixa**, abra um turno com número livre e fundo de R$ 0,00.

## Passos e resultados esperados

1. Em **Itens da venda**, preencha **Quantidade** com `3` e informe o código do arroz em **Produto por código ou nome**. Clique em **Adicionar** ou pressione Enter no campo de busca. Confira 3 unidades e subtotal de R$ 60,00.
2. Repita com 3 unidades de feijão. Confira o subtotal de R$ 30,00 e o total da venda de R$ 90,00.
3. Em **Forma de pagamento**, selecione **Crédito**. Em ambiente de teste, marque **Confirmei o recebimento** como simulação e clique em **Concluir venda**.
4. Confira o **Comprovante** com a venda **Concluída**, pagamento **Crédito**, os dois itens e total de R$ 90,00.
5. Em outra sessão, entre como gerente e abra **Estoque**. Confira 7 unidades em cada lote e duas movimentações de `-3` vinculadas ao número da venda.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
