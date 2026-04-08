# CRUD FastAPI + Apache + RabbitMQ + Datadog

Demo local para gerar tráfego observável com:

- `Apache` servindo uma UI estática e fazendo reverse proxy para a API
- `FastAPI` com CRUD em memória de `items`
- `RabbitMQ` recebendo eventos de `create`, `update` e `delete`
- `Worker` consumindo a fila e registrando processamento
- `Load Generator` opcional para gerar tráfego automático nos endpoints via Apache
- `Datadog Agent` coletando traces, logs e métricas de runtime

Para Data Streams Monitoring com RabbitMQ no Python, a aplicação usa `Kombu`, que é a biblioteca suportada pelo tracer do Datadog para esse cenário.
O projeto usa apenas auto-instrumentação com `ddtrace-run` e variáveis de ambiente; não depende de spans manuais no código.

## Requisitos

- Docker e Docker Compose
- Credenciais válidas do Datadog

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha estas variáveis:
   - `DD_API_KEY`
   - `DD_SITE`
   - `DD_ENV`
   - `DD_SERVICE`
   - `DD_VERSION`
   - `DD_RUM_APPLICATION_ID`
   - `DD_RUM_CLIENT_TOKEN`
   - `DD_RUM_SITE`
   - `DD_RUM_SERVICE`
   - `DD_RUM_ENV`
   - `DD_RUM_VERSION`
   - `DD_RUM_SESSION_SAMPLE_RATE`
   - `DD_RUM_SESSION_REPLAY_SAMPLE_RATE`
   - `DD_RUM_TRACK_RESOURCES`
   - `DD_RUM_TRACK_USER_INTERACTIONS`
   - `DD_RUM_TRACK_LONG_TASKS`
   - `DD_RUM_DEFAULT_PRIVACY_LEVEL`
   - `DD_RUM_ALLOWED_TRACING_PATHS`

3. Para o Terraform do Datadog, copie `datadog/terraform.tfvars.example` para `datadog/terraform.tfvars` e preencha:
   - `datadog_api_key`
   - `datadog_app_key`
   - `datadog_api_url`

Os serviços `api` e `worker` já saem com `DD_DATA_STREAMS_ENABLED=true` e `DD_TRACE_REMOVE_INTEGRATION_SERVICE_NAMES_ENABLED=true` no `docker-compose.yml` para habilitar Data Streams Monitoring no fluxo RabbitMQ.
As integrações automáticas relevantes também ficam explícitas no ambiente, como `DD_TRACE_FASTAPI_ENABLED=true`, `DD_TRACE_KOMBU_ENABLED=true` e `DD_LOGS_INJECTION=true`.
Os serviços Python (`api`, `worker` e `loadgen`) emitem logs estruturados em JSON, com serialização explícita de stack traces em logs de erro. Os campos de correlação `dd.trace_id`, `dd.span_id`, `dd.service`, `dd.env` e `dd.version` são preservados no payload JSON quando o `ddtrace` injeta esses valores no `LogRecord`.
Exceções não tratadas nos processos Python também passam pelo logger estruturado antes do encerramento do processo, evitando tracebacks multiline soltos em `stderr`.
O frontend continua estático, mas o container Apache gera `/config.js` em runtime a partir do `.env`, evitando deixar a configuração do Datadog RUM hardcoded no repositório.

## Execução

```bash
docker compose --env-file .env up --build
```

A aplicação ficará disponível em:

- UI + API via Apache: `http://localhost:8080`
- RabbitMQ Management: `http://localhost:15672`

O serviço `loadgen` sobe junto com o stack e gera ciclos contínuos de:

- `GET /health`
- `POST /api/items`
- `GET /api/items`
- `GET /api/items/{id}`
- `PUT /api/items/{id}`
- `DELETE /api/items/{id}`

Você pode controlar a cadência pelo `.env`:

- `LOADGEN_INTERVAL_SECONDS=2`
- `LOADGEN_TIMEOUT_SECONDS=10`

## Endpoints

- `GET /health`
- `GET /api/items`
- `GET /api/items/{id}`
- `POST /api/items`
- `PUT /api/items/{id}`
- `DELETE /api/items/{id}`

## Validando a instrumentação no Datadog

1. Abra `http://localhost:8080` e crie, edite e remova itens.
   Como alternativa, deixe o `loadgen` gerar tráfego automaticamente para popular o Live Tail e o APM.
2. Em APM, procure pelos serviços `${DD_SERVICE}-api` e `${DD_SERVICE}-worker`.
3. Procure também pelo serviço `${DD_SERVICE}-loadgen` se quiser ver a origem dos requests automáticos.
4. Valide traces do FastAPI para os endpoints `/api/items`.
5. Valide spans automáticos de HTTP e `Kombu` para publish/consume.
6. Em Logs, filtre pelos containers `appoena-demo-api`, `appoena-demo-worker` e `appoena-demo-loadgen` e confirme que os eventos JSON contêm `dd.trace_id` e `dd.span_id` quando houver spans ativos.
   Para validar stack traces, provoque uma falha controlada e confirme o campo `stack` no evento JSON.
7. Em Data Streams Monitoring, valide o caminho produtor `api` -> fila RabbitMQ -> consumidor `worker`.
8. Em Metrics ou Runtime Metrics, confira atividade da aplicação, do worker e do load generator.

Observação: na tela de Setup do Data Streams, o que aparece são os serviços instrumentados que produzem/consomem mensagens, não o broker RabbitMQ como um serviço APM.
Observação: `DD_LOGS_INJECTION` só se aplica aos processos Python instrumentados com `ddtrace-run`. O Apache permanece com logs em texto, com `LogLevel warn`, para evitar forçar um formato JSON parcial ou frágil no `httpd` base da demo.
Observação: `docker compose up` prefixa cada linha com o nome do container. Para ver a linha JSON bruta exatamente como o Datadog ingere, use `docker logs <container>`.

## Testes

```bash
pytest api/tests worker/tests
```

## Notas

- A persistência é em memória; reiniciar o container da API limpa os dados.
- O Apache registra logs em texto e permanece em `warning`.
- O worker faz deduplicação em memória por `event_id` apenas para a execução corrente.
