from abc import ABC
from dataclasses import asdict
from typing import Any, Dict


from tinydb import TinyDB, Query
from tinydb.table import Document

from . import defaults
from . import mappings as m
from . import data_models as models


def init_db(
    local_storage_path: str,
):
    return TinyDB(f"{local_storage_path}/db.json")


class Es8TableException(Exception):
    pass


class Es8Table:
    model_map = models.MODEL_MAP

    def __init__(self, db: TinyDB, orm: Query, table_name: str) -> None:
        self._db = db
        self._orm = orm
        self._table_name = table_name
        self._table = self._db.table(self._table_name)
        self.current_entry = {}

    def _sanitize_payload(self, payload: Dict[str, Any], screen: str) -> Dict[str, Any]:
        """For a given payload dict and screen:
        - find the associated data model
        - filter the payload dict to remove keys not in the model
        - return the union of both dicts (to include any default fields from the model)
        """
        model = asdict(self.model_map[screen]())
        filtered = {k: v for k, v in payload.items() if k in model}
        return model | filtered

    def upsert(self, payload: Dict[str, Any], screen: str):
        if self.current_entry.get(screen) is None:
            self._table.upsert(
                self._sanitize_payload(payload, screen), self._orm.type == screen
            )
        else:
            self._table.upsert(
                Document(
                    self._sanitize_payload(payload, screen),
                    doc_id=self.current_entry[screen],
                )
            )

    def get(self, screen: str = None):
        if self.current_entry.get(screen) is not None:
            result = self._table.get(doc_id=self.current_entry[screen])
        elif screen is not None:
            result = self._table.get(self._orm.type == screen)
        else:
            result = None
        return result

    def insert(self, payload: Dict[str, Any], screen: str):
        return self._table.insert(self._sanitize_payload(payload, screen))

    def search(self, screen: str):
        return self._table.search(self._orm.type == screen)

    def delete(self, screen: str):
        return self._table.remove(doc_ids=[self.current_entry.get(screen)])
