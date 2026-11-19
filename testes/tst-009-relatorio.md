# TST-009 · Relatório de vendas e exportação em PDF

**Caso de uso** UC-009 — Emitir relatório  
**Origem** `Caso de teste de Relatório.xlsx`

## Pré-condições

- Use o ambiente do [TST-001](tst-001-login.md). Cadastre um produto a R$ 150,00 com 10 unidades ou mais em lote válido.
- Como operador, registre no mesmo dia dez vendas concluídas de uma unidade, sem desconto ou cancelamento. Use uma base em que essas sejam as únicas vendas do dia. Anote a data da execução e depois entre como gerente.

## Passos e resultados esperados

1. Abra **Relatórios**. Preencha **De** e **Até** com a data registrada e clique em **Filtrar**. O período usa a data real de registro das vendas.
2. Confira **Faturamento** de R$ 1.500,00, **Vendas concluídas** igual a 10 e **Ticket médio** de R$ 150,00. Em **Vendas e conciliação fiscal**, confira as dez vendas de R$ 150,00.
3. Clique em **Imprimir / salvar PDF** e selecione **Salvar como PDF** no diálogo do navegador.
4. Abra o PDF salvo. Confira que os indicadores e as dez vendas do período aparecem no documento.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
