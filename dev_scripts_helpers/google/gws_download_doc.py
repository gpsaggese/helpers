#!/usr/bin/env python

r"""
Download Google Docs using gws (Google Workspace CLI).

This script downloads a Google Doc from a URL and saves it to a specified file
path. The output format is automatically detected from the file extension.

Supported formats (inferred from output file extension):
- .pdf: PDF format
- .docx: Microsoft Word format
- .odt: OpenDocument format
- .rtf: Rich Text format
- .txt: Plain text format
- .html: HTML format
- .md: Markdown format
- .epub: EPUB format
- .zip: ZIP format (for web archive)

Prerequisites:
- gws CLI tool installed: https://github.com/googleworkspace/cli
- gws authentication configured (run 'gws auth login' if not authenticated)

# Usage Example

- Download a Google Doc as PDF to an explicit file path:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_file document.pdf

- Download a Google Doc as a Word document:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_file document.docx

- Download a Google Doc as Markdown:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_file document.md

- Download a Google Doc as Markdown and save its images in `document.figs/`:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_file document.md --extract_images

- Download a Google Doc and auto-generate the filename from the document name:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_dir ./output

- Download a Google Doc and auto-generate the filename with a specific extension:
> gws_download_doc.py --from_url https://docs.google.com/document/d/ABC123/edit \
    --to_dir ./output --extension docx
"""

import argparse
import base64
import json
import logging
import os
import re
import string

import helpers.hdbg as hdbg
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Mapping of file extensions to gws drive files export MIME types.
_FORMAT_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "odt": "application/vnd.oasis.opendocument.text",
    "rtf": "application/rtf",
    "txt": "text/plain",
    "html": "text/html",
    "md": "text/markdown",
    "epub": "application/epub+zip",
    "zip": "application/zip",
}

# #############################################################################
# Helper functions
# #############################################################################


def _extract_doc_id(url: str) -> str:
    """
    Extract Google Docs document ID from a URL.

    :param url: Google Docs URL
    :return: document ID
    """
    # Pattern to match Google Docs URLs.
    pattern = r"/document/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    hdbg.dassert_is_not(
        match,
        None,
        "Invalid Google Docs URL format; expected /document/d/{ID}:",
        url,
    )
    doc_id = match.group(1)  # type: ignore
    return doc_id


def _get_format_from_suffix(file_path: str) -> str:
    """
    Get export format from file extension.

    :param file_path: output file path
    :return: MIME type for gws export
    """
    # Get file extension without the dot.
    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip(".").lower()
    hdbg.dassert_in(
        ext,
        _FORMAT_MAP,
        "Unsupported file format; supported formats are: %s",
        ", ".join(_FORMAT_MAP.keys()),
    )
    mime_type = _FORMAT_MAP[ext]
    return mime_type


