# TST-004 · Desconto percentual com autorização

**Caso de uso** UC-004 — Aplicar desconto  
**Origem** `Caso de teste de Aplicação de desconto.xlsx`

## Pré-condições

- Use o ambiente do [TST-001](tst-001-login.md). Em **Configurações**, confirme o limite de desconto sem autorização de 5%.
- Cadastre um produto de R$ 200,00 com pelo menos uma unidade em lote válido. Entre como operador e abra um turno em **PDV / Caixa**. Tenha uma conta de gerente habilitada para autorizar a operação.

## Passos e resultados esperados

1. Adicione uma unidade do produto. Confira o total inicial de R$ 200,00.
2. Em **Desconto na venda**, informe `10` e selecione **%** em **Tipo**. O total exibido deve ser R$ 180,00.
3. Selecione **PIX**, marque **Confirmei o recebimento** como simulação e clique em **Concluir venda** sem preencher a autorização. O sistema deve solicitar credenciais gerenciais e manter a venda sem registro.
4. Clique em **Voltar e revisar**. Se o navegador tiver descartado o carrinho, monte a venda novamente com os mesmos dados. Expanda **Autorização gerencial** e peça ao gerente de teste para preencher **Usuário do gerente** e **Senha de autorização**.
5. Confirme o pagamento simulado e clique em **Concluir venda**. O comprovante deve exibir desconto de R$ 20,00 e total de R$ 180,00. Em **Vendas do turno**, deve haver apenas um novo registro para o cenário.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
