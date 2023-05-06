from tinydb import TinyDB


def init_db(
    local_storage_path: str,
):
    return TinyDB(f"{local_storage_path}/db.json")
