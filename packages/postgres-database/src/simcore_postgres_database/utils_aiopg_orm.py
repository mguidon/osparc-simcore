"""
    BaseOrm: A draft and basic, yet practical, aiopg-based ORM to simplify operations with postgres database

    - Aims to hide the functionality of aiopg
    - Probably in the direction of the other more sophisticated libraries like (that we might adopt)
        - the new async sqlalchemy ORM https://docs.sqlalchemy.org/en/14/orm/
        - https://piccolo-orm.readthedocs.io/en/latest/index.html
"""
# pylint: disable=no-value-for-parameter

import functools
import operator
from typing import Dict, Generic, List, Optional, Set, Tuple, TypeVar, Union

import sqlalchemy as sa
from aiopg.sa.connection import SAConnection
from aiopg.sa.result import ResultProxy, RowProxy
from sqlalchemy.sql.base import ImmutableColumnCollection
from sqlalchemy.sql.dml import Insert, Update, UpdateBase
from sqlalchemy.sql.elements import literal_column
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.selectable import Select

RowUId = TypeVar("RowUId", int, str)  # typically id or uuid


def _normalize(names: Union[str, List[str], None]) -> List[str]:
    if not names:
        return []
    if isinstance(names, str):
        names = names.replace(",", " ").split()
    return list(map(str, names))


# Tokens for defaults
ALL_COLUMNS = f"{__name__}.ALL_COLUMNS"
PRIMARY_KEY = f"{__name__}.PRIMARY_KEY"


class BaseOrm(Generic[RowUId]):
    def __init__(
        self,
        table: sa.Table,
        connection: SAConnection,
        *,
        readonly: Optional[Set] = None,
        writeonce: Optional[Set] = None,
    ):
        """
        :param readonly: read-only columns typically created in the server side, defaults to None
        :param writeonce: columns inserted once but that cannot be updated, defaults to None
        :raises ValueError: an error in any of the arguments
        """
        self._conn = connection
        self._readonly: Set = readonly or {"created", "modified", "id"}
        self._writeonce: Set = writeonce or set()

        # row selection logic
        self._unique_match = None
        try:
            self._primary_key: Column = next(c for c in table.columns if c.primary_key)
            # FIXME: how can I compare a concrete with a generic type??
            # assert self._primary_key.type.python_type == RowUId  # nosec
        except StopIteration as e:
            raise ValueError(f"Table {table.name} MUST define a primary key") from e

        self._table = table

    def _compose_select_query(
        self,
        columns: Union[str, List[str]],
    ) -> Select:
        column_names: List[str] = _normalize(columns)

        if ALL_COLUMNS in column_names:
            query = self._table.select()
        elif PRIMARY_KEY in column_names:
            query = sa.select(
                [
                    self._primary_key,
                ]
            )
        else:
            query = sa.select([self._table.c[name] for name in column_names])

        return query

    def _append_returning(
        self, columns: Union[str, List[str]], query: UpdateBase
    ) -> Tuple[UpdateBase, bool]:
        column_names: List[str] = _normalize(columns)

        is_scalar: bool = len(column_names) == 1

        if PRIMARY_KEY in column_names:
            # defaults to primery key
            query = query.returning(self._primary_key)

        elif ALL_COLUMNS in column_names:
            query = query.returning(literal_column("*"))
            is_scalar = False
            # NOTE: returning = self._table would also work. less efficient?
        else:
            # selection
            query = query.returning(*[self._table.c[name] for name in column_names])

        return query, is_scalar

    @staticmethod
    def _check_access_rights(access: Set, values: Dict) -> None:
        not_allowed: Set[str] = access.intersection(values.keys())
        if not_allowed:
            raise ValueError(f"Columns {not_allowed} are read-only")

    @property
    def columns(self) -> ImmutableColumnCollection:
        return self._table.columns

    def set_default(self, rowid: Optional[RowUId] = None, **unique_id) -> "BaseOrm":
        """
        Sets default for read operations either by passing a row identifier or a filter
        """
        if unique_id and rowid:
            raise ValueError("Either identifier or unique condition but not both")

        if rowid:
            self._unique_match = self._primary_key == rowid
        elif unique_id:
            self._unique_match = functools.reduce(
                operator.and_,
                (
                    operator.eq(self._table.columns[name], value)
                    for name, value in unique_id.items()
                ),
            )
        if not self.is_default_set():
            raise ValueError(
                "Either identifier or unique condition required. None provided"
            )
        return self

    def clear_default(self) -> None:
        self._unique_match = None

    def is_default_set(self) -> bool:
        # WARNING: self._unique_match can evaluate false. Keep explicit
        return self._unique_match is not None

    async def fetch(
        self,
        returning_cols: Union[str, List[str]] = ALL_COLUMNS,
        *,
        rowid: Optional[RowUId] = None,
    ) -> Optional[RowProxy]:
        query = self._compose_select_query(returning_cols)
        if rowid:
            # overrides pinned row
            query = query.where(self._primary_key == rowid)
        elif self.is_default_set():
            assert self._unique_match is not None  # nosec
            query = query.where(self._unique_match)

        result: ResultProxy = await self._conn.execute(query)
        row: Optional[RowProxy] = await result.first()
        return row

    async def fetchall(
        self,
        returning_cols: Union[str, List[str]] = ALL_COLUMNS,
    ) -> List[RowProxy]:

        query = self._compose_select_query(returning_cols)

        result: ResultProxy = await self._conn.execute(query)
        rows: List[RowProxy] = await result.fetchall()
        return rows

    async def update(
        self, returning_cols: Union[str, List[str]] = PRIMARY_KEY, **values
    ) -> Union[RowUId, RowProxy, None]:
        self._check_access_rights(self._readonly, values)
        self._check_access_rights(self._writeonce, values)

        query: Update = self._table.update().values(**values)
        if self.is_default_set():
            assert self._unique_match is not None  # nosec
            query = query.where(self._unique_match)

        query, is_scalar = self._append_returning(returning_cols, query)
        if is_scalar:
            return await self._conn.scalar(query)

        result: ResultProxy = await self._conn.execute(query)
        row: Optional[RowProxy] = await result.first()
        return row

    async def insert(
        self, returning_cols: Union[str, List[str]] = PRIMARY_KEY, **values
    ) -> Union[RowUId, RowProxy, None]:
        self._check_access_rights(self._readonly, values)

        query: Insert = self._table.insert().values(**values)

        query, is_scalar = self._append_returning(returning_cols, query)
        if is_scalar:
            return await self._conn.scalar(query)

        result: ResultProxy = await self._conn.execute(query)
        row: Optional[RowProxy] = await result.first()
        return row