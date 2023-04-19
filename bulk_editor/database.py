import sqlite3

DB_FILE = "es8_editor.db"


class Metadata(object):
    def __init__(self):
        self._db = sqlite3.connect(DB_FILE)
        self._db.row_factory = sqlite3.Row
        self._db.cursor().execute(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                patch_backup_filepath TEXT,
                default_patch_filepath TEXT
            )
            """
        )
        self._db.commit()

    def add(self, profile: dict):
        self._db.cursor().execute(
            """
            INSERT INTO metadata(name, patch_backup_filepath, default_patch_filepath)
            VALUES(:name, :patch_backup_filepath, :default_patch_filepath)""",
            profile,
        )
        self._db.commit()
        return self.fetch_name_by_id(profile["name"])

    def fetch_name_by_id(self, name: str):
        return (
            self._db.cursor()
            .execute("SELECT id from metadata where name=:name", {"name": name})
            .fetchone()
        )

    def get_metadata_by_id(self, id: int):
        cursor = self._db.execute("SELECT * FROM metadata WHERE id = ?", (id,))
        return cursor.fetchone()

    def get_metadata_by_name(self, name: str):
        cursor = self._db.execute("SELECT * FROM metadata WHERE name = ?", (name,))
        return cursor.fetchone()

    def update(self, profile_id, profile: dict):
        profile["id"] = profile_id
        self._db.execute(
            """
            UPDATE metadata 
            SET 
                name = :name,
                patch_backup_filepath = :patch_backup_filepath,
                default_patch_filepath = :default_patch_filepath
            WHERE id = :id
            """,
            profile,
        )
        self._db.commit()

    def delete_metadata(self, id):
        self._db.execute("DELETE FROM metadata WHERE id = ?", (id,))
        self._db.commit()

    def close(self):
        self._db.close()


class AssignModel(object):
    def __init__(self):
        self._db = sqlite3.connect(":memory:")
        self._db.row_factory = sqlite3.Row

        self._db.cursor().execute(
            """
            CREATE TABLE assign(
                patch_id INTEGER,
                assign_number INTEGER,
                source TEXT,
                target TEXT,
                mode TEXT,
                is_enabled INTEGER,
                min INTEGER,
                max INTEGER,
                ActL INTEGER,
                ActH INTEGER,
                trigger INTEGER,
                time INTEGER,
                curve INTEGER,
                rate INTEGER,
                form INTEGER,
                cc# INTEGER,
                target_cc_ch INTEGER,
                target_cc# INTEGER
                
            )
            """
        )
