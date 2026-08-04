# Licenciamento online do Andromeda (servidor + painel web), com fallback local

## Contexto

Hoje o Andromeda (`C:\Users\Icarl\Documents\GitHub\andromeda`) valida a licença **inteiramente offline**: no startup (`src/main.py:38-50`), `check_license()` (em `src/core/system/auxiliars/license_manager_controller.py`) lê `license.json`, verifica a assinatura RSA-PSS/SHA256 com uma chave pública embutida em `src/core/constants.py` (`LICENSE_PUBLIC_KEY`), confere expiração e se o `hardware_id` bate com o hash de um identificador estável da máquina (`get_hardware_id()`).

As licenças são emitidas por este repo (`andromeda-license`), hoje um app desktop PyQt5 (`src/main_controller.py`) que assina com `src/core/security/private_key.pem` (via `src/core/crypto.py`) e grava metadados num SQLite local (`src/core/security/license_users.db`, gerido por `src/core/db.py`).

Objetivo: introduzir um **servidor central** que passa a ser a fonte de verdade para revogação/status de licenças, com um **painel web para admins** gerenciarem (criar, revogar, listar) licenças, publicado via **Docker**. O cliente Andromeda passa a consultar esse servidor no startup, mas **a validação local atual continua existindo como fallback** quando o servidor está inacessível — decisão confirmada com o usuário.

O app desktop PyQt5 atual será **removido**, já que o painel web assume esse papel.

## Arquitetura

### Novo servidor (neste repo, `andromeda-license`)

- **Stack**: FastAPI + SQLAlchemy + PostgreSQL, Jinja2 para o painel web server-rendered (sem build de frontend separado — mais simples de containerizar).
- **Reaproveita**: a lógica de assinatura de `src/core/crypto.py` (mesma chave privada `src/core/security/private_key.pem`, para que licenças novas continuem validando contra o `LICENSE_PUBLIC_KEY` já embutido no cliente — **a chave não pode ser trocada**).
- Estrutura nova:
    ```
    server/
      app/
        main.py            # cria o FastAPI app, monta routers
        config.py          # settings via env (DATABASE_URL, PRIVATE_KEY_PATH, SESSION_SECRET, bootstrap admin)
        database.py        # engine/session SQLAlchemy
        models.py          # License, AdminUser
        schemas.py         # Pydantic (request/response)
        crypto.py           # port de src/core/crypto.py (assinatura)
        security.py         # hashing de senha (passlib/bcrypt) + dependência de sessão
        routers/
          verify.py          # endpoint público: checagem online usada pelo cliente Andromeda
          admin_api.py        # criar/listar/revogar licenças e admins (JSON, usado pelas telas)
          admin_ui.py          # login, dashboard, formulário de nova licença (HTML)
        templates/
          login.html, dashboard.html, new_license.html, admins.html
        static/style.css
      Dockerfile
    docker-compose.yml     # serviço app + serviço postgres
    .env.example
    ```
- **Remove** (substituídos pelo servidor): `src/main.py`, `src/main_controller.py`, `src/gui/**`, `src/core/api.py`, `src/core/db.py`. `src/core/crypto.py` é portado para `server/app/crypto.py` e removido do local antigo. `requirements.txt` passa a listar as deps do servidor (fastapi, uvicorn, sqlalchemy, psycopg2-binary, jinja2, passlib[bcrypt], python-multipart, cryptography).

### Modelo de dados (Postgres)

- `licenses`: id, user_email, hardware_id, license_id (uuid, único), issued_at, expires_at, status (`active`/`revoked`/`expired`), notes, signature, license_json (payload assinado completo, para poder reexportar/baixar), created_by (admin), created_at.
- `admins`: id, username (único), password_hash, created_at. Bootstrap: se a tabela estiver vazia no startup, cria o primeiro admin a partir de `ADMIN_USERNAME`/`ADMIN_PASSWORD` do `.env`; os demais admins são criados pelos próprios admins dentro do painel.

### Endpoints