def _sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by replacing non-bash-friendly characters with underscores.

    :param filename: original filename
    :return: sanitized filename
    """
    # Keep only alphanumeric characters, dots, and hyphens.
    # Replace everything else (spaces, special chars, etc) with underscores.
    allowed_chars = set(string.ascii_letters + string.digits + ".-")
    sanitized = ""
    for char in filename:
        if char in allowed_chars:
            sanitized += char
        else:
            sanitized += "_"
    # Replace multiple consecutive underscores with single underscore.
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    # Remove leading/trailing underscores.
    sanitized = sanitized.strip("_")
    return sanitized


def _run_gws(cmd: str) -> str:
    """
    Run a `gws` command, asking to log in again on an authorization error.

    :param cmd: `gws` command to run
    :return: output of the command
    """
    _LOG.debug(hprint.to_str("cmd"))
    rc, output = hsystem.system_to_string(cmd, abort_on_error=False)
    # `gws auth status` can succeed with an expired session, so the error can
    # show up only when calling the API.
    if rc != 0 and '"authError"' in output:
        raise PermissionError(
            f"{output}\ngws authorization failed; please run: gws auth login"
        )
    hdbg.dassert_eq(rc, 0, "gws command failed:\n%s", output)
    return output


def _get_document_name(doc_id: str) -> str:
    """
    Get the document name from Google Drive metadata.

    :param doc_id: Google Docs document ID
    :return: document name
    """
    _LOG.debug("Fetching document metadata for ID: %s", doc_id)
    # Build params to fetch metadata.
    params = {
        "fileId": doc_id,
        "fields": "name",
    }
    params_json = json.dumps(params)
    # Use gws drive files get to fetch metadata.
    cmd = f"gws drive files get --params '{params_json}'"
    output = _run_gws(cmd)
    # Parse JSON output to extract name.
    try:
        metadata = json.loads(output)
        doc_name = metadata.get("name", "document")
    except json.JSONDecodeError:
        _LOG.warning("Failed to parse document metadata; using default name")
        doc_name = "document"
    _LOG.info("Document name: %s", doc_name)
    return doc_name


def _check_gws_authentication() -> None:
    """
    Check if gws is authenticated.

    If not authenticated, log an error and abort with instructions.
    """
    _LOG.debug("Checking gws authentication")
    rc = hsystem.system(
        "gws auth status", suppress_output=True, abort_on_error=False
    )
    hdbg.dassert_eq(
        rc, 0, "gws is not authenticated; please run: gws auth login"
    )
    _LOG.debug("gws authentication verified")


def _download_doc(doc_id: str, mime_type: str, output_file: str) -> None:
    """
    Download Google Doc using gws drive files export command.

    :param doc_id: Google Docs document ID
    :param mime_type: MIME type for export format
    :param output_file: path to save downloaded file
    """
    _LOG.info("Downloading document %s to %s", doc_id, output_file)
    # Build params JSON.
    params = {
        "fileId": doc_id,
        "mimeType": mime_type,
    }
    params_json = json.dumps(params)
    # Build gws command.
    cmd = (
        f"gws drive files export --params '{params_json}' --output {output_file}"
    )
    _run_gws(cmd)
    _LOG.info("Document successfully saved to: %s", output_file)


def _extract_images(md_file: str) -> None:
    """
    Save the images embedded in a Markdown file as separate files.

    Google exports each image as a base64 reference definition, e.g.,
    ```
    [image1]: <data:image/png;base64,iVBORw0KGgo...>
    ```
    The image is saved in a `<name>.figs` dir next to `<name>.md` and the
    definition is updated to point to it:
    ```
    [image1]: <name.figs/image1.png>
    ```

    :param md_file: path to the Markdown file, modified in place
    """
    _LOG.debug(hprint.to_str("md_file"))
    figs_dir = os.path.splitext(md_file)[0] + ".figs"
    # Match the reference definition of an embedded image.
    image_def_re = re.compile(
        r"""
        ^\[(?P<label>[\w-]+)\]:[ \t]*       # `[image1]: `
        <?data:image/(?P<type>[\w.+-]+);     # `<data:image/png;`
        base64,(?P<data>[A-Za-z0-9+/=]+)>?  # `base64,iVBOR...>`
        [ \t]*$
        """,
        re.MULTILINE | re.VERBOSE,
    )

    def _save_image(match: re.Match) -> str:
        """
        Save one image and return the updated reference definition.
        """
        label = match.group("label")
        image_type = match.group("type")
        # Map the MIME subtypes that differ from the usual file extension.
        ext = {"jpeg": "jpg", "svg+xml": "svg"}.get(image_type, image_type)
        file_name = f"{label}.{ext}"
        hio.create_dir(figs_dir, incremental=True)
        with open(os.path.join(figs_dir, file_name), "wb") as f:
            f.write(base64.b64decode(match.group("data")))
        # The link is relative to the dir of the Markdown file.
        link = f"{os.path.basename(figs_dir)}/{file_name}"
        return f"[{label}]: <{link}>"

    txt = hio.from_file(md_file)
    txt, num_images = image_def_re.subn(_save_image, txt)
    if num_images:
        hio.to_file(md_file, txt)
        _LOG.info("Saved %d images in '%s'", num_images, figs_dir)
    else:
        _LOG.info("No embedded images found in '%s'", md_file)


def _main(parser: argparse.ArgumentParser) -> None:
    """
    Execute the script workflow.
    """
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    _LOG.info("Starting Google Docs download")
    # Check gws authentication.
    _check_gws_authentication()
    # Validate and extract document ID from URL.
    doc_id = _extract_doc_id(args.from_url)
    _LOG.info("Extracted document ID: %s", doc_id)
    # Determine output file path.
    if args.to_file:
        output_file = args.to_file
    else:
        # Get document name and sanitize it.
        doc_name = _get_document_name(doc_id)
        sanitized_name = _sanitize_filename(doc_name)
        # Use extension or default to .md.
        ext = args.extension or "md"
        if not ext.startswith("."):
            ext = f".{ext}"
        filename = f"{sanitized_name}{ext}"
        output_file = os.path.join(args.to_dir, filename)
        _LOG.info("Output filename: %s", filename)
    # Get export format from file extension.
    mime_type = _get_format_from_suffix(output_file)
    _LOG.info("Exporting as format: %s", mime_type)
    if args.extract_images:
        hdbg.dassert_eq(
            mime_type,
            _FORMAT_MAP["md"],
            "--extract_images requires a Markdown output file",
        )
    # Create parent directories if needed.
    parent_dir = os.path.dirname(output_file)
    if parent_dir:
        hio.create_dir(parent_dir, incremental=True)
    # Download the document.
    _download_doc(doc_id, mime_type, output_file)
    if args.extract_images:
        _extract_images(output_file)
    _LOG.info("Download complete")


def _parse() -> argparse.ArgumentParser:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--from_url",
        action="store",
        required=True,
        help="Google Docs URL to download from",
    )
    # Create mutually exclusive group for output options.
    output_group = parser.add_mutually_exclusive_group(required=True)
    output_group.add_argument(
        "--to_file",
        action="store",
        help="Output file path (format inferred from extension)",
    )
    output_group.add_argument(
        "--to_dir",
        action="store",
        help="Output directory (filename derived from document name)",
    )
    parser.add_argument(
        "--extension",
        action="store",
        default="md",
        help="File extension when using --to_dir (default: md)",
    )
    parser.add_argument(
        "--extract_images",
        action="store_true",
        help="Save the images of a Markdown export in a '<name>.figs' dir",
    )
    hparser.add_verbosity_arg(parser)
    return parser


if __name__ == "__main__":
    _main(_parse())
