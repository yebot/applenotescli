"""SQLite read layer for Apple Notes database."""

import os
import sqlite3
from pathlib import Path

# Apple Notes database location
NOTES_DB_PATH = Path(
    "~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"
).expanduser()


def get_connection() -> sqlite3.Connection:
    """Get a read-only connection to the Notes database."""
    if not NOTES_DB_PATH.exists():
        raise FileNotFoundError(f"Notes database not found at {NOTES_DB_PATH}")

    # Connect in read-only mode
    conn = sqlite3.connect(f"file:{NOTES_DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_notes() -> list[dict]:
    """List all notes with basic metadata."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        n.Z_PK as id,
        n.ZTITLE as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        n.ZCREATIONDATE as created,
        f.ZTITLE as folder
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    WHERE n.ZTITLE IS NOT NULL
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
    """Search notes by title (basic LIKE search)."""
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        n.Z_PK as id,
        n.ZTITLE as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        f.ZTITLE as folder
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    WHERE n.ZTITLE LIKE ?
    AND n.ZMARKEDFORDELETION = 0
    ORDER BY n.ZMODIFICATIONDATE DESC
    """

    cursor.execute(sql, (f"%{query}%",))
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
