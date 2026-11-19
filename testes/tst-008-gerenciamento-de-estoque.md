# TST-008 · Saída de estoque por lote

**Caso de uso** UC-008 — Gerenciar estoque  
**Origem** `Caso de teste de Gerenciado de produto.xlsx`

## Pré-condições

Use o ambiente do [TST-001](tst-001-login.md) e entre como gerente. Cadastre **Feijão Ajuste** com 10 unidades em um único lote `FEI-A`, com validade futura.

## Passos e resultados esperados

1. Abra **Estoque** e confira que o saldo inicial do produto e do lote é 10.
2. Em **Movimentar estoque**, escolha **Saída / perda** no campo **Tipo** e selecione **Feijão Ajuste · FEI-A** em **Lote existente**.
3. Informe **Quantidade** `5` e **Motivo** `Avaria de teste`. Clique em **Registrar ajuste**.
4. Confira saldos **Físico** e **Disponível** iguais a 5 para o produto, e saldo de 5 no lote.
5. Em **Movimentações recentes**, confira o lançamento de `-5`, o lote `FEI-A`, o motivo informado e o usuário gerente.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
