"""Unit tests for multi-protocol CodeGenerator (TypeScript & Pydantic v2)."""

from pathlib import Path

import pytest

from contracthub.core.codegen import CodeGenerator, TargetLanguage


def test_proto_codegen_typescript():
    proto_file = Path("examples/order_v1.proto")
    content = proto_file.read_text(encoding="utf-8")

    ts_code = CodeGenerator.generate(content, target=TargetLanguage.TYPESCRIPT)
    assert "export enum OrderStatus {" in ts_code
    assert "ORDER_STATUS_PENDING = 1," in ts_code
    assert "export interface OrderItem {" in ts_code
    assert "item_id: string;" in ts_code
    assert "quantity: number;" in ts_code
    assert "price: number;" in ts_code
    assert "export interface OrderEvent {" in ts_code
    assert "items: OrderItem[];" in ts_code


def test_proto_codegen_pydantic():
    proto_file = Path("examples/order_v1.proto")
    content = proto_file.read_text(encoding="utf-8")

    py_code = CodeGenerator.generate(content, target="pydantic")
    assert "class OrderStatus(IntEnum):" in py_code
    assert "ORDER_STATUS_PENDING = 1" in py_code
    assert "class OrderItem(BaseModel):" in py_code
    assert "item_id: str" in py_code
    assert "price: float" in py_code
    assert "class OrderEvent(BaseModel):" in py_code
    assert "items: list[OrderItem] = Field(default_factory=list)" in py_code


def test_avro_codegen_typescript_and_pydantic():
    avsc_file = Path("examples/order_v1.avsc")
    content = avsc_file.read_text(encoding="utf-8")

    ts_code = CodeGenerator.generate(content, target="ts")
    assert "export interface OrderEvent {" in ts_code
    assert "order_id: string;" in ts_code
    assert "total_amount: number;" in ts_code

    py_code = CodeGenerator.generate(content, target="pydantic")
    assert "class OrderEvent(BaseModel):" in py_code
    assert "order_id: str" in py_code
    assert "total_amount: float" in py_code


def test_json_schema_codegen_typescript_and_pydantic():
    json_file = Path("examples/customer_v1.json")
    content = json_file.read_text(encoding="utf-8")

    ts_code = CodeGenerator.generate(content, target="typescript")
    assert "export interface Customer {" in ts_code
    assert "id: string;" in ts_code
    assert "email: string;" in ts_code
    assert "age?: number;" in ts_code

    py_code = CodeGenerator.generate(content, target="python")
    assert "class Customer(BaseModel):" in py_code
    assert "id: str" in py_code
    assert "email: str" in py_code
    assert "age: int | None = Field(default=None)" in py_code


def test_openapi_codegen_typescript_and_pydantic():
    openapi_file = Path("examples/petstore_v1.json")
    content = openapi_file.read_text(encoding="utf-8")

    ts_code = CodeGenerator.generate(content, target="typescript")
    assert "export interface Pet {" in ts_code
    assert "export interface NewPet {" in ts_code
    assert "name: string;" in ts_code
    assert "tag?: string;" in ts_code

    py_code = CodeGenerator.generate(content, target="pydantic")
    assert "class Pet(BaseModel):" in py_code
    assert "class NewPet(BaseModel):" in py_code
    assert "name: str" in py_code


def test_codegen_invalid_target():
    proto_file = Path("examples/order_v1.proto")
    content = proto_file.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported target language 'rust'"):
        CodeGenerator.generate(content, target="rust")
