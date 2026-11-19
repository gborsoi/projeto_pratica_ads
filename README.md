# Mercado Central

Sistema web local de gestão para pequenos supermercados. A especificação orienta as regras e os perfis. O guia do usuário orienta os fluxos de operação. A interface é própria deste projeto.

## Executar no Windows

1. Tenha Python 3.11 ou superior disponível no terminal. O projeto usa a biblioteca padrão e SQLite.
2. Na pasta do repositório, execute:

   ```powershell
   py -3 app.py
   ```

   Se o comando `py` estiver indisponível, use `python app.py` com uma instalação funcional do Python. Use `--port 8080` se a porta 8000 estiver ocupada.
3. Abra [http://127.0.0.1:8000](http://127.0.0.1:8000) e cadastre a primeira conta, com perfil de proprietário.
4. Em **Configurações**, defina o nome da loja e o limite de desconto sem autorização, inicialmente em 5%. Em **Usuários**, crie os acessos da equipe.

O banco `mercado.sqlite3` é criado na primeira execução. A variável de ambiente `MERCADO_DB` permite escolher outro caminho gravável. Encerre o servidor para fazer uma cópia do banco em repouso.

## Hospedar no PythonAnywhere

Use uma base de demonstração com dados fictícios. No console Bash, entre na pasta que contém `app.py` e execute com a mesma versão de Python (3.11 ou superior) escolhida na aba **Web**:

```bash
mkdir -p "$HOME/mercado-dados"
MERCADO_DB="$HOME/mercado-dados/demonstracao.sqlite3" python3.13 app.py --init-owner
```

O comando cria o banco e solicita os dados do primeiro proprietário. Escolha uma senha exclusiva. Na aba **Web**, crie uma aplicação com **Manual configuration** e abra o arquivo WSGI indicado no painel. Ajuste os dois caminhos abaixo para o nome da sua conta e a pasta do código:

```python
import os
import sys

os.environ["MERCADO_DB"] = "/home/SEU_USUARIO/mercado-dados/demonstracao.sqlite3"
sys.path.insert(0, "/home/SEU_USUARIO/projeto_pratica_ads")

from wsgi import application
```

Ative **Force HTTPS**, clique em **Reload** e abra o endereço HTTPS mostrado no painel. Confira o login do proprietário e crie os acessos de gerente e operador para a avaliação. A criação inicial do proprietário pelo navegador está disponível na execução local. Na hospedagem, use o comando do console antes de compartilhar o link.

## Fluxos disponíveis

- **Caixa:** abertura com fundo, leitura de código de barras como entrada de teclado, busca manual, descontos, confirmação de pagamento, troco, comprovante e fechamento por meio de pagamento.
- **Estoque:** cadastro e inativação de produtos, entradas e ajustes por lote, histórico, estoque mínimo e alertas de validade nos próximos 30 dias. O PDV baixa primeiro o lote com validade mais próxima entre os lotes vendáveis.
- **Supervisão:** autorização gerencial, cancelamento de venda com estorno dos lotes, reabertura de caixa, perfis e auditoria.
- **Gestão:** pedidos de compra e conferência, clientes, fornecedores, contas a pagar e a receber, relatórios por período e impressão ou exportação em PDF pelo navegador.

## Integrações e recorte desta versão

- PIX, cartão e vales têm confirmação manual no PDV. A confirmação automática depende de uma integração de pagamento.
- A conciliação fiscal aceita a referência de uma nota emitida externamente. Emissão fiscal, cancelamento fiscal e envio de notas por e-mail dependem de integração.
- O servidor escuta em `127.0.0.1` para execução local. Acesso por vários computadores exige uma configuração de hospedagem própria.
- O cadastro trabalha com quantidades inteiras. Cada pedido registra um produto, e as permissões são atribuídas por perfil e situação da conta.
