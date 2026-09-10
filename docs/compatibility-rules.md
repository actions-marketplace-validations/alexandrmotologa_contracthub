# Compatibility Rules and Semantic Invariants

ContractHub guarantees schema evolution safety by formalizing breaking change rules across data serialization and API specifications.

## Compatibility Modes

| Mode | Producer ($V_1$) -> Consumer ($V_2$) | Producer ($V_2$) -> Consumer ($V_1$) | Primary Use Case |
| :--- | :--- | :--- | :--- |
| `BACKWARD` | Allowed | Not guaranteed | Upgrade consumers first, then producers |
| `FORWARD` | Not guaranteed | Allowed | Upgrade producers first, then consumers |
| `FULL` | Allowed | Allowed | Producers and consumers can be upgraded in any order |

## Protocol Buffers (Proto3) Specification

In Protocol Buffers, binary encoding relies on numeric tags, wire types, and field offsets rather than field names.

### Breaking Rules

1. `PROTO_FIELD_REMOVED`:
   - Deleting a field without declaring its tag in a `reserved` statement can cause binary data corruption if that tag is reassigned in the future.
   - Fix: Keep the field or add `reserved <tag>;` and `reserved "<name>";`.

2. `PROTO_TAG_MUTATED`:
   - Changing the numeric tag of a field alters its binary key on the wire.
   - Example: changing `string id = 1;` to `string id = 2;`.

3. `PROTO_TYPE_CHANGED`:
   - Changing a field type (e.g. `string` to `int32` or `int32` to `int64`) causes deserialization errors unless types have wire-compatible encodings (such as `int32`, `uint32`, `int64` with varint representations under specific constraints). In ContractHub, scalar type changes between incompatible categories are rejected.

4. `PROTO_TAG_COLLISION`:
   - Introducing a new field using a tag that was previously declared as `reserved`.

5. `PROTO_ENUM_VALUE_REMOVED`:
   - Removing an enum option breaks consumers receiving that integer representation.

6. `PROTO_MESSAGE_REMOVED`:
   - Deleting a message referenced by other messages or by client services.

## OpenAPI 3.x Specification

For HTTP REST endpoints, breaking changes occur when request validation tightens or response guarantees loosen.

### Breaking Rules

1. `REST_ENDPOINT_REMOVED`:
   - A path present in the base schema is missing in the candidate schema. Existing clients calling this URI will receive 404 responses.

2. `REST_METHOD_REMOVED`:
   - An HTTP operation (GET, POST, PUT, DELETE, PATCH) defined on a path was deleted. Existing callers will receive 405 Method Not Allowed.

3. `REST_REQUIRED_PARAM_ADDED`:
   - Adding a query, path, or header parameter marked as `required: true`. Existing clients will fail request validation.

4. `REST_REQUIRED_BODY_ADDED`:
   - Changing `requestBody.required` from `false` to `true`, or adding a new required field to an existing request body schema.

5. `REST_STATUS_MUTATED`:
   - Removing a declared HTTP success status (e.g. 200 OK or 201 Created), or replacing a success status with a different response structure.

6. `REST_RESPONSE_TYPE_MUTATED`:
   - Changing property types in response schemas in a way that breaks client deserializers.

## JSON Schema Specification

JSON Schema rules govern document payloads used across webhook payloads and NoSQL structures.

### Breaking Rules

1. `JSON_SCHEMA_REQUIRED_ADDED`:
   - Adding a field to the `required` array breaks existing payloads that do not contain that field.

2. `JSON_SCHEMA_TYPE_NARROWED`:
   - Reducing the allowable types (for example, allowing only `integer` when previously `number` was permitted).

3. `JSON_SCHEMA_PROPERTY_REMOVED`:
   - Removing a defined property from a schema with `additionalProperties: false`.
