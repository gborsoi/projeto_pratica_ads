# TST-010 · Retorno ao sistema após encerrar a sessão

**Caso de uso** UC-001 — Realizar login  


## Pré-condições

Use o ambiente do [TST-001](tst-001-login.md). Entre como `operador.teste` e mantenha o mesmo navegador durante o teste.

## Passos e resultados esperados

1. Em **Visão geral**, clique em **Sair**. Confira que o sistema apresenta **Acesse sua conta**.
2. Digite diretamente `http://127.0.0.1:8001/pdv` na barra de endereços. O sistema deve apresentar a tela de login e impedir acesso à operação do caixa.
3. Informe novamente o usuário e a senha do operador e clique em **Entrar**. O sistema deve abrir **Visão geral** com o perfil **Operador**.
4. Clique em **PDV / Caixa**. O sistema deve apresentar a abertura de caixa ou o turno já existente para a conta.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
