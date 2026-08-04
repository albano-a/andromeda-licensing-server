# andromeda-license
A license generator app for Andromeda software

## Coolify

### PostgreSQL

Create a PostgreSQL service and fill the fields like this:

- `Username`: `andromeda`
- `Password`: use one password and keep it for the app env too
- `Initial database`: `andromeda_license`

### App

Set these environment variables in the app service:

```env
DATABASE_URL=postgresql+psycopg2://andromeda:SUA_SENHA@SEU_HOST:5432/andromeda_license
POSTGRES_ADMIN_URL=postgresql+psycopg2://postgres:SENHA_ADMIN@SEU_HOST:5432/postgres
CREATE_DATABASE_ON_STARTUP=true
SESSION_SECRET=uma-string-longa-e-aleatoria
ADMIN_USERNAME=admin
ADMIN_PASSWORD=uma-senha-forte
```

If you can mount a secret file, set:

```env
PRIVATE_KEY_PATH=/run/secrets/private_key.pem
```

If Coolify makes file mounting awkward, use the base64 option instead:

```env
PRIVATE_KEY_B64=base64-do-arquivo-pem
```

### Criar o database uma vez

The app now tries to create the database automatically on startup. For that to work, provide `POSTGRES_ADMIN_URL` with a privileged PostgreSQL connection and keep `CREATE_DATABASE_ON_STARTUP=true`.

If you want to do it manually instead, run this once inside the app container:

```bash
python scripts/create_database.py
```

Use `POSTGRES_MAINTENANCE_DB=postgres` if you need to connect through the default maintenance database.

### Observação

If Coolify shows `database andromeda does not exist`, the `Initial database` value and the database name in `DATABASE_URL` do not match. The app does not create the PostgreSQL database itself; it only creates tables after connecting.
