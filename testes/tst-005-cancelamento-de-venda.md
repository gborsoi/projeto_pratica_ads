# TST-005 · Cancelamento de venda concluída

**Caso de uso** UC-005 — Cancelar venda  
**Origem** `Caso de teste de Cancelamento de Venda.xlsx`

## Pré-condições

- Use o ambiente do [TST-001](tst-001-login.md). Cadastre um produto de R$ 100,00 com 5 unidades em um único lote válido.
- Como operador, em um turno aberto, conclua uma venda de duas unidades por R$ 200,00 com **PIX** confirmado em simulação. Anote o número da venda e mantenha o turno aberto. Confira com o gerente que o saldo do lote caiu para 3.

## Passos e resultados esperados

1. No **PDV / Caixa**, localize a venda de R$ 200,00 em **Vendas do turno** pelo número anotado. Abra seu comprovante.
2. Em **Cancelamento**, expanda **Estornar venda**. Informe o motivo `Cancelamento de teste` e peça ao gerente de teste para preencher as credenciais de autorização.
3. Marque **Confirmo o estorno dos itens** e clique em **Confirmar cancelamento**.
4. Confira que o comprovante e a lista do turno apresentam a venda como **Cancelada**. O comprovante deve mostrar o motivo, o autorizador e o valor original de R$ 200,00.
5. Como gerente, confira em **Estoque** que o mesmo lote voltou a 5 unidades e que o histórico registra entrada de `+2` vinculada ao estorno.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
