"""SQLite read layer for Apple Notes database."""

import gzip
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


def extract_text_from_note_data(data: bytes) -> str:
    """Extract plain text from compressed note data.

    Apple Notes stores content as gzip-compressed protobuf.
    This extracts readable text for searching.
    """
    if not data:
        return ""

    try:
        decompressed = gzip.decompress(data)
    except Exception:
        return ""

    # Extract UTF-8 text sequences from protobuf binary
    text_parts = []
    current_text = bytearray()

    for byte in decompressed:
        # Printable ASCII, whitespace, or UTF-8 continuation bytes
        if 32 <= byte <= 126 or byte in (9, 10, 13) or byte >= 192:
            current_text.append(byte)
        else:
            if len(current_text) >= 3:
                try:
                    decoded = current_text.decode("utf-8", errors="ignore")
                    text_parts.append(decoded)
                except Exception:
                    pass
            current_text = bytearray()

    # Handle remaining text
    if len(current_text) >= 3:
        try:
            decoded = current_text.decode("utf-8", errors="ignore")
            text_parts.append(decoded)
        except Exception:
            pass

    return " ".join(text_parts)


def list_notes() -> list[dict]:
    """List all notes with basic metadata."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        n.Z_PK as id,
        COALESCE(n.ZTITLE1, n.ZTITLE, n.ZSNIPPET) as title,
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
        COALESCE(n.ZTITLE1, n.ZTITLE, n.ZSNIPPET) as title,
        n.ZIDENTIFIER as identifier,
        n.ZMODIFICATIONDATE as modified,
        n.ZCREATIONDATE as created,
        f.ZTITLE as folder,
        nd.ZDATA as data
    FROM ZICCLOUDSYNCINGOBJECT n
    LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
    LEFT JOIN ZICNOTEDATA nd ON n.ZNOTEDATA = nd.Z_PK
    WHERE (n.ZTITLE1 = ? OR n.ZTITLE = ?)
    AND n.ZMARKEDFORDELETION = 0
    """

    cursor.execute(query, (title, title))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def search_notes(query: str, title_only: bool = False) -> list[dict]:
    """Search notes by title and optionally body content.

    Args:
        query: Search term (case-insensitive partial match)
        title_only: If True, only search title/snippet, not body content
    """
    conn = get_connection()
    cursor = conn.cursor()

    if title_only:
        # Fast path: title-only search using SQL
        sql = """
        SELECT
            n.Z_PK as id,
            COALESCE(n.ZTITLE1, n.ZTITLE, n.ZSNIPPET) as title,
            n.ZIDENTIFIER as identifier,
            n.ZMODIFICATIONDATE as modified,
            n.ZCREATIONDATE as created,
            f.ZTITLE as folder
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        WHERE n.ZNOTEDATA IS NOT NULL
        AND n.ZMARKEDFORDELETION = 0
        AND (n.ZTITLE1 LIKE ? COLLATE NOCASE OR n.ZTITLE LIKE ? COLLATE NOCASE OR n.ZSNIPPET LIKE ? COLLATE NOCASE)
        ORDER BY n.ZMODIFICATIONDATE DESC
        """
        cursor.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%"))
        results = [dict(row) for row in cursor.fetchall()]
    else:
        # Full search: title + body content
        sql = """
        SELECT
            n.Z_PK as id,
            COALESCE(n.ZTITLE1, n.ZTITLE, n.ZSNIPPET) as title,
            n.ZIDENTIFIER as identifier,
            n.ZMODIFICATIONDATE as modified,
            n.ZCREATIONDATE as created,
            f.ZTITLE as folder,
            nd.ZDATA as data
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        LEFT JOIN ZICNOTEDATA nd ON n.ZNOTEDATA = nd.Z_PK
        WHERE n.ZNOTEDATA IS NOT NULL
        AND n.ZMARKEDFORDELETION = 0
        ORDER BY n.ZMODIFICATIONDATE DESC
        """
        cursor.execute(sql)

        query_lower = query.lower()
        results = []
        for row in cursor.fetchall():
            note = dict(row)
            title = note.get("title") or ""
            data = note.pop("data", None)  # Remove data from result

            # Check title first
            if query_lower in title.lower():
                results.append(note)
                continue

            # Check body content
            if data:
                body_text = extract_text_from_note_data(data)
                if query_lower in body_text.lower():
                    results.append(note)

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
