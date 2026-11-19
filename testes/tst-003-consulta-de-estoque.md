# TST-003 · Consulta de estoque

**Caso de uso** UC-003 — Consultar estoque  
**Origem** `Caso de teste de Consulta de Estoque.xlsx`

## Pré-condições

- Use o ambiente do [TST-001](tst-001-login.md) e entre como gerente.
- Cadastre **Arroz Consulta** com estoque mínimo de 2 e um lote com validade futura e 8 unidades. Cadastre **Feijão Consulta** com estoque inicial de 0 e sem lote.

## Passos e resultados esperados

1. Abra **Estoque** no menu lateral. Na tabela **Saldos por produto**, localize **Arroz Consulta** pelo nome. Em uma lista extensa, use a busca do navegador.
2. Confira **Físico** e **Disponível** iguais a 8, **Mínimo** igual a 2 e situação **Regular**. Em **Lotes**, confira o lote e seu saldo de 8.
3. Localize **Feijão Consulta** na tabela de saldos. Confira **Físico** e **Disponível** iguais a 0 e situação **Em falta**.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
