# ContractHub

ContractHub is a schema registry and breaking change linter for Protocol Buffers (Proto3), OpenAPI 3.x, and JSON Schema. It helps teams maintain data compatibility across event streams and HTTP services by analyzing schema syntax trees, checking semantic rules, and blocking incompatible pull requests in CI pipelines.

ContractHub also exposes a wire-compatible API for Confluent Schema Registry clients, so Kafka producers and consumers can register and fetch schemas without code changes.

## Features

- AST-level compatibility checks for Proto3, OpenAPI 3.x, and JSON Schema.
- Three compatibility modes: BACKWARD, FORWARD, and FULL.
- CLI tool (`contracthub diff`, `contracthub check`) designed for developer terminals and CI runners.
- Confluent Schema Registry wire-compatible HTTP endpoints (`/subjects`, `/schemas/ids/{id}`, `/compatibility/subjects/{subject}/versions/{version}`).
- Built-in Web Studio (`/studio`) to inspect schemas and test candidate changes in the browser.
- Standalone GitHub Action (`alexandrmotologa/contracthub@v1`) to guard repositories against breaking contract edits.
- Local SQLite storage by default, with support for PostgreSQL.

## Compatibility Rules

### Protocol Buffers (Proto3)

| Rule | Severity | Condition |
| :--- | :--- | :--- |
| `PROTO_FIELD_REMOVED` | BREAKING | Field deleted without marking its tag as `reserved` |
| `PROTO_TAG_MUTATED` | BREAKING | Existing field assigned a different numeric tag |
| `PROTO_TYPE_CHANGED` | BREAKING | Field data type changed (for example, `string` to `int32`) |
| `PROTO_TAG_COLLISION` | BREAKING | Field uses a tag number previously marked as reserved |
| `PROTO_ENUM_VALUE_REMOVED` | BREAKING | Enum value name or number deleted |
| `PROTO_MESSAGE_REMOVED` | BREAKING | Top-level or nested message removed |

### OpenAPI 3.x

| Rule | Severity | Condition |
| :--- | :--- | :--- |
| `REST_ENDPOINT_REMOVED` | BREAKING | URL path removed from the specification |
| `REST_METHOD_REMOVED` | BREAKING | HTTP method removed from an existing path |
| `REST_REQUIRED_PARAM_ADDED` | BREAKING | New required query, header, or path parameter introduced |
| `REST_REQUIRED_BODY_ADDED` | BREAKING | Request body made required or new required property added |
| `REST_STATUS_MUTATED` | BREAKING | Expected response status code altered or removed |
| `REST_RESPONSE_TYPE_MUTATED` | BREAKING | Response property type changed incompatibly |

### JSON Schema

| Rule | Severity | Condition |
| :--- | :--- | :--- |
| `JSON_SCHEMA_REQUIRED_ADDED` | BREAKING | New field added to `required` array in candidate schema |
| `JSON_SCHEMA_TYPE_NARROWED` | BREAKING | Allowed type set reduced (for example, `["string", "null"]` to `string`) |
| `JSON_SCHEMA_PROPERTY_REMOVED` | BREAKING | Property removed when `additionalProperties: false` is configured |

## Installation

Using `uv`:

```bash
uv pip install contracthub
```

Or using standard `pip`:

```bash
pip install contracthub
```

For local development:

```bash
git clone https://github.com/alexandrmotologa/contracthub.git
cd contracthub
uv sync
```

## Quick Start

### 1. Diff two local schemas

Compare two files directly to verify whether an update is safe:

```bash
# Compare two Proto files
contracthub diff examples/order_v1.proto examples/order_v2_compatible.proto

# Check with strict FULL compatibility
contracthub diff examples/order_v1.proto examples/order_v2_breaking.proto --mode FULL
```

The command returns exit code `0` if compatible, or exit code `1` if breaking changes exist.

### 2. Run the Registry Server & Web Studio

Start the local registry server:

```bash
contracthub serve --port 8000
```

Access the interactive interfaces:
- Web Diff Studio: `http://localhost:8000/studio`
- OpenAPI Documentation: `http://localhost:8000/docs`

### 3. Check against a registered subject

Validate a working file against the latest version stored in your registry:

```bash
contracthub check --subject order-events --file schemas/order.proto --url http://localhost:8000
```

### 4. Register a new schema version

Register an approved schema into the registry:

```bash
contracthub register --subject order-events --file schemas/order.proto --url http://localhost:8000
```

## GitHub Action Usage

Add ContractHub to your pull request workflow (`.github/workflows/contract-lint.yml`):

```yaml
name: Schema Lint

on:
  pull_request:
    paths:
      - 'proto/**'
      - 'openapi/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: alexandrmotologa/contracthub@v1
        with:
          file: 'proto/order.proto'
          base-ref: 'origin/main'
          mode: 'BACKWARD'
```

## Confluent Schema Registry Compatibility

ContractHub implements the Confluent wire protocol. Existing Kafka clients can point directly to ContractHub:

```python
from confluent_kafka.schema_registry import SchemaRegistryClient

client = SchemaRegistryClient({"url": "http://localhost:8000"})
latest_version = client.get_latest_version("order-events")
print(f"Version: {latest_version.version}, Schema ID: {latest_version.schema_id}")
```

Supported Confluent endpoints:
- `GET /subjects`
- `GET /subjects/{subject}/versions`
- `GET /subjects/{subject}/versions/{version}`
- `POST /subjects/{subject}/versions`
- `GET /schemas/ids/{id}`
- `POST /compatibility/subjects/{subject}/versions/{version}`

## Documentation

Detailed guides are available in the `docs/` directory:
- [Architecture & Design](docs/architecture.md)
- [Compatibility Modes & Rules](docs/compatibility-rules.md)
- [CLI Reference](docs/cli-reference.md)
- [REST API Reference](docs/api-reference.md)

## License

MIT License. See [LICENSE](LICENSE) for details.
