"""CLI entry point for Apple Notes CLI."""

import click
from datetime import datetime, timedelta

from . import __version__
from . import db
from . import applescript
from . import convert


def format_date(timestamp: float | None) -> str:
    """Format Apple Core Data timestamp to readable date."""
    if timestamp is None:
        return "Unknown"
    # Core Data timestamps are seconds since 2001-01-01
    # Valid range: 0 to ~50 years in seconds
    if timestamp < 0 or timestamp > 2000000000:
        return "Unknown"
    try:
        dt = datetime(2001, 1, 1) + timedelta(seconds=timestamp)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (OverflowError, OSError):
        return "Unknown"


@click.group()
@click.version_option(version=__version__, prog_name="notes")
def cli():
    """Apple Notes CLI - CRUD operations for Apple Notes."""
    pass


@cli.command()
@click.option("--folder", "-f", help="Filter by folder name")
def list(folder: str | None):
    """List all notes."""
    try:
        notes = db.list_notes()

        if folder:
            notes = [n for n in notes if n.get("folder") == folder]

        if not notes:
            click.echo("No notes found.")
            return

        # Display notes in a table format
        click.echo(f"{'ID':<6} {'Title':<40} {'Modified':<18} {'Folder'}")
        click.echo("-" * 80)

        for note in notes:
            raw_title = note["title"] or "(Untitled)"
            title = raw_title[:38] + ".." if len(raw_title) > 40 else raw_title
            modified = format_date(note.get("modified"))
            folder_name = note.get("folder") or "Notes"
            click.echo(f"{note['id']:<6} {title:<40} {modified:<18} {folder_name}")

        click.echo(f"\nTotal: {len(notes)} notes")

    except db.DatabaseNotFoundError as e:
        raise click.ClickException(str(e))
    except db.DatabaseLockedError as e:
        raise click.ClickException(str(e))
    except db.NotesDBError as e:
        raise click.ClickException(f"Database error: {e}")


@cli.command()
@click.argument("query")
@click.option("--folder", "-f", help="Filter by folder name")
@click.option("--title-only", "-t", is_flag=True, help="Search title only (faster)")
def search(query: str, folder: str | None, title_only: bool):
    """Search notes by title and content."""
    try:
        notes = db.search_notes(query, title_only=title_only)

        if folder:
            notes = [n for n in notes if n.get("folder") == folder]

        if not notes:
            click.echo(f"No notes found matching '{query}'.")
            return

        # Display notes in a table format
        click.echo(f"{'ID':<6} {'Title':<40} {'Modified':<18} {'Folder'}")
        click.echo("-" * 80)

        for note in notes:
            raw_title = note["title"] or "(Untitled)"
            title = raw_title[:38] + ".." if len(raw_title) > 40 else raw_title
            modified = format_date(note.get("modified"))
            folder_name = note.get("folder") or "Notes"
            click.echo(f"{note['id']:<6} {title:<40} {modified:<18} {folder_name}")

        click.echo(f"\nFound: {len(notes)} notes matching '{query}'")

    except db.DatabaseNotFoundError as e:
        raise click.ClickException(str(e))
    except db.DatabaseLockedError as e:
        raise click.ClickException(str(e))
    except db.NotesDBError as e:
        raise click.ClickException(f"Database error: {e}")


@cli.command()
@click.argument("identifier")
def show(identifier: str):
    """Show a note's content by ID or title."""
    try:
        # Try to parse as ID first
        try:
            note_id = int(identifier)
            note = db.get_note_by_id(note_id)
        except ValueError:
            # Not a number, search by title
            note = db.get_note_by_title(identifier)

        if not note:
            raise click.ClickException(f"Note not found: {identifier}")

        # Display note metadata
        title = note.get("title") or "(Untitled)"
        folder = note.get("folder") or "Notes"
        modified = format_date(note.get("modified"))
        created = format_date(note.get("created"))

        click.echo(f"Title: {title}")
        click.echo(f"Folder: {folder}")
        click.echo(f"Modified: {modified}")
        click.echo(f"Created: {created}")
        click.echo("-" * 40)

        # Extract and display content
        data = note.get("data")
        if data:
            content = db.extract_text_from_note_data(data, for_display=True)
            if content:
                click.echo(content)
            else:
                click.echo("(No text content)")
        else:
            click.echo("(No content)")

    except db.DatabaseNotFoundError as e:
        raise click.ClickException(str(e))
    except db.DatabaseLockedError as e:
        raise click.ClickException(str(e))
    except db.NotesDBError as e:
        raise click.ClickException(f"Database error: {e}")