- `POST /api/v1/licenses/verify` — **público**, chamado pelo cliente Andromeda. Body: `{license_id, hardware_id}`. Resposta: `{"valid": true, "status": "active", "expires": "..."}` ou `{"valid": false, "reason": "revoked" | "not_found" | "expired" | "hardware_mismatch"}`.
- `POST /api/v1/admin/licenses` — cria e assina uma nova licença (email, hardware_id, meses), protegido por sessão.
- `GET /api/v1/admin/licenses` — lista (mesmas colunas da tabela atual do app desktop: email, hardware, emissão, expiração, dias restantes, status).
- `POST /api/v1/admin/licenses/{id}/revoke`, `DELETE /api/v1/admin/licenses/{id}` — protegidos.
- `POST /api/v1/admin/admins` — cria novo admin, protegido (exige login).
- Painel HTML: `/login`, `/dashboard`, `/licenses/new`, `/admins` (gestão de contas admin).

### Docker

- `server/Dockerfile`: `python:3.12-slim`, instala deps, copia `server/app`, roda `uvicorn app.main:app`.
- `docker-compose.yml` na raiz: serviço `app` (build do Dockerfile) + serviço `db` (postgres:16, volume nomeado). A chave privada é montada como **bind mount somente-leitura** (não copiada para dentro da imagem), para não vazar no build.
- **Nota de segurança a levantar com o usuário**: `src/core/security/private_key.pem` parece estar versionado no git deste repo. Vou reusar o arquivo como está (não vou reescrever histórico do git sem pedido explícito), mas recomendo removê-lo do controle de versão e tratá-lo só como secret local/mount — decisão que fica para o usuário confirmar separadamente.

## Cliente Andromeda (`C:\Users\Icarl\Documents\GitHub\andromeda`)

Arquivo principal: `src/core/system/auxiliars/license_manager_controller.py`. `requests` já é dependência do projeto (`pyproject.toml`).

Fluxo confirmado com o usuário para `check_license()`:

1. Validação local de sempre (assinatura + expiração + hardware via `validate_license()`). Se falhar → `False` (sem mudança de comportamento aqui).
2. Se local passou: chama o servidor (`POST /api/v1/licenses/verify` com `license_id` e `hardware_id`), timeout curto (~3s).
    - Erro de rede/timeout/servidor fora do ar → **fallback**: usa o resultado local (`True`).
    - Servidor responde `valid: true` → `True`.
    - Servidor responde `valid: false, reason: revoked/expired/hardware_mismatch` (o servidor _tem_ o registro e diz que não vale) → `False`, mesmo com assinatura local válida.
    - Servidor responde `valid: false, reason: not_found` (licença emitida antes da migração / desconhecida do servidor) → trata como "servidor não tem opinião", cai no fallback local (`True`), para não quebrar licenças já emitidas hoje (ex.: `license_cseabra_prio3.com.br_2026-04-15.json`).
3. Novidades em `constants.py`: `ANDROMEDA_LICENSE_SERVER_URL` (env var, ex. `ANDROMEDA_LICENSE_SERVER_URL`) e `LICENSE_SERVER_TIMEOUT`. Se a URL não estiver configurada, pula direto para o resultado local (sem tentar rede) — mantém o comportamento 100% offline em instalações sem servidor.

Testes existentes em `src/tests/system/test_license_manager_controller.py` serão estendidos com casos: servidor indisponível (fallback), servidor revoga, servidor não conhece a licença (fallback), servidor confirma.

## Migração de dados existentes

`license_users.db` atual não guarda o payload assinado completo (só metadados), então licenças antigas não podem ser totalmente "importadas" para verificação online — elas continuam funcionando via fallback local (comportamento igual ao de hoje) até serem reemitidas pelo painel novo. Vou escrever um script simples (`server/scripts/migrate_sqlite.py`) que importa os metadados existentes (email, hardware, datas, status) para a tabela `licenses` do Postgres só para fins de listagem/histórico no painel, marcando-as sem `signature`/`license_json` (não verificáveis online, mas visíveis e revogáveis administrativamente).

## Verificação

- Subir `docker-compose up` localmente, checar `/docs` (Swagger) do FastAPI.
- Criar o primeiro admin via bootstrap env vars, logar no painel, criar uma licença de teste, baixar o `license.json` gerado e confirmar que o formato bate com o que `validate_license()` do cliente espera (mesmos campos/assinatura).
- Rodar os testes existentes/novos do cliente (`pytest src/tests/system/test_license_manager_controller.py`) cobrindo os 4 cenários de fallback/online.
- Fluxo ponta a ponta manual: gerar `hardware_id` real pelo botão "Generate Token" do cliente, emitir licença pelo painel para esse hardware, importar no cliente e confirmar que libera o app; depois revogar pelo painel e confirmar que o cliente bloqueia no próximo start mesmo com o `license.json` local ainda válido.
