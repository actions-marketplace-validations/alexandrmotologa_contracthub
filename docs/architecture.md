# Architecture and Design

ContractHub operates as both a local command line linter and a centralized schema registry service.

## High Level Overview

```
                          ┌───────────────────────┐
                          │  Developer Terminal   │
                          │   or CI/CD Pipeline   │
                          └──────────┬────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 │                                       │
                 ▼                                       ▼
        contracthub diff                        contracthub check
       (Local AST Engine)                    (Remote Registry Client)
                 │                                       │
                 │                                       ▼
                 │                          ┌─────────────────────────┐
                 │                          │  ContractHub REST API   │
                 │                          │   (FastAPI + Uvicorn)   │
                 │                          └────────────┬────────────┘
                 ▼                                       │
      ┌──────────────────────┐                           ▼
      │  AST Parsers Layer   │               ┌───────────────────────┐
      │ - Proto3 Parser      │               │   Relational Storage  │
      │ - OpenAPI 3.x Parser │               │  (SQLite/PostgreSQL)  │
      │ - JSON Schema Parser │               └───────────────────────┘
      └──────────┬───────────┘
                 │
                 ▼
      ┌──────────────────────┐
      │ Compatibility Engine │
      │ - BACKWARD           │
      │ - FORWARD            │
      │ - FULL               │
      └──────────────────────┘
```

## Component Breakdown

### 1. Abstract Syntax Tree (AST) Parsers

ContractHub does not rely on heavy external compilers like `protoc` at runtime. Instead, it uses specialized in-process parsers that extract the structural semantics of schema documents:

- **Proto3 Parser (`parsers/proto_parser.py`)**: Tokenizes `.proto` files into messages, enums, fields, tag numbers, types, cardinality, and reserved declarations. It accounts for comments, nested types, and package declarations.
- **OpenAPI 3.x Parser (`parsers/openapi_parser.py`)**: Validates and normalizes paths, operations, query/header parameters, request body schemas, and response definitions.
- **JSON Schema Parser (`parsers/json_schema_parser.py`)**: Traverses schema properties, required arrays, type constraints, and composition keywords (`anyOf`, `allOf`, `oneOf`).

### 2. Compatibility Engine

The engine takes two parsed schema structures (a base schema $V_1$ and a candidate schema $V_2$) and applies a rule matrix based on the requested mode:

- **BACKWARD**: Consumers running the new schema ($V_2$) can read data produced by producers running the old schema ($V_1$). Example: adding an optional field is allowed.
- **FORWARD**: Consumers running the old schema ($V_1$) can read data produced by producers running the new schema ($V_2$). Example: deleting an optional field is allowed only if consumers ignore unknown fields or if the field was marked reserved.
- **FULL**: Satisfies both BACKWARD and FORWARD rules simultaneously. Any change that breaks either direction is rejected.

### 3. Registry and Wire Protocol Layer

The registry server provides two API interfaces:

- **Native REST API (`api/native_routes.py`)**: Idiomatic JSON endpoints for subject registration, version retrieval, and diff generation.
- **Confluent Wire Protocol (`api/confluent_routes.py`)**: Compatibility layer implementing Confluent Schema Registry HTTP specifications. Kafka serialization libraries interact with ContractHub without modifications.

### 4. Storage Subsystem

Schema metadata is persisted through SQLAlchemy models:

- `Subject`: Represents a distinct contract namespace (e.g. `order-events-value`, `payments-service-api`).
- `SchemaVersion`: An immutable record holding the version number, raw schema content, schema format, fingerprint hash, and creation timestamp.
- `CompatibilityConfig`: Per-subject or global policy overrides.
