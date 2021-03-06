# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: response.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='response.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=b'\n\x0eresponse.proto\x1a\x19google/protobuf/any.proto\"$\n\tResponses\x12\x17\n\x07matches\x18\x01 \x03(\x0b\x32\x06.Match\"\xf0\x01\n\x05Match\x12\x13\n\x04span\x18\x01 \x01(\x0b\x32\x05.Span\x12*\n\nattributes\x18\x02 \x03(\x0b\x32\x16.Match.AttributesEntry\x12*\n\nunderscore\x18\x03 \x03(\x0b\x32\x16.Match.UnderscoreEntry\x1a\x31\n\x0f\x41ttributesEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x1aG\n\x0fUnderscoreEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b\x32\x14.google.protobuf.Any:\x02\x38\x01\"`\n\x06Labels\x12!\n\x05items\x18\x01 \x03(\x0b\x32\x12.Labels.ItemsEntry\x1a\x33\n\nItemsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x14\n\x05value\x18\x02 \x01(\x0b\x32\x05.Span:\x02\x38\x01\"\"\n\x04Span\x12\r\n\x05start\x18\x01 \x01(\t\x12\x0b\n\x03\x65nd\x18\x02 \x01(\tb\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_any__pb2.DESCRIPTOR,])




_RESPONSES = _descriptor.Descriptor(
  name='Responses',
  full_name='Responses',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='matches', full_name='Responses.matches', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=45,
  serialized_end=81,
)


_MATCH_ATTRIBUTESENTRY = _descriptor.Descriptor(
  name='AttributesEntry',
  full_name='Match.AttributesEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='Match.AttributesEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='Match.AttributesEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=202,
  serialized_end=251,
)

_MATCH_UNDERSCOREENTRY = _descriptor.Descriptor(
  name='UnderscoreEntry',
  full_name='Match.UnderscoreEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='Match.UnderscoreEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='Match.UnderscoreEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=253,
  serialized_end=324,
)

_MATCH = _descriptor.Descriptor(
  name='Match',
  full_name='Match',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='span', full_name='Match.span', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='attributes', full_name='Match.attributes', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='underscore', full_name='Match.underscore', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_MATCH_ATTRIBUTESENTRY, _MATCH_UNDERSCOREENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=84,
  serialized_end=324,
)


_LABELS_ITEMSENTRY = _descriptor.Descriptor(
  name='ItemsEntry',
  full_name='Labels.ItemsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='Labels.ItemsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='Labels.ItemsEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=371,
  serialized_end=422,
)

_LABELS = _descriptor.Descriptor(
  name='Labels',
  full_name='Labels',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='items', full_name='Labels.items', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_LABELS_ITEMSENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=326,
  serialized_end=422,
)


_SPAN = _descriptor.Descriptor(
  name='Span',
  full_name='Span',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='start', full_name='Span.start', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='end', full_name='Span.end', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=424,
  serialized_end=458,
)

_RESPONSES.fields_by_name['matches'].message_type = _MATCH
_MATCH_ATTRIBUTESENTRY.containing_type = _MATCH
_MATCH_UNDERSCOREENTRY.fields_by_name['value'].message_type = google_dot_protobuf_dot_any__pb2._ANY
_MATCH_UNDERSCOREENTRY.containing_type = _MATCH
_MATCH.fields_by_name['span'].message_type = _SPAN
_MATCH.fields_by_name['attributes'].message_type = _MATCH_ATTRIBUTESENTRY
_MATCH.fields_by_name['underscore'].message_type = _MATCH_UNDERSCOREENTRY
_LABELS_ITEMSENTRY.fields_by_name['value'].message_type = _SPAN
_LABELS_ITEMSENTRY.containing_type = _LABELS
_LABELS.fields_by_name['items'].message_type = _LABELS_ITEMSENTRY
DESCRIPTOR.message_types_by_name['Responses'] = _RESPONSES
DESCRIPTOR.message_types_by_name['Match'] = _MATCH
DESCRIPTOR.message_types_by_name['Labels'] = _LABELS
DESCRIPTOR.message_types_by_name['Span'] = _SPAN
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Responses = _reflection.GeneratedProtocolMessageType('Responses', (_message.Message,), {
  'DESCRIPTOR' : _RESPONSES,
  '__module__' : 'response_pb2'
  # @@protoc_insertion_point(class_scope:Responses)
  })
_sym_db.RegisterMessage(Responses)

Match = _reflection.GeneratedProtocolMessageType('Match', (_message.Message,), {

  'AttributesEntry' : _reflection.GeneratedProtocolMessageType('AttributesEntry', (_message.Message,), {
    'DESCRIPTOR' : _MATCH_ATTRIBUTESENTRY,
    '__module__' : 'response_pb2'
    # @@protoc_insertion_point(class_scope:Match.AttributesEntry)
    })
  ,

  'UnderscoreEntry' : _reflection.GeneratedProtocolMessageType('UnderscoreEntry', (_message.Message,), {
    'DESCRIPTOR' : _MATCH_UNDERSCOREENTRY,
    '__module__' : 'response_pb2'
    # @@protoc_insertion_point(class_scope:Match.UnderscoreEntry)
    })
  ,
  'DESCRIPTOR' : _MATCH,
  '__module__' : 'response_pb2'
  # @@protoc_insertion_point(class_scope:Match)
  })
_sym_db.RegisterMessage(Match)
_sym_db.RegisterMessage(Match.AttributesEntry)
_sym_db.RegisterMessage(Match.UnderscoreEntry)

Labels = _reflection.GeneratedProtocolMessageType('Labels', (_message.Message,), {

  'ItemsEntry' : _reflection.GeneratedProtocolMessageType('ItemsEntry', (_message.Message,), {
    'DESCRIPTOR' : _LABELS_ITEMSENTRY,
    '__module__' : 'response_pb2'
    # @@protoc_insertion_point(class_scope:Labels.ItemsEntry)
    })
  ,
  'DESCRIPTOR' : _LABELS,
  '__module__' : 'response_pb2'
  # @@protoc_insertion_point(class_scope:Labels)
  })
_sym_db.RegisterMessage(Labels)
_sym_db.RegisterMessage(Labels.ItemsEntry)

Span = _reflection.GeneratedProtocolMessageType('Span', (_message.Message,), {
  'DESCRIPTOR' : _SPAN,
  '__module__' : 'response_pb2'
  # @@protoc_insertion_point(class_scope:Span)
  })
_sym_db.RegisterMessage(Span)


_MATCH_ATTRIBUTESENTRY._options = None
_MATCH_UNDERSCOREENTRY._options = None
_LABELS_ITEMSENTRY._options = None
# @@protoc_insertion_point(module_scope)
