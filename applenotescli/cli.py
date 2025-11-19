"""CLI entry point for Apple Notes CLI."""

import click
from datetime import datetime, timedelta

from . import __version__
from . import db


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
def search(query: str, folder: str | None):
    """Search notes by title."""
    try:
        notes = db.search_notes(query)

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
@click.argument("title")
def show(title: str):
    """Show a note by title."""
    click.echo(f"Showing note: {title} (not yet implemented)")


@cli.command()
@click.argument("title")
@click.option("--folder", "-f", default="Notes", help="Folder to create note in")
def create(title: str, folder: str):
    """Create a new note."""
    click.echo(f"Creating note '{title}' in folder '{folder}' (not yet implemented)")


@cli.command()
@click.argument("title")
def edit(title: str):
    """Edit an existing note."""
    click.echo(f"Editing note: {title} (not yet implemented)")


@cli.command()
@click.argument("title")
def delete(title: str):
    """Delete a note."""
    click.echo(f"Deleting note: {title} (not yet implemented)")


if __name__ == "__main__":
    cli()
