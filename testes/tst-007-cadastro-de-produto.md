# TST-007 · Cadastro de produto com lote inicial

**Caso de uso** UC-007 — Cadastrar produto  
**Origem** `Caso de teste de Cadastro de produto.xlsx`

## Pré-condições

Use o ambiente do [TST-001](tst-001-login.md) e entre como gerente. Escolha um SKU e um código de barras ainda livres.

## Passos e resultados esperados

1. Abra **Produtos → Cadastro → Novo produto**.
2. Preencha **Nome** com `Arroz Cadastro`, **Código (SKU)** com `TST007-ARROZ` e **Código de barras** com `2000000000074`. Use **Categoria** `Mercearia`, **Unidade** `un`, **Custo (R$)** `12,00`, **Preço de venda (R$)** `20,00` e **Estoque mínimo** `2`.
3. Mantenha **Produto ativo** marcado. Informe **Estoque inicial** `10`, **Lote inicial** `CAD-A` e **Validade inicial** com uma data futura, por exemplo 60 dias após a execução. Clique em **Salvar**.
4. Em **Catálogo**, confira o produto com o SKU informado, categoria **Mercearia**, preço de R$ 20,00, saldo **Disponível** de 10 e situação **Ativo**.
5. Em **Estoque → Lotes**, confira o lote `CAD-A` com a validade informada e saldo de 10. O histórico deve ter uma entrada de `+10` com motivo **Estoque inicial**.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
