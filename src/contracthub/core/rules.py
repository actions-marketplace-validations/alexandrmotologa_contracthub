"""Rule definitions and error codes for breaking change detection."""

# Protocol Buffers Rules
PROTO_FIELD_REMOVED = "PROTO_FIELD_REMOVED"
PROTO_TAG_MUTATED = "PROTO_TAG_MUTATED"
PROTO_TYPE_CHANGED = "PROTO_TYPE_CHANGED"
PROTO_TAG_COLLISION = "PROTO_TAG_COLLISION"
PROTO_ENUM_VALUE_REMOVED = "PROTO_ENUM_VALUE_REMOVED"
PROTO_ENUM_NUM_MUTATED = "PROTO_ENUM_NUM_MUTATED"
PROTO_MESSAGE_REMOVED = "PROTO_MESSAGE_REMOVED"
PROTO_CARDINALITY_CHANGED = "PROTO_CARDINALITY_CHANGED"

# OpenAPI Rules
REST_ENDPOINT_REMOVED = "REST_ENDPOINT_REMOVED"
REST_METHOD_REMOVED = "REST_METHOD_REMOVED"
REST_REQUIRED_PARAM_ADDED = "REST_REQUIRED_PARAM_ADDED"
REST_PARAM_TYPE_MUTATED = "REST_PARAM_TYPE_MUTATED"
REST_REQUIRED_BODY_ADDED = "REST_REQUIRED_BODY_ADDED"
REST_STATUS_MUTATED = "REST_STATUS_MUTATED"
REST_RESPONSE_SCHEMA_REMOVED = "REST_RESPONSE_SCHEMA_REMOVED"

# JSON Schema Rules
JSON_SCHEMA_REQUIRED_ADDED = "JSON_SCHEMA_REQUIRED_ADDED"
JSON_SCHEMA_TYPE_NARROWED = "JSON_SCHEMA_TYPE_NARROWED"
JSON_SCHEMA_PROPERTY_REMOVED = "JSON_SCHEMA_PROPERTY_REMOVED"
JSON_SCHEMA_ADDITIONAL_PROPERTIES_FALSE = "JSON_SCHEMA_ADDITIONAL_PROPERTIES_FALSE"

# Apache Avro Rules
AVRO_FIELD_REMOVED_NO_DEFAULT = "AVRO_FIELD_REMOVED_NO_DEFAULT"
AVRO_FIELD_ADDED_NO_DEFAULT = "AVRO_FIELD_ADDED_NO_DEFAULT"
AVRO_TYPE_MUTATED = "AVRO_TYPE_MUTATED"


RULE_DESCRIPTIONS = {
    PROTO_FIELD_REMOVED: "Field was removed without declaring its tag as reserved",
    PROTO_TAG_MUTATED: "Existing field numeric tag was changed",
    PROTO_TYPE_CHANGED: "Field data type was modified incompatibly",
    PROTO_TAG_COLLISION: "Field assigned a tag number that is reserved or in conflict",
    PROTO_ENUM_VALUE_REMOVED: "Enum option was removed",
    PROTO_ENUM_NUM_MUTATED: "Enum value numeric assignment was modified",
    PROTO_MESSAGE_REMOVED: "Existing message was removed",
    PROTO_CARDINALITY_CHANGED: "Field cardinality was modified (e.g. repeated to singular)",
    REST_ENDPOINT_REMOVED: "HTTP path endpoint was removed",
    REST_METHOD_REMOVED: "HTTP method was removed from endpoint",
    REST_REQUIRED_PARAM_ADDED: "New required parameter was added to request",
    REST_PARAM_TYPE_MUTATED: "Parameter data type was changed incompatibly",
    REST_REQUIRED_BODY_ADDED: "Request body was made required or new required body field added",
    REST_STATUS_MUTATED: "HTTP response status code was removed or altered",
    REST_RESPONSE_SCHEMA_REMOVED: "Response schema definition was removed",
    JSON_SCHEMA_REQUIRED_ADDED: "New required property was added to JSON schema",
    JSON_SCHEMA_TYPE_NARROWED: "Allowed type spectrum was narrowed",
    JSON_SCHEMA_PROPERTY_REMOVED: "Property was removed from schema with additionalProperties: false",
    JSON_SCHEMA_ADDITIONAL_PROPERTIES_FALSE: "Schema restricted additionalProperties to false",
}
