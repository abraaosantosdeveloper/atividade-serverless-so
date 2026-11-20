# Atividade individual 1 — Serverless (Rota Vital: guia de transporte)

Infraestrutura de Software · ADS · CESAR School · 2026.2
**Estudante:** _<seu nome>_ · **Caminho escolhido:** A — AWS SAM CLI local (sem conta AWS)

Função serverless (AWS Lambda, Python 3.12) que recebe uma requisição do Rota Vital e gera a guia de transporte das bolsas. A função é acionada de dois jeitos: por **evento** (`sam local invoke`) e por **HTTP** (`sam local start-api` + `curl`, emulando o API Gateway).

## Estrutura

```
.
├── template.yaml          # SAM: função, rota POST /guias, Timeout em Globals
├── hello_world/app.py     # handler da função
├── events/pedido.json     # evento API Gateway gerado com sam local generate-event
├── tests/unit/            # testes unitários do handler (pytest)
└── evidencias/            # prints dos comandos e saídas
```

## Pré-requisitos

| Ferramenta | Versão usada | Como conferir |
|---|---|---|
| Docker Desktop (rodando) | 29.8.0 | `docker --version` |
| AWS SAM CLI | 1.174.0 | `sam --version` |
| Python | 3.12 | `python --version` |

> No Windows, rodar os comandos no **Git Bash** ou no **WSL**. Docker Desktop precisa estar **aberto** (`docker ps` não pode dar erro).

### Instalação do SAM CLI

- **Windows:** instalador `.msi` oficial — https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi. Depois de instalar, **feche e abra o terminal**.
- **macOS:** `.pkg` em https://github.com/aws/aws-sam-cli/releases/latest (arm64 para chip Apple, x86_64 para Intel).
- **Linux/WSL:** `aws-sam-cli-linux-x86_64.zip` na mesma página, `unzip` e `sudo ./sam-installation/install`.
- **Qualquer sistema (alternativa):** `pip install aws-sam-cli`.

### Problemas comuns no Windows (Git Bash)

| Sintoma | Causa | Solução |
|---|---|---|
| `sam: command not found` no Git Bash, mas funciona no PowerShell/CMD | No Windows o SAM é um `sam.cmd` e o Git Bash não o encontra só por `sam` | Usar `sam.cmd` ou criar um alias: `echo "alias sam='sam.cmd'" >> ~/.bashrc && source ~/.bashrc`. Se nem `sam.cmd` funcionar: `echo 'export PATH="$PATH:/c/Program Files/Amazon/AWSSAMCLI/bin"' >> ~/.bashrc` |
| `sam build` falha com `Binary validation failed for python ... did not satisfy constraints for runtime: python3.12` | O template usa Python 3.12 e a máquina tem outra versão (ex.: 3.13) | Usar **`sam build --use-container`** (o build roda num container com Python 3.12) ou instalar o Python 3.12 lado a lado. **Não** trocar o runtime no template |
| `'C:\Program' não é reconhecido como um comando interno ou externo` ao rodar `sam local generate-event ... --body '{...}'` | O `sam.cmd` passa pelo `cmd.exe`, que se perde com o espaço em `C:\Program Files` quando há JSON entre aspas nos argumentos | Não é preciso gerar o evento: `events/pedido.json` já está no repositório. Se precisar, rodar o comando no WSL/Linux/macOS |
| `events/pedido.json` ficou vazio | O `> events/pedido.json` do comando acima cria o arquivo mesmo quando o comando falha | Conferir com `head -5 events/pedido.json` e restaurar com `git checkout events/pedido.json` (ou extraindo de novo do zip) |
| Container não aparece no Docker Desktop depois do `build` ou do `invoke` | Comportamento normal: esses containers são temporários e removidos ao terminar. Só a **imagem** fica (aba *Images*) | Para ver um container ativo, usar `sam local start-api --warm-containers LAZY` e fazer uma chamada |
| `curl` devolve **502 Internal server error** e o log mostra `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` | O `curl` foi rodado no **CMD** (ou PowerShell) do Windows, que não reconhece aspas simples: o JSON chega à função com as aspas junto e fica inválido | Rodar o `curl` no **Git Bash**, ou mandar o corpo a partir de arquivo (funciona em qualquer terminal): `curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" -d @events/r002.json` (arquivos `events/r002.json` e `events/r003.json` já estão no repositório) |
| Comando quebrado em várias linhas não funciona | O `\` só continua o comando se for o **último caractere** da linha | Colando em uma linha só, apagar os `\` |

## Como rodar

### 1. Build e invocação por evento

```bash
sam build --use-container # roda utilizando container docker
sam local invoke -e events/pedido.json   # rodar 2 vezes e anotar o tempo
```

Para medir o tempo total: `time sam local invoke -e events/pedido.json`.

> A primeira execução baixa a imagem `public.ecr.aws/lambda/python:3.12` e por isso demora bem mais. Saída esperada: `"statusCode": 201` com `"invocacaoNesteAmbiente": 1`.

Para gerar o evento de novo (**não é necessário**: o arquivo já está no repositório; no Git Bash do Windows este comando falha — veja *Problemas comuns*):

```bash
sam local generate-event apigateway aws-proxy --method POST --path guias \
    --body '{"requisicaoId":"R-001","hospital":"H-Recife","bolsas":["O-NEG-0142"]}' \
    > events/pedido.json
