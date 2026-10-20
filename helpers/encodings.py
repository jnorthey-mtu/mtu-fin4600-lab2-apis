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


# ---------------------------------------------------------------------------
# FIX: the classic tag=value text format, and FIX Simple Binary Encoding (SBE)
# ---------------------------------------------------------------------------
SOH = "\x01"   # FIX's field delimiter (shown as "|" when printed for humans)


def _fix_checksum(msg: str) -> str:
    """FIX tag 10: sum of every byte up to and including the SOH before '10=', mod 256, as 3 digits."""
    return f"{sum(msg.encode()) % 256:03d}"


def to_fix_tagvalue(q: dict) -> bytes:
    """One quote as a FIX 4.4 MarketDataSnapshotFullRefresh (35=W) in tag=value format.

    Tags: 55 Symbol · 268 NoMDEntries · 269 MDEntryType (2 = trade, B = trade volume) ·
    270 MDEntryPx · 15 Currency · 271 MDEntrySize · 52 SendingTime.
    """
    allowed = {"symbol", "currency", "price", "volume", "time_unix"}
    extra = set(q) - allowed
    if extra:
        raise ValueError(f"no FIX tag mapped for {sorted(extra)}")
    import datetime as _dt
    sending = _dt.datetime.fromtimestamp(q["time_unix"], _dt.timezone.utc).strftime("%Y%m%d-%H:%M:%S")
    body = SOH.join([
        "35=W", "49=MTUQUANT", "56=STUDENT", "34=1", f"52={sending}",
        f"55={q['symbol']}", "268=2",
        "269=2", f"270={q['price']}", f"15={q['currency']}",
        "269=B", f"271={q['volume']}",
    ]) + SOH
    head = f"8=FIX.4.4{SOH}9={len(body.encode())}{SOH}"
    msg = head + body
    return (msg + f"10={_fix_checksum(msg)}{SOH}").encode()


SBE_SCHEMA_XML = """<sbe:messageSchema xmlns:sbe="http://fixprotocol.io/2016/sbe"
    package="fin4600" id="4600" version="1" byteOrder="littleEndian">
  <types>
    <composite name="messageHeader">
      <type name="blockLength" primitiveType="uint16"/>
      <type name="templateId"  primitiveType="uint16"/>
      <type name="schemaId"    primitiveType="uint16"/>
      <type name="version"     primitiveType="uint16"/>
    </composite>
    <composite name="Price9">                       <!-- price = mantissa x 10^-9 -->
      <type name="mantissa" primitiveType="int64"/>
      <type name="exponent" primitiveType="int8" presence="constant">-9</type>
    </composite>
    <type name="Symbol"   primitiveType="char" length="8"/>
    <type name="Currency" primitiveType="char" length="3"/>
  </types>
  <sbe:message name="Quote" id="1">                 <!-- field ids reuse FIX tag numbers -->
    <field name="price"    id="270" type="Price9"   offset="0"/>
    <field name="volume"   id="271" type="uint64"   offset="8"/>
    <field name="timeUnix" id="60"  type="uint64"   offset="16"/>
    <field name="symbol"   id="55"  type="Symbol"   offset="24"/>
    <field name="currency" id="15"  type="Currency" offset="32"/>
  </sbe:message>
</sbe:messageSchema>"""

# Fixed layout of the Quote block: name -> (offset in bytes after the 8-byte header, struct format)
SBE_HEADER = "<HHHH"                     # blockLength, templateId, schemaId, version (little-endian)
SBE_LAYOUT = {"price": (0, "<q"), "volume": (8, "<Q"), "time_unix": (16, "<Q"),
              "symbol": (24, "8s"), "currency": (32, "3s")}
SBE_BLOCK_LENGTH = 35
SBE_PRICE_EXPONENT = -9


def to_sbe(q: dict) -> bytes:
    """Hand-rolled SBE encoder for the Quote message above.

    Real systems generate the encoder from the XML schema (e.g. with Real Logic's sbe-tool);
    we use Python's struct module so you can see every byte.
    """
    import struct
    extra = set(q) - set(SBE_LAYOUT)
    if extra:
        raise ValueError(f"field(s) {sorted(extra)} not in the SBE schema — fixed layout, no room")
    header = struct.pack(SBE_HEADER, SBE_BLOCK_LENGTH, 1, 4600, 1)
    block = struct.pack("<qQQ8s3s",
                        round(q["price"] * 10 ** -SBE_PRICE_EXPONENT), q["volume"], q["time_unix"],
                        q["symbol"].encode("ascii"), q["currency"].encode("ascii"))
    return header + block


def sbe_read(buf: bytes, field: str):
    """Read ONE field straight from its fixed offset — no parsing of anything else (the point of SBE)."""
    import struct
    offset, fmt = SBE_LAYOUT[field]
    (value,) = struct.unpack_from(fmt, buf, struct.calcsize(SBE_HEADER) + offset)
    if field == "price":
        return value / 10 ** -SBE_PRICE_EXPONENT    # exact decimal mantissa → float only at the edge
    if isinstance(value, bytes):
        return value.rstrip(b"\x00").decode("ascii")
    return value


def to_msgpack(q: dict) -> bytes:
    import msgpack
    return msgpack.packb(q)


def to_cbor(q: dict) -> bytes:
    import cbor2
    return cbor2.dumps(q)


ENCODERS = {
    "XML": to_xml, "JSON": to_json, "FIX tag=value": to_fix_tagvalue, "MessagePack": to_msgpack,
    "CBOR": to_cbor, "Protocol Buffers": to_protobuf, "Avro": to_avro, "FIX SBE": to_sbe,
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
