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

---

### `contracthub scan`

Scans a git repository for modified schema files against a base git reference, comparing each file AST.

```bash
contracthub scan [OPTIONS]
```

#### Options:
- `--repo-path, -r`: Path to git repository root. Defaults to `.`.
- `--base-ref, -b`: Base git reference or commit to compare against. Defaults to `origin/main`.
- `--mode, -m`: Compatibility mode (`BACKWARD`, `FORWARD`, `FULL`). Defaults to `FULL`.
- `--format, -f`: Output format (`table`, `json`). Defaults to `table`.
- `--github-summary`: Path to write GitHub Actions Step Summary markdown.
- `--strict / --no-strict`: Treat warnings as breaking errors. Defaults to `false`.

#### Example:
```bash
contracthub scan --base-ref origin/main --mode BACKWARD --github-summary $GITHUB_STEP_SUMMARY
```

---

### `contracthub fix`

Analyzes breaking changes between two schema files and automatically applies safe remediations (for instance, declaring removed tags and names as `reserved` in Protobuf).

```bash
contracthub fix --base <BASE_FILE> --candidate <CANDIDATE_FILE> [OPTIONS]
```

#### Options:
- `--base, -b`: Path to base schema file (required).
- `--candidate, -c`: Path to candidate schema file (required).
- `--write, -w`: Write remediated contents directly to the candidate file.
- `--output, -o`: Output path for remediated schema file.

#### Example:
```bash
# Preview remediation in terminal
contracthub fix --base proto/order_v1.proto --candidate proto/order_v2.proto

# Apply fixes directly
contracthub fix --base proto/order_v1.proto --candidate proto/order_v2.proto --write
```

---

### `contracthub mock`

Generates synthetic, deterministic mock JSON payloads according to schema definitions. Supports Proto3, Apache Avro, OpenAPI, JSON Schema, and GraphQL SDL.

```bash
contracthub mock --file <FILE> [OPTIONS]
```

#### Options:
- `--file, -f`: Path to schema file (required).
- `--message, -m`: Message, record, or GraphQL type name for files containing multiple schemas.
- `--output, -o`: Output path to write generated JSON payload.

#### Example:
```bash
contracthub mock --file proto/payment.proto --message PaymentRequest --output mock_payment.json
```

---

### `contracthub semver`

Recommends automated Semantic Versioning (`MAJOR`, `MINOR`, or `PATCH`) by comparing the AST changes between two schemas.

```bash
contracthub semver <BASE_FILE> <CANDIDATE_FILE> [OPTIONS]
```

#### Options:
- `--current-version, -c`: Current version string (e.g. `1.2.0`). Defaults to `1.0.0`.
- `--mode, -m`: Compatibility mode (`BACKWARD`, `FORWARD`, `FULL`). Defaults to `FULL`.
- `--format, -f`: Output format (`table`, `json`). Defaults to `table`.

#### Example:
```bash
contracthub semver schemas/user_v1.proto schemas/user_v2.proto --current-version 2.1.0
```

---

### `contracthub validate`

Validates a real JSON data payload against any schema (JSON Schema, OpenAPI component, Protobuf message, Avro record, or GraphQL type).

```bash
contracthub validate --file <FILE> --payload <PAYLOAD> [OPTIONS]
```

#### Options:
- `--file, -f`: Path to schema file (required).
- `--payload, -p`: Path to JSON payload file, or raw JSON string (required).
- `--entity, -e`: Optional target entity name (e.g. OpenAPI model or Proto message).
- `--format, -f`: Output format (`table`, `json`). Defaults to `table`.

#### Exit codes:
- `0`: Payload is strictly valid according to the schema.
- `1`: Validation errors were detected.
- `2`: Schema or payload parsing error.

#### Example:
```bash
contracthub validate --file proto/user.proto --entity User --payload payload.json
```

---

### `contracthub codegen`

Generates typed client data models (TypeScript interfaces or Python Pydantic v2 models) directly from contract schemas (Proto3, Apache Avro, JSON Schema, or OpenAPI 3.x).

```bash
contracthub codegen --file <FILE> [OPTIONS]
```

#### Options:
- `--file, -f`: Path to schema file (required).
- `--target, -t`: Target language or framework (`typescript` or `pydantic`). Defaults to `typescript`.
- `--output, -o`: Output file path. If omitted, outputs code to standard output.

#### Example:
```bash
# Generate TypeScript interfaces to stdout
contracthub codegen --file proto/order.proto --target typescript

# Generate Pydantic v2 classes to a file
contracthub codegen --file avro/customer.avsc --target pydantic --output models.py
```