```

### 2. Gatilho HTTP

> Rodar o `curl` no **Git Bash** (no CMD/PowerShell as aspas simples quebram o JSON). Alternativa que funciona em qualquer terminal: `-d @events/r002.json`.

**2a. Sem reaproveitamento explícito**

Terminal 1:

```bash
sam local start-api
```

Terminal 2, rodar **3 vezes** e anotar `invocacaoNesteAmbiente`:

```bash
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
    -d '{"requisicaoId":"R-002","hospital":"H-Caruaru"}'
```

**2b. Com `--warm-containers LAZY`**

Terminal 1: `Ctrl+C` no servidor e subir de novo:

```bash
sam local start-api --warm-containers LAZY
```

Terminal 2, rodar **3 vezes** de novo e comparar com o 2a (valores do contador e tempo da 1ª chamada):

```bash
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
    -d '{"requisicaoId":"R-002","hospital":"H-Caruaru"}'
```

### 3. Limite de tempo

**3a. Com `Timeout: 3`**

O repositório está com o valor final (**10**). Para reproduzir o erro, editar `template.yaml` e deixar:

```yaml
Globals:
  Function:
    Timeout: 3
```

Terminal 1 (`Ctrl+C` se o servidor estiver rodando):

```bash
sam build --use-container
sam local start-api
```

Terminal 2:

```bash
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
    -d '{"requisicaoId":"R-003","demorar":true}'
```

Esperado: `{"message":"Internal server error"}` (HTTP 502) e, no log do terminal 1, `Function 'HelloWorldFunction' timed out after 3 seconds`.

**3b. Com `Timeout: 10`**

Voltar `Timeout` para `10` no `template.yaml` e, no terminal 1 (`Ctrl+C` antes):

```bash
sam build --use-container
sam local start-api
```

Terminal 2, mesmo `curl` do 3a:

```bash
curl -X POST http://127.0.0.1:3000/guias -H "Content-Type: application/json" \
    -d '{"requisicaoId":"R-003","demorar":true}'
```

Esperado: depois de ~5 s, HTTP 201 com `"guia": "G-R-003"`.

### 4. Testes unitários (opcional)

```bash
pip install pytest
python -m pytest tests/unit
```

## Ajuste no código do enunciado (body em base64)

Na versão do SAM CLI que usei, o `sam local generate-event` gera o evento com `"isBase64Encoded": true` e o `body` codificado em base64. O código original fazia `json.loads(event["body"])` direto e quebrava com `JSONDecodeError`. Acrescentei a decodificação antes do `json.loads`:

```python
body = event.get("body") or "{}"
if event.get("isBase64Encoded"):      # o evento gerado pelo SAM vem em base64
    body = base64.b64decode(body).decode("utf-8")
