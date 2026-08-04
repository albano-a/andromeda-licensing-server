# andromeda-license
A license generator app for Andromeda software

## Coolify

If you deploy this app on Coolify, make sure the PostgreSQL database name in `DATABASE_URL` already exists. The app does not create it automatically.

For the private key, you have two options:

1. Mount a persistent volume at `/run/secrets` and store the file as `private_key.pem`.
2. Set `PRIVATE_KEY_B64` with the base64-encoded PEM contents and skip persistent storage entirely.

If Coolify is showing `database andromeda does not exist`, the database name in the connection string does not match the actual database created in the Postgres service. Update `DATABASE_URL` to the real database name or create a database with that name first.
