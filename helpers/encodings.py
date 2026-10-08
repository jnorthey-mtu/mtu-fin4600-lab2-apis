"""Encode one quote in several wire formats to compare size and readability."""
from __future__ import annotations

import io
import json
from xml.sax.saxutils import escape

SAMPLE_QUOTE = {  # illustrative values only
    "symbol": "F", "currency": "USD", "price": 11.87,
    "volume": 58234117, "time_unix": 1790107200,
}

AVRO_SCHEMA = {
    "type": "record", "name": "Quote", "namespace": "edu.mtu.fin4600",
    "fields": [
        {"name": "symbol", "type": "string"},
        {"name": "currency", "type": "string"},
        {"name": "price", "type": "double"},
        {"name": "volume", "type": "long"},
        {"name": "time_unix", "type": "long"},
    ],
}

PROTO_TEXT = """syntax = "proto3";
package fin4600;

message Quote {
  string symbol    = 1;
  string currency  = 2;
  double price     = 3;
  int64  volume    = 4;
  int64  time_unix = 5;
}"""


def to_json(q: dict) -> bytes:
    return json.dumps(q, separators=(",", ":")).encode()


def to_xml(q: dict) -> bytes:
    body = "".join(f"<{k}>{escape(str(v))}</{k}>" for k, v in q.items() if k != "symbol")
    return f'<Quote symbol="{escape(q["symbol"])}">{body}</Quote>'.encode()


def quote_message_class():
    """Build the protobuf Quote class at runtime (no protoc compiler needed)."""
    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

    F = descriptor_pb2.FieldDescriptorProto
    fdp = descriptor_pb2.FileDescriptorProto(name="quote.proto", package="fin4600", syntax="proto3")
    msg = fdp.message_type.add(name="Quote")
    for number, (name, ftype) in enumerate([
            ("symbol", F.TYPE_STRING), ("currency", F.TYPE_STRING), ("price", F.TYPE_DOUBLE),
            ("volume", F.TYPE_INT64), ("time_unix", F.TYPE_INT64)], start=1):
        msg.field.add(name=name, number=number, type=ftype, label=F.LABEL_OPTIONAL)
    pool = descriptor_pool.DescriptorPool()
    pool.Add(fdp)
    return message_factory.GetMessageClass(pool.FindMessageTypeByName("fin4600.Quote"))


def to_protobuf(q: dict) -> bytes:
    return quote_message_class()(**q).SerializeToString()


def to_avro(q: dict) -> bytes:
    import fastavro
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, fastavro.parse_schema(AVRO_SCHEMA), q)
    return buf.getvalue()


def to_msgpack(q: dict) -> bytes:
    import msgpack
    return msgpack.packb(q)


def to_cbor(q: dict) -> bytes:
    import cbor2
    return cbor2.dumps(q)


ENCODERS = {
    "XML": to_xml, "JSON": to_json, "MessagePack": to_msgpack,
    "CBOR": to_cbor, "Protocol Buffers": to_protobuf, "Avro": to_avro,
}


def encode_all(q: dict = SAMPLE_QUOTE) -> dict[str, bytes]:
    """Return {format_name: encoded_bytes}. Formats whose library is missing are skipped."""
    out = {}
    for name, fn in ENCODERS.items():
        try:
            out[name] = fn(q)
        except ImportError as exc:
            print(f"(skipping {name}: {exc})")
    return out


def hexdump(b: bytes, width: int = 16) -> str:
    return "\n".join(" ".join(f"{x:02x}" for x in b[i:i + width]) for i in range(0, len(b), width))