pedido = json.loads(body)
```

Pelo `curl` o body chega em texto puro (`isBase64Encoded: false`), então os dois caminhos funcionam. Na nuvem o API Gateway também pode mandar o body em base64 (por exemplo, com conteúdo binário), então tratar isso é uma boa prática.

## Resultados

> Preencher com o que **você** mediu. Os valores entre colchetes são de um teste de referência (SAM CLI 1.174, Linux) só para comparação.

| Experimento | Resultado |
|---|---|
| `sam local invoke`, 1ª vez | _<tempo>_ [ref.: ~11,5 s, incluindo download da imagem `public.ecr.aws/lambda/python:3.12`] |
| `sam local invoke`, 2ª vez | _<tempo>_ [ref.: ~3,1 s; `Duration` ~40–50 ms] |
| `invocacaoNesteAmbiente` no `invoke` | _<valor>_ [ref.: sempre 1] |
| `start-api` sem `--warm-containers`, 3 chamadas | _<valores>_ [ref.: veja a pergunta 2] |
| `start-api --warm-containers LAZY`, 3 chamadas | _<valores>_ [ref.: 1, 2, 3; 1ª ~1,1 s, demais ~7 ms] |
| `demorar: true` com `Timeout: 3` | _<saída>_ [ref.: HTTP 502 `{"message":"Internal server error"}` e no log `Function 'HelloWorldFunction' timed out after 3 seconds`] |
| `demorar: true` com `Timeout: 10` | _<saída>_ [ref.: HTTP 201 após ~5 s, `Duration: 5041 ms`] |

## Respostas

> Rascunho de apoio: reescreva com as suas palavras e os seus números (a rubrica pede isso e vocês podem ser chamados a explicar).

**1. Por que a primeira invocação demorou mais que a segunda? O que acontece na fase de Init?**

A primeira invocação é um *cold start*: não existe ambiente de execução pronto, então ele precisa ser criado. No meu teste local, a primeira vez ainda incluiu o download da imagem do runtime Python 3.12, por isso demorou bem mais. Na fase de **Init** o Lambda cria o ambiente isolado (microVM, no caso local um container Docker), carrega o runtime, baixa/monta o código da função e executa tudo que está **fora** do handler (imports, variáveis globais como `contador = 0`, conexões abertas no topo do arquivo). Só depois disso vem a fase de **Invoke**, que roda o `lambda_handler`. Na nuvem esse tempo aparece como `Init Duration` no log. Uma observação: no `sam local invoke` cada execução cria um container novo, então as duas são "frias"; a segunda é mais rápida porque a imagem já está em cache, e o `invocacaoNesteAmbiente` volta sempre para 1.

**2. O que o campo `invocacaoNesteAmbiente` mostrou com e sem `--warm-containers`? O que isso diz sobre guardar estado numa variável global?**

Com `--warm-containers LAZY` o valor subiu 1, 2, 3: o container é criado na primeira chamada e reaproveitado nas seguintes, então a variável global continua na memória, e só a primeira chamada pagou o cold start. Sem a opção, _<descrever o que você viu>_. Nas versões mais antigas do SAM CLI cada requisição sobe um container novo e o valor fica sempre em 1. Na versão que usei como referência (1.174) o `start-api` já reaproveitou o container por padrão e também deu 1, 2, 3. Isso mostra o ponto principal: **reaproveitar ou não o ambiente é decisão da plataforma, não do código**. O Lambda pode reaproveitar, criar ambientes paralelos (cada um com seu próprio contador) ou descartar o ambiente a qualquer momento. Por isso a variável global serve como cache (ex.: conexão com banco, configuração), mas **não** para guardar estado de negócio. Estado tem que ir para um serviço externo (DynamoDB, RDS, S3, Redis).

**3. O que aconteceu com `demorar = true`? Qual é o tempo máximo no Lambda e o que fazer com trabalho mais longo?**

Com `Timeout: 3` a função foi interrompida depois de 3 segundos (`timed out after 3 seconds`) e o cliente recebeu **502 Internal server error**. A guia não foi gerada. Com `Timeout: 10` a chamada levou cerca de 5 s e retornou 201. O máximo configurável no Lambda é **900 segundos (15 minutos)**. Detalhe: atrás do API Gateway (REST), a requisição HTTP tem limite padrão de 29 s, então uma API síncrona deve responder bem antes disso. Para trabalho mais longo: quebrar em etapas menores orquestradas com **AWS Step Functions**; responder na hora com "recebido" e processar de forma assíncrona com uma fila (**SQS**) ou eventos; ou usar um serviço sem esse limite, como contêineres no **ECS/Fargate** ou **AWS Batch**.

**4. Custo de 1 milhão de execuções com 128 MB e 100 ms (us-east-1)**

- Requisições: 1.000.000 × (US$ 0,20 / 1.000.000) = **US$ 0,20**
- Memória em GB: 128 MB = 128 / 1024 = **0,125 GB**
- GB-s por execução: 0,125 GB × 0,1 s = **0,0125 GB-s**
- GB-s totais: 0,0125 × 1.000.000 = **12.500 GB-s**
- Computação: 12.500 × US$ 0,0000166667 = **US$ 0,2083**
- **Total ≈ US$ 0,20 + US$ 0,21 = US$ 0,41**

Considerando a faixa sempre gratuita (1 milhão de requisições e 400.000 GB-s por mês), esse volume sozinho sairia **US$ 0,00**.

**5. Onde uma função assim faria sentido no Rota Vital, e onde não faria?**

_<ajustar para a arquitetura real do seu grupo>_

Faz sentido em tarefas curtas, sem estado e disparadas por evento, com uso irregular: gerar a guia de transporte quando uma requisição de bolsa é aprovada; mandar notificação (e-mail/SMS/push) ao hospital quando o status da requisição muda; validar e gravar um pedido recebido por um webhook. Nesses casos só se paga quando há requisição e a escala acompanha os picos sozinha.

Não faz sentido no que precisa de estado ou de conexão longa e contínua: o rastreamento em tempo real do transporte (WebSocket aberto o tempo todo, atualização a cada poucos segundos); o banco de dados principal com o estoque de bolsas; processos que podem passar de 15 minutos; ou um endpoint crítico de baixíssima latência em que um cold start não é aceitável sem pagar por *provisioned concurrency*. Para esses, um serviço sempre ligado (contêiner/servidor) e um banco gerenciado são mais adequados.

## Evidências

Os prints estão em [`evidencias/`](evidencias/). O vídeo (até 3 min) está em: _<link do vídeo>_

## Uso de IA

| Ferramenta | Finalidade | Como validei |
|---|---|---|
| _<ex.: Claude (Anthropic)>_ | _<ex.: estruturar o projeto, identificar o problema do body em base64, revisar o README e o cálculo de custo>_ | _<ex.: rodei todos os comandos na minha máquina, conferi as saídas com os prints, refiz a conta de custo à mão e conferi o limite de 15 min na documentação de cotas do Lambda>_ |

Uso declarado conforme a PO-CESAR-021.
