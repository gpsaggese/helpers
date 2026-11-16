#!/usr/bin/env -S uv run

# /// script
# dependencies = [
#   "google-api-python-client",
#   "google-auth",
#   "gspread",
#   "pandas",
#   "pyyaml",
#   "tqdm",
# ]
# ///

"""
Create or update a Google Group in a Google Workspace domain so that its members
are the emails listed in a CSV file.

By default the group is synced to the CSV:
- the group is created if it does not exist
- the emails in the CSV that are not in the group are added
- the members of the group that are not in the CSV are removed (use
  `--no_remove_extra` to only add), except the members with the `OWNER` role

Consumer groups (`@googlegroups.com`) have no public API, so the group must be in
a Google Workspace domain. The script calls the Admin SDK Directory API and needs:
- The Admin SDK API enabled in the Google Cloud project of the service account
- The scopes `admin.directory.group` and `admin.directory.group.member` granted to
  the service account with domain-wide delegation in the Workspace admin console
- A Workspace admin email passed with `--admin_email`, impersonated by the
  service account

The service account key is read from
`~/.config/gspread_pandas/google_secret.json`.

If the group was just created, Google can take a few minutes before accepting
members: rerun the script, which is idempotent, if some additions fail.

# Usage Example

- Sync the group with the emails in the `Email` column of a CSV file:
> sync_google_group.py \
    --csv_file "/tmp/github_users.csv" \
    --admin_email admin@example.com

- Sync the group `gp_umd_ai_research@example.com` using a different column:
> sync_google_group.py \
    --csv_file "/tmp/github_users.csv" \
    --email_column "Email address" \
    --group_email gp_umd_ai_research@example.com \
    --admin_email admin@example.com

- Add the missing members without removing anyone:
> sync_google_group.py \
    --csv_file "/tmp/github_users.csv" \
    --admin_email admin@example.com \
    --no_remove_extra

- Show who would be added and removed, without changing the group:
> sync_google_group.py \
    --csv_file "/tmp/github_users.csv" \
    --admin_email admin@example.com \
    --dry_run

Import as:

import dev_scripts_helpers.github.sync_google_group as dshgsygogr
"""

import argparse
import csv
import logging
import re
from typing import Dict, List, Tuple

import googleapiclient.discovery as godisc
import googleapiclient.errors as goerr
import tqdm

import helpers.hdbg as hdbg
import helpers.hgoogle_drive_api as hgodrapi
import helpers.hparser as hparser
import helpers.hprint as hprint

_LOG = logging.getLogger(__name__)

# Role of a member of a group that is never removed by the sync.
_OWNER_ROLE = "OWNER"


# #############################################################################
# CSV
# #############################################################################


def _extract_emails_from_csv(csv_path: str, email_column: str) -> List[str]:
    """
    Extract the emails from a CSV file containing a column with the emails.

    Emails are stripped and lowercased, since Google Groups treats them as
    case-insensitive. Empty cells, invalid emails and duplicates are dropped,
    keeping the order of the file.

    :param csv_path: path to csv
    :param email_column: name of the column storing the emails
    :return: emails
    """
    _LOG.debug(hprint.to_str("csv_path email_column"))
    # Read the column.
    raw_emails: List[str] = []
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        hdbg.dassert_in(
            email_column,
            reader.fieldnames,
            "CSV is missing the email column",
        )
        for row in reader:
            raw_emails.append(row[email_column])
    # Normalize the emails.
    emails: List[str] = []
    for raw_email in raw_emails:
        email = (raw_email or "").strip().lower()
        if not email:
            continue
        # A valid email has one `@` and a dot in the domain.
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            _LOG.warning("Skipping invalid email '%s'", email)
            continue
        emails.append(email)
    # Drop duplicates keeping the order.
    emails = list(dict.fromkeys(emails))
    _LOG.info("Emails (CSV) = %d", len(emails))
    _LOG.debug("return=%s", emails)
    return emails


