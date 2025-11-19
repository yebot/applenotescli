"""AppleScript write layer for Apple Notes operations."""

import subprocess


class AppleScriptError(Exception):
    """Error running AppleScript."""
    pass


def run_applescript(script: str) -> str:
    """Execute AppleScript and return the result."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise AppleScriptError(f"AppleScript error: {e.stderr.strip()}") from e


def create_note(title: str, body: str, folder: str = "Notes") -> str:
    """Create a new note in the specified folder."""
    # Escape quotes in strings for AppleScript
    title_escaped = title.replace('"', '\\"')
    body_escaped = body.replace('"', '\\"')
    folder_escaped = folder.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        tell folder "{folder_escaped}"
            make new note with properties {{name:"{title_escaped}", body:"{body_escaped}"}}
        end tell
    end tell
    '''

    return run_applescript(script)


def update_note(title: str, new_body: str) -> str:
    """Update the body of an existing note."""
    title_escaped = title.replace('"', '\\"')
    body_escaped = new_body.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        set body of theNote to "{body_escaped}"
    end tell
    '''

    return run_applescript(script)


def append_to_note(title: str, content: str) -> str:
    """Append content to an existing note."""
    title_escaped = title.replace('"', '\\"')
    content_escaped = content.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        set body of theNote to (body of theNote) & "{content_escaped}"
    end tell
    '''

    return run_applescript(script)


def delete_note(title: str) -> str:
    """Delete a note by title."""
    title_escaped = title.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        delete (first note whose name is "{title_escaped}")
    end tell
    '''

    return run_applescript(script)


def create_folder(name: str) -> str:
    """Create a new folder."""
    name_escaped = name.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        make new folder with properties {{name:"{name_escaped}"}}
    end tell
    '''

    return run_applescript(script)


def get_note_body(title: str) -> str:
    """Get the HTML body of a note via AppleScript."""
    title_escaped = title.replace('"', '\\"')

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        return body of theNote
    end tell
    '''

    return run_applescript(script)
