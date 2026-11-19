# TST-001 · Login do operador

**Caso de uso** UC-001 — Realizar login  
**Origem** `Caso de teste de login fluxo principal.xlsx`

## Preparação do ambiente

Para evitar alterações nos dados da loja, inicie uma instância de testes com um arquivo SQLite novo, em outra porta. Execute no PowerShell a partir da raiz do repositório:

```powershell
$env:MERCADO_DB = Join-Path ([System.IO.Path]::GetTempPath()) ("mercado-testes-" + [guid]::NewGuid() + ".sqlite3")
py -3 app.py --port 8001
```

Abra `http://127.0.0.1:8001` em uma janela privada ou em um perfil separado do navegador. No primeiro acesso, crie o proprietário. Em **Usuários → Novo usuário → Cadastrar usuário**, crie as contas fictícias `operador.teste` (perfil **Operador**) e `gerente.teste` (perfil **Gerente**), com senhas de teste de pelo menos 10 caracteres.

Para executar um cenário isoladamente, repita a preparação com um banco novo. Se reutilizar a mesma base, use códigos exclusivos por cenário e encerre os turnos anteriores antes de abrir um turno novo para o mesmo operador. Cadastre produtos pelos passos do [TST-007](tst-007-cadastro-de-produto.md), com os dados de cada cenário.

## Passos e resultados esperados

1. Saia da sessão do proprietário pelo botão **Sair**. A tela **Acesse sua conta** deve aparecer.
2. Em **Usuário**, informe `operador.teste`. Em **Senha**, informe a senha cadastrada para essa conta. Clique em **Entrar**.
3. Confira que o sistema abre **Visão geral**, mostra o nome da conta e o perfil **Operador**. No menu, confira **PDV / Caixa** e **Minha conta**. Os módulos **Usuários** e **Configurações** devem estar indisponíveis para esse perfil.

## Registro da execução

- **Status** Executado
- **Data e responsável** 18/11 - Gustavo
- **Resultado observado e evidências** - Resultado positivo - Operações realizadas corretamente