# #############################################################################
# Diff between the CSV and the group
# #############################################################################


def _split_emails(
    emails: List[str], members: Dict[str, str]
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """
    Compare the passed emails with the members of a group.

    The members with the `OWNER` role are never in the users to remove, so that
    the sync cannot lock the owners out of the group.

    :param emails: lowercase emails that must be in the group
    :param members: map from the lowercase email of each member of the group to
        its role
    :return: emails to add, members to remove, emails already in the group,
        owners that are not in the passed emails (and are kept)
    """
    _LOG.debug(hprint.to_str("emails members"))
    unique_emails = list(dict.fromkeys(emails))
    to_add = [email for email in unique_emails if email not in members]
    already_members = [email for email in unique_emails if email in members]
    extra = [email for email in members if email not in unique_emails]
    to_remove = [email for email in extra if members[email] != _OWNER_ROLE]
    kept_owners = [email for email in extra if members[email] == _OWNER_ROLE]
    return to_add, to_remove, already_members, kept_owners


# #############################################################################
# Google Directory API
# #############################################################################


def _get_directory_service(admin_email: str) -> "godisc.Resource":
    """
    Get the Admin SDK Directory service impersonating a Workspace admin.

    :param admin_email: email of the Workspace admin to impersonate
    :return: Directory API service
    """
    _LOG.debug(hprint.to_str("admin_email"))
    scopes = [
        "https://www.googleapis.com/auth/admin.directory.group",
        "https://www.googleapis.com/auth/admin.directory.group.member",
    ]
    # Reuse the service account key, but with the scopes of the Directory API
    # and acting on behalf of the admin (domain-wide delegation).
    credentials = hgodrapi.get_credentials()
    credentials = credentials.with_scopes(scopes)
    credentials = credentials.with_subject(admin_email)
    service = godisc.build(
        "admin", "directory_v1", credentials=credentials, cache_discovery=False
    )
    return service


def _group_exists(service: "godisc.Resource", group_email: str) -> bool:
    """
    Check if a group exists in the domain of its email.

    :param service: Directory API service
    :param group_email: email of the group
    :return: whether the group exists
    """
    _LOG.debug(hprint.to_str("group_email"))
    domain = group_email.split("@")[1]
    group_emails = set()
    page_token = None
    # List all the groups of the domain, since a `get` of a missing group raises.
    while True:
        response = (
            service.groups()
            .list(domain=domain, maxResults=200, pageToken=page_token)
            .execute()
        )
        for group in response.get("groups", []):
            group_emails.add(group["email"].lower())
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    exists = group_email.lower() in group_emails
    _LOG.debug("return=%s", exists)
    return exists


def _create_group(service: "godisc.Resource", group_email: str) -> None:
    """
    Create a group.

    :param service: Directory API service
    :param group_email: email of the group, whose local part is used as name
    """
    _LOG.debug(hprint.to_str("group_email"))
    body = {"email": group_email, "name": group_email.split("@")[0]}
    service.groups().insert(body=body).execute()
    _LOG.info("Created group '%s'", group_email)


def _get_members(service: "godisc.Resource", group_email: str) -> Dict[str, str]:
    """
    Get the members of a group.

    :param service: Directory API service
    :param group_email: email of the group
    :return: map from the lowercase email of each member to its role
    """
    _LOG.debug(hprint.to_str("group_email"))
    members: Dict[str, str] = {}
    page_token = None
    while True:
        response = (
            service.members()
            .list(groupKey=group_email, maxResults=200, pageToken=page_token)
            .execute()
        )
        for member in response.get("members", []):
            members[member["email"].lower()] = member["role"]
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    _LOG.debug("return=%s", members)
    return members


def _add_member(
    service: "godisc.Resource", group_email: str, email: str
) -> None:
    """
    Add a member with the `MEMBER` role to a group.

    :param service: Directory API service
    :param group_email: email of the group
    :param email: email of the member to add
    """
    body = {"email": email, "role": "MEMBER"}
    service.members().insert(groupKey=group_email, body=body).execute()
    _LOG.info("Added '%s' to '%s'", email, group_email)


def _remove_member(
    service: "godisc.Resource", group_email: str, email: str
) -> None:
    """
    Remove a member from a group.

    :param service: Directory API service
    :param group_email: email of the group
    :param email: email of the member to remove
    """
    service.members().delete(groupKey=group_email, memberKey=email).execute()
    _LOG.info("Removed '%s' from '%s'", email, group_email)


# #############################################################################
# Sync
# #############################################################################


def sync_google_group(
    emails: List[str],
    group_email: str,
    admin_email: str,
    *,
    remove_extra: bool,
    dry_run: bool,
) -> None:
    """
    Create a Google Group if missing and sync its members with the passed emails.

    :param emails: lowercase emails that must be in the group
    :param group_email: email of the group (e.g., `team@example.com`)
    :param admin_email: email of the Workspace admin to impersonate
    :param remove_extra: remove the members that are not in `emails` (the owners
        are never removed)
    :param dry_run: report what would be done without changing the group
    """
    _LOG.debug(hprint.to_str("group_email admin_email remove_extra dry_run"))
    hdbg.dassert_in("@", group_email, "Group needs to be an email address")
    service = _get_directory_service(admin_email)
    # Compute the difference between the passed emails and the group members.
    group_exists = _group_exists(service, group_email)
    if group_exists:
        members = _get_members(service, group_email)
    else:
        members = {}
    to_add, to_remove, already_members, kept_owners = _split_emails(
        emails, members
    )
    if not remove_extra:
        to_remove = []
    _LOG.info("Group exists: %s", group_exists)
    _LOG.info("Already members: %d", len(already_members))
    _LOG.info("To add: %s", to_add)
    _LOG.info("To remove: %s", to_remove)
    if kept_owners:
        _LOG.warning("Owners not in the CSV are kept: %s", kept_owners)
    # Create the group.
    if not group_exists:
        if dry_run:
            _LOG.warning("[DRY_RUN] Would create group '%s'", group_email)
        else:
            _create_group(service, group_email)
    # Add the missing members.
    for email in tqdm.tqdm(to_add, desc="Adding members"):
        if dry_run:
            _LOG.warning("[DRY_RUN] Would add '%s' to '%s'", email, group_email)
        else:
            try:
                _add_member(service, group_email, email)
            except goerr.HttpError as exc:
                _LOG.error("Failed to add '%s': %s", email, exc.reason)
    # Remove the members that are not in the CSV.
    for email in tqdm.tqdm(to_remove, desc="Removing members"):
        if dry_run:
            _LOG.warning(
                "[DRY_RUN] Would remove '%s' from '%s'", email, group_email
            )
        else:
            try:
                _remove_member(service, group_email, email)
            except goerr.HttpError as exc:
                _LOG.error("Failed to remove '%s': %s", email, exc.reason)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    parser.add_argument(
        "--csv_file",
        required=True,
        help="Path to CSV file containing a column with the emails of the members",
    )
    parser.add_argument(
        "--email_column",
        default="Email",
        help="Name of the CSV column with the emails",
    )
    parser.add_argument(
        "--group_email",
        default="gp_umd_ai_research@causify.ai",
        help="Email of the Google Group in a Google Workspace domain",
    )
    parser.add_argument(
        "--admin_email",
        required=True,
        help="Email of the Workspace admin impersonated by the service account",
    )
    hparser.add_bool_arg(
        parser,
        "remove_extra",
        default_value=True,
        help_="Remove the members of the group that are not in the CSV (the owners are never removed)",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    emails = _extract_emails_from_csv(args.csv_file, args.email_column)
    hdbg.dassert_lte(1, len(emails), "No valid email found in the CSV")
    sync_google_group(
        emails,
        args.group_email,
        args.admin_email,
        remove_extra=args.remove_extra,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
