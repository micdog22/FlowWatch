# FlowWatch - Monitor de Erros do n8n (FastAPI + SQLite)

FlowWatch é um serviço leve para receber webhooks de erro do n8n, registrar ocorrências em banco local (SQLite) e exibir um painel simples para investigação e resolução. Ideal para quem usa n8n self‑hosted e quer rastrear exceções, tempos, tentativas e payloads problemáticos.

## Visão Geral

- **Entrada**: endpoint HTTP que aceita webhooks do n8n (por exemplo, a partir do nó “HTTP Request” dentro do fluxo de erro).
- **Persistência**: SQLite com SQLAlchemy.
- **API**: FastAPI com OpenAPI/Swagger.
- **Painel**: interface HTML simples para listar, filtrar e marcar ocorrências como resolvidas.
- **Segurança**: token via `FLOWWATCH_TOKEN` para proteção de escrita via webhook.
- **Deploy**: roda com Uvicorn ou Docker.

> Observação: O projeto não depende do n8n diretamente. Ele apenas define um formato comum para receber dados oriundos de um fluxo de erro do n8n. Você pode adaptar a estrutura do JSON conforme sua necessidade.

---

## Como funciona o webhook do n8n

1. No n8n, crie um **Fluxo de Erros** (ou use o nó *Error Trigger* ou um branch de *Catch*).
2. Adicione um nó **HTTP Request** configurado como **POST** para a URL do FlowWatch:  
   `http://SEU_HOST:8000/webhooks/n8n?token=SEU_TOKEN`
3. No corpo (JSON), envie as informações do erro. Exemplo de body sugerido:

```json
{
  "workflow_id": "{{ $json.workflow.id }}",
  "workflow_name": "{{ $json.workflow.name }}",
  "node": "{{ $json.node.type }}",
  "error_message": "{{ $json.error.message }}",
  "error_stack": "{{ $json.error.stack }}",
  "run_id": "{{ $json.execution.id }}",
  "attempt": "{{ $json.execution.retryOf || 0 }}",
  "payload": {{$json.payload}}
}
```

> Você pode montar esse JSON manualmente usando expressões do n8n. O importante é enviar ao menos `error_message` e `workflow_name`.

---

## Estrutura do Projeto

```
FlowWatch/
├─ app/
│  ├─ main.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ templates/
│  │  └─ index.html
│  └─ static/
│     └─ styles.css
├─ .env.example
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ LICENSE
└─ README.md
```

---

## Instalação (sem Docker)

Pré‑requisitos:
- Python 3.11+
- pip

Passos:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edite .env e defina FLOWWATCH_TOKEN como um valor secreto
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- Painel: `http://localhost:8000/`
- Documentação da API: `http://localhost:8000/docs`

---

## Uso com Docker

```bash
docker build -t flowwatch:latest .
docker run --env-file .env -p 8000:8000 flowwatch:latest
```

Ou com `docker-compose`:

```bash
docker compose up --build
```

---

## Configuração do n8n

1. Crie um fluxo de *error handling* ou um *Error Trigger*.
2. Adicione um nó **HTTP Request**:
   - Método: `POST`
   - URL: `http://SEU_HOST:8000/webhooks/n8n?token=SEU_TOKEN`
   - Headers: `Content-Type: application/json`
   - Body: RAW / JSON com o conteúdo sugerido acima.
3. Publique/execute para que, sempre que ocorrer um erro, o n8n envie os dados ao FlowWatch.

---

## Rotas Principais

- `GET /` — Painel HTML com listagem e filtros.
- `POST /webhooks/n8n?token=...` — Recebe eventos. Requer token.
- `POST /resolve/{id}` — Marca um evento como resolvido.
- `GET /api/events` — Lista eventos em JSON (paginado, filtros).
- `GET /health` — Status do serviço.

Veja os parâmetros no Swagger em `GET /docs`.

---

## Variáveis de Ambiente

- `FLOWWATCH_TOKEN` (obrigatório para escrever via webhook).
- `DATABASE_URL` (opcional; padrão: `sqlite:///./flowwatch.db`).
- `APP_TITLE` (opcional; padrão: `FlowWatch`).
- `APP_HOST` e `APP_PORT` (usadas no Dockerfile/compose).

Use `.env.example` como base.

---

## Esquema de Dados (resumo)

- `Event`:
  - `id` (int, PK)
  - `created_at` (datetime)
  - `workflow_id` (str)
  - `workflow_name` (str, index)
  - `node` (str)
  - `error_message` (text, index)
  - `error_stack` (text)
  - `run_id` (str)
  - `attempt` (int)
  - `payload` (json, opcional)
  - `resolved` (bool, default False)
  - `resolved_at` (datetime, opcional)

---

## Licença

MIT — veja o arquivo `LICENSE`.

---

## Roadmap Sugerido

- Autenticação para painel (Basic Auth).
- Exportação CSV/JSON dos eventos.
- Integração com e-mail/Telegram para alertas.
- Análises (agregações por workflow, últimas 24h etc.).

---

## Suporte

Abra uma issue no repositório ou adapte livremente ao seu uso.
