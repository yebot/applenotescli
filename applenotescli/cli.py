"""CLI entry point for Apple Notes CLI."""

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="notes")
def cli():
    """Apple Notes CLI - CRUD operations for Apple Notes."""
    pass


@cli.command()
def list():
    """List all notes."""
    click.echo("Listing notes... (not yet implemented)")


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
