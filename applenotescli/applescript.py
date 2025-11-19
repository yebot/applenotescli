"""AppleScript write layer for Apple Notes operations."""

import subprocess


class AppleScriptError(Exception):
    """Base exception for AppleScript errors."""
    pass


class AppleScriptPermissionError(AppleScriptError):
    """TCC permission denied error."""
    pass


class AppleScriptExecutionError(AppleScriptError):
    """AppleScript execution failed."""
    pass


def escape_for_applescript(text: str) -> str:
    """Escape a string for safe use in AppleScript.

    Handles backslashes and double quotes which have special meaning.
    """
    # Escape backslashes first, then quotes
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    return text


def run_applescript(script: str) -> str:
    """Execute AppleScript and return the result.

    Args:
        script: The AppleScript code to execute

    Returns:
        The stdout from the script execution, stripped of whitespace

    Raises:
        AppleScriptPermissionError: If TCC permissions are denied
        AppleScriptExecutionError: If the script fails to execute
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip()

        # Check for TCC permission errors
        if "not allowed" in stderr.lower() or "permission" in stderr.lower():
            raise AppleScriptPermissionError(
                "AppleScript access denied. Please grant automation permission:\n"
                "System Settings > Privacy & Security > Automation > Enable Terminal"
            ) from e

        # Check for Notes-specific errors
        if "notes" in stderr.lower() and "doesn't understand" in stderr.lower():
            raise AppleScriptExecutionError(
                f"Notes app error: {stderr}"
            ) from e

        # Generic error
        raise AppleScriptExecutionError(
            f"AppleScript failed: {stderr}"
        ) from e


def create_note(title: str, body: str, folder: str = "Notes") -> str:
    """Create a new note in the specified folder."""
    title_escaped = escape_for_applescript(title)
    body_escaped = escape_for_applescript(body)
    folder_escaped = escape_for_applescript(folder)

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
    title_escaped = escape_for_applescript(title)
    body_escaped = escape_for_applescript(new_body)

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        set body of theNote to "{body_escaped}"
    end tell
    '''

    return run_applescript(script)


def append_to_note(title: str, content: str) -> str:
    """Append content to an existing note."""
    title_escaped = escape_for_applescript(title)
    content_escaped = escape_for_applescript(content)

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        set body of theNote to (body of theNote) & "{content_escaped}"
    end tell
    '''

    return run_applescript(script)


def delete_note(title: str) -> str:
    """Delete a note by title."""
    title_escaped = escape_for_applescript(title)

    script = f'''
    tell application "Notes"
        delete (first note whose name is "{title_escaped}")
    end tell
    '''

    return run_applescript(script)


def create_folder(name: str) -> str:
    """Create a new folder."""
    name_escaped = escape_for_applescript(name)

    script = f'''
    tell application "Notes"
        make new folder with properties {{name:"{name_escaped}"}}
    end tell
    '''

    return run_applescript(script)


def get_note_body(title: str) -> str:
    """Get the HTML body of a note via AppleScript."""
    title_escaped = escape_for_applescript(title)

    script = f'''
    tell application "Notes"
        set theNote to first note whose name is "{title_escaped}"
        return body of theNote
    end tell
    '''

    return run_applescript(script)
