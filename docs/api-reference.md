# REST API Reference

ContractHub provides two API surfaces: a native REST API under `/v1` and a Confluent-compatible Schema Registry API at the root path.

## Native API (`/v1`)

### 1. List Subjects

`GET /v1/subjects`

Returns an array of registered subject names.

```json
[
  "order-events",
  "payments-api"
]
```

### 2. Get Subject Details

`GET /v1/subjects/{subject}`

Returns subject metadata, active compatibility mode, and total versions count.

### 3. Register Schema Version

`POST /v1/subjects/{subject}/versions`

Registers a new schema version. Automatically runs a compatibility check against the latest version unless disabled.

Request body:
```json
{
  "schema": "syntax = \"proto3\";\nmessage Order { string id = 1; }",
  "schemaType": "PROTOBUF"
}
```

Response:
```json
{
  "id": 1,
  "subject": "order-events",
  "version": 1,
  "schemaType": "PROTOBUF",
  "fingerprint": "a8f5c3..."
}
```

### 4. Direct Diff Comparison

`POST /v1/diff`

Computes violations directly between two submitted schema strings without writing to the database.

Request body:
```json
{
  "baseSchema": "syntax = \"proto3\";\nmessage Order { string id = 1; }",
  "candidateSchema": "syntax = \"proto3\";\nmessage Order { int32 id = 1; }",
  "schemaType": "PROTOBUF",
  "mode": "FULL"
}
```

Response:
```json
{
  "isCompatible": false,
  "mode": "FULL",
  "violations": [
    {
      "code": "PROTO_TYPE_CHANGED",
      "severity": "BREAKING",
      "path": "Order.id",
      "message": "Field 'id' changed type from 'string' to 'int32'"
    }
  ]
}
```

---

## Confluent Compatibility Layer

ContractHub implements the endpoints expected by Confluent Schema Registry client libraries.

### Supported Endpoints

- `GET /subjects`: List subject names.
- `GET /subjects/{subject}/versions`: List version numbers for a subject.
- `GET /subjects/{subject}/versions/{version}`: Fetch a specific version or `latest`.
- `POST /subjects/{subject}/versions`: Register a schema in Confluent JSON format `{"schema": "...", "schemaType": "PROTOBUF"}`. Returns `{"id": <int>}`.
- `GET /schemas/ids/{id}`: Fetch schema definition by its global unique identifier.
- `POST /compatibility/subjects/{subject}/versions/{version}`: Dry run compatibility test. Returns `{"is_compatible": true|false}`.