@cli.command()
def folders():
    """List all folders."""
    try:
        folders_list = db.list_folders()

        if not folders_list:
            click.echo("No folders found.")
            return

        # Group by account
        accounts = {}
        for folder in folders_list:
            account = folder.get("account") or "Unknown"
            # Clean up account name (remove leading numbers like "1_")
            if account.startswith("1_"):
                account = account[2:]
            if account not in accounts:
                accounts[account] = []
            accounts[account].append(folder)

        for account, folder_items in accounts.items():
            click.echo(f"\n{account}:")
            for folder in folder_items:
                title = folder.get("title") or "(Untitled)"
                click.echo(f"  {folder['id']:<6} {title}")

        total = sum(len(f) for f in accounts.values())
        click.echo(f"\nTotal: {total} folders")

    except db.DatabaseNotFoundError as e:
        raise click.ClickException(str(e))
    except db.DatabaseLockedError as e:
        raise click.ClickException(str(e))
    except db.NotesDBError as e:
        raise click.ClickException(f"Database error: {e}")


@cli.command()
@click.argument("title")
@click.option("--body", "-b", help="Note body (Markdown format)")
@click.option("--folder", "-f", default="Notes", help="Folder to create note in")
@click.option("--account", "-a", help="Account name (default: first account)")
def create(title: str, body: str | None, folder: str, account: str | None):
    """Create a new note.

    Body can be provided via --body option or piped from stdin.
    Markdown formatting is supported and will be converted to HTML.
    """
    import sys

    # Get body from option or stdin
    if body is None:
        if not sys.stdin.isatty():
            body = sys.stdin.read()
        else:
            body = ""

    # Convert Markdown to HTML
    html_body = convert.markdown_to_html(body) if body else ""

    try:
        note_id = applescript.create_note(
            title=title,
            body=html_body,
            folder=folder,
            account=account
        )
        click.echo(f"Created note '{title}' (ID: {note_id})")

    except applescript.AppleScriptPermissionError as e:
        raise click.ClickException(str(e))
    except applescript.AppleScriptExecutionError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("identifier")
@click.option("--body", "-b", help="New body content (Markdown format)")
@click.option("--editor", "-e", is_flag=True, help="Open in $EDITOR")
def edit(identifier: str, body: str | None, editor: bool):
    """Edit an existing note.

    IDENTIFIER can be a note ID or title.
    Use --editor to open in $EDITOR, or --body to set content directly.
    Content can also be piped from stdin.
    """
    import os
    import sys
    import tempfile

    try:
        # Find the note - try as ID first
        try:
            note_id = int(identifier)
            note = db.get_note_by_id(note_id)
        except ValueError:
            note = db.get_note_by_title(identifier)

        if not note:
            raise click.ClickException(f"Note not found: {identifier}")

        # Get the Apple Notes ID for this note
        note_title = note.get("title") or "(Untitled)"
        try:
            apple_id = applescript.get_note_id_by_title(note_title)
        except applescript.AppleScriptExecutionError as e:
            raise click.ClickException(f"Could not find note in Apple Notes: {e}")

        # Get initial modification date for race condition detection
        initial_mod_date = applescript.get_note_modification_date(apple_id)

        # Get current content
        current_html = applescript.get_note_body_by_id(apple_id)
        current_markdown = convert.html_to_markdown(current_html)

        # Get new content
        new_markdown = None

        if body is not None:
            new_markdown = body
        elif not sys.stdin.isatty():
            new_markdown = sys.stdin.read()
        elif editor:
            # Open in editor
            editor_cmd = os.environ.get("EDITOR", "vim")
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
                f.write(current_markdown)
                temp_path = f.name

            try:
                import subprocess
                result = subprocess.run([editor_cmd, temp_path])
                if result.returncode != 0:
                    raise click.ClickException(f"Editor exited with code {result.returncode}")

                with open(temp_path) as f:
                    new_markdown = f.read()
            finally:
                os.unlink(temp_path)
        else:
            raise click.ClickException(
                "No content provided. Use --body, --editor, or pipe content."
            )

        # Check if content actually changed
        if new_markdown.strip() == current_markdown.strip():
            click.echo("No changes made.")
            return

        # Check for race condition - modification date changed?
        current_mod_date = applescript.get_note_modification_date(apple_id)
        if current_mod_date != initial_mod_date:
            click.echo(
                f"Warning: Note was modified externally.\n"
                f"  Initial: {initial_mod_date}\n"
                f"  Current: {current_mod_date}\n"
            )
            if not click.confirm("Overwrite changes?"):
                click.echo("Edit cancelled.")
                return

        # Convert to HTML and update
        new_html = convert.markdown_to_html(new_markdown)
        applescript.update_note_by_id(apple_id, new_html)
        click.echo(f"Updated note '{note_title}'")

    except db.DatabaseNotFoundError as e:
        raise click.ClickException(str(e))
    except db.DatabaseLockedError as e:
        raise click.ClickException(str(e))
    except db.NotesDBError as e:
        raise click.ClickException(f"Database error: {e}")
    except applescript.AppleScriptPermissionError as e:
        raise click.ClickException(str(e))
    except applescript.AppleScriptExecutionError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("title")
def delete(title: str):
    """Delete a note."""
    click.echo(f"Deleting note: {title} (not yet implemented)")


if __name__ == "__main__":
    cli()
