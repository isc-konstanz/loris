# -*- coding: utf-8 -*-
"""
lori.connectors.sql.column
~~~~~~~~~~~~~~~~~~~~~~~~~~


"""

from __future__ import annotations

import datetime as dt
from typing import Any, AnyStr, Optional, Type, TypeVar

import sqlalchemy as sql
from sqlalchemy.types import BOOLEAN, DATETIME, FLOAT, INTEGER, TIMESTAMP, String, TypeEngine

import pandas as pd
from lori.core import ConfigurationException, ResourceException

ColumnType = TypeVar("ColumnType", Type[TypeEngine], TypeEngine)


class Column(sql.Column):
    inherit_cache: bool = True

    # noinspection PyShadowingBuiltins, SpellCheckingInspection
    def __init__(
        self,
        name: str,
        type: ColumnType,
        nullable: bool = True,
        default: Optional[Any] = None,
        onupdate: Optional[Any] = None,
        **kwargs,
    ) -> None:
        super().__init__(name, type, nullable=nullable, server_default=default, server_onupdate=onupdate, **kwargs)

    @property
    def _constructor(self):
        # TODO: Look into
        return sql.Column

    def validate(self, data: Any) -> Any:
        if data is None and not self.nullable:
            raise ResourceException(f"None value for '{self.name}' NOT NULL")
        return data


# noinspection PyShadowingBuiltins
def parse_type(type: Type | AnyStr, length: Optional[int] = None) -> Type[TypeEngine] | TypeEngine:
    if issubclass(type, float):
        type = "FLOAT"
    elif issubclass(type, int):
        type = "INTEGER"
    elif issubclass(type, bool):
        type = "BOOL"
    elif issubclass(type, (pd.Timestamp, dt.datetime)):
        type = "TIMESTAMP"
    elif issubclass(type, str):
        type = "STRING"
    elif isinstance(type, str):
        type = type.upper()
    else:
        raise ConfigurationException(f"Unknown SQL data type: {type}")

    return to_type_engine(type, length)


# noinspection PyShadowingBuiltins
def to_type_engine(type: Type | AnyStr, length: Optional[int] = None) -> Type[TypeEngine] | TypeEngine:
    if type == "FLOAT":
        return FLOAT
    if type in ["IN", "INTEGER"]:
        return INTEGER
    if type in ["BOOL", "BOOLEAN"]:
        return BOOLEAN
    if type == "DATETIME":
        return DATETIME
    if type == "TIMESTAMP":
        return TIMESTAMP
    if type in ["VARCHAR", "STRING"]:
        if type == "VARCHAR" and length is None:
            raise ConfigurationException(f"Invalid SQL data type '{type}' without configured length")
        if length is None:
            return String
        return String(length)

    raise ConfigurationException(f"Unknown SQL data type: {type}")