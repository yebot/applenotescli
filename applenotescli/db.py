"""SQLite read layer for Apple Notes database."""

import sqlite3
from pathlib import Path

# Apple Notes database location
NOTES_DB_PATH = Path(
    "~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
).expanduser()


class NotesDBError(Exception):
    """Base exception for Notes database errors."""
    pass


class DatabaseNotFoundError(NotesDBError):
    """Notes database file not found."""
    pass


class DatabaseLockedError(NotesDBError):
    """Notes database is locked by another process."""
    pass


def get_connection() -> sqlite3.Connection:
    """Get a read-only connection to the Notes database."""
    if not NOTES_DB_PATH.exists():
        raise DatabaseNotFoundError(f"Notes database not found at {NOTES_DB_PATH}")

    try:
        # Connect in read-only mode with timeout for locked database
        conn = sqlite3.connect(
            f"file:{NOTES_DB_PATH}?mode=ro",
            uri=True,
            timeout=5.0
        )
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        error_msg = str(e).lower()
        if "database is locked" in error_msg:
            raise DatabaseLockedError(
                "Notes database is locked. Please close Notes app and try again."
            ) from e
        if "unable to open database file" in error_msg:
            raise NotesDBError(
                "Cannot access Notes database. Please grant Full Disk Access to Terminal:\n"
                "System Settings > Privacy & Security > Full Disk Access > Enable Terminal"
            ) from e
        raise NotesDBError(f"Database error: {e}") from e


def list_notes() -> list[dict]:
    """List all notes with basic metadata."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        n.Z_PK as id,
        COALESCE(n.ZTITLE, n.ZSNIPPET) as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        n.ZCREATIONDATE as created,
        f.ZTITLE as folder
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    WHERE n.ZNOTEDATA IS NOT NULL
    AND n.ZMARKEDFORDELETION = 0
    ORDER BY n.ZMODIFICATIONDATE DESC
    """

    cursor.execute(query)
    results = []
    for row in cursor.fetchall():
        results.append(dict(row))

    conn.close()
    return results


def get_note_by_title(title: str) -> dict | None:
    """Get a note by its title."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        n.Z_PK as id,
        n.ZTITLE as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        n.ZCREATIONDATE as created,
        f.ZTITLE as folder,
        nd.ZDATA as data
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    LEFT JOIN ZICNOTEDATA nd ON n.ZNOTEDATA = nd.Z_PK
    WHERE n.ZTITLE = ?
    AND n.ZMARKEDFORDELETION = 0
    """

    cursor.execute(query, (title,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def search_notes(query: str) -> list[dict]:
    """Search notes by title with case-insensitive partial matching."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        n.Z_PK as id,
        COALESCE(n.ZTITLE, n.ZSNIPPET) as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        n.ZCREATIONDATE as created,
        f.ZTITLE as folder
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    WHERE n.ZNOTEDATA IS NOT NULL
    AND n.ZMARKEDFORDELETION = 0
    AND (n.ZTITLE LIKE ? COLLATE NOCASE OR n.ZSNIPPET LIKE ? COLLATE NOCASE)
    ORDER BY n.ZMODIFICATIONDATE DESC
    """

    cursor.execute(sql, (f"%{query}%", f"%{query}%"))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results


def list_folders() -> list[dict]:
    """List all folders."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        Z_PK as id,
        ZTITLE as title,
        ZIDENTIFIER as identifier
    FROM ZICCLOUDSYNCINGOBJECT
    WHERE ZTITLE IS NOT NULL
    AND ZFOLDER IS NULL
    AND ZMARKEDFORDELETION = 0
    AND Z_PK IN (SELECT DISTINCT ZFOLDER FROM ZICCLOUDSYNCINGOBJECT WHERE ZFOLDER IS NOT NULL)
    ORDER BY ZTITLE
    """

    cursor.execute(query)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return results
