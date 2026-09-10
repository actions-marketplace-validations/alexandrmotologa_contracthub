# CLI Reference

The `contracthub` command line interface provides commands for schema comparison, registry interactions, and local development.

## Syntax

```bash
contracthub [COMMAND] [OPTIONS]
```

## Global Options

- `--help`: Display available commands and options.
- `--version`: Display current version.

## Commands

### `contracthub diff`

Compares two local schema files and outputs structured AST violations.

```bash
contracthub diff <BASE_FILE> <CANDIDATE_FILE> [OPTIONS]
```

#### Options:
- `--mode, -m`: Compatibility mode (`BACKWARD`, `FORWARD`, `FULL`). Defaults to `FULL`.
- `--format, -f`: Output format (`table`, `json`). Defaults to `table`.
- `--strict / --no-strict`: When true, warnings are treated as errors. Defaults to `false`.

#### Exit codes:
- `0`: Schemas are compatible according to the selected mode.
- `1`: Incompatible breaking changes were detected.
- `2`: Syntax or parse error in one of the schema files.

#### Example:
```bash
contracthub diff schemas/user_v1.proto schemas/user_v2.proto --mode BACKWARD
```

---

### `contracthub check`

Checks a candidate schema against the latest version stored in a remote ContractHub registry.

```bash
contracthub check --subject <SUBJECT> --file <FILE> [OPTIONS]
```

#### Options:
- `--subject, -s`: Name of the schema subject in the registry (required).
- `--file, -f`: Path to the candidate schema file (required).
- `--url, -u`: Registry base URL. Defaults to `http://localhost:8000` or the `CONTRACTHUB_URL` environment variable.
- `--mode, -m`: Compatibility mode override. If omitted, uses the subject setting from the registry.

#### Example:
```bash
contracthub check --subject payment-events --file proto/payment.proto --url https://registry.internal
```

---

### `contracthub register`

Registers a new schema version under a designated subject. Validates compatibility before committing unless forced.

```bash
contracthub register --subject <SUBJECT> --file <FILE> [OPTIONS]
```

#### Options:
- `--subject, -s`: Target subject name (required).
- `--file, -f`: Path to schema file to register (required).
- `--url, -u`: Registry base URL. Defaults to `http://localhost:8000`.
- `--force`: Bypass compatibility check (not recommended for production).

#### Example:
```bash
contracthub register --subject order-events --file proto/order.proto
```

---

### `contracthub serve`

Starts the HTTP registry server, API documentation, and Web Studio.

```bash
contracthub serve [OPTIONS]
```

#### Options:
- `--host`: Bind host address. Defaults to `127.0.0.1`.
- `--port, -p`: Bind port. Defaults to `8000`.
- `--reload`: Enable auto-reload for local development.
- `--db`: SQLite database path or PostgreSQL connection URL.
