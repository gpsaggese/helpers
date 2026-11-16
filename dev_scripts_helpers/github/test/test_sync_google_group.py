import os
import unittest.mock as mock
from typing import Dict, List

import pytest

import helpers.hio as hio
import helpers.hunit_test as hunitest

MODULE_PATH = "dev_scripts_helpers.github.sync_google_group"

# Skip this test suite if the dependencies of the `uv` script are not installed.
pytest.importorskip("googleapiclient")
pytest.importorskip("tqdm")
dshgsygogr = pytest.importorskip(
    MODULE_PATH,
    reason="Google client libraries not available; skipping group sync tests.",
)


# #############################################################################
# Test__extract_emails_from_csv
# #############################################################################


class Test__extract_emails_from_csv(hunitest.TestCase):
    """
    Verify that emails are correctly extracted from a CSV file.
    """

    def _create_csv(self, content: str) -> str:
        """
        Create a CSV file in the scratch space.

        :param content: content of the file
        :return: path to the file
        """
        csv_path = os.path.join(self.get_scratch_space(), "users.csv")
        hio.to_file(file_name=csv_path, txt=content)
        return csv_path

    def test_basic(self) -> None:
        # Prepare inputs.
        csv_path = self._create_csv(
            "GitHub user,Email\nalice,Alice@Example.com\nbob,bob@example.com\n"
        )
        # Run test.
        actual = dshgsygogr._extract_emails_from_csv(csv_path, "Email")
        # Check outputs.
        expected = ["alice@example.com", "bob@example.com"]
        self.assertEqual(actual, expected)

    def test_drop_empty_invalid_and_duplicates(self) -> None:
        # Prepare inputs.
        csv_path = self._create_csv(
            "GitHub user,Email\n"
            "alice,alice@example.com\n"
            "bob,\n"
            "carol,not_an_email\n"
            "dave, ALICE@example.com \n"
            "erin,erin@example.com\n"
        )
        # Run test.
        actual = dshgsygogr._extract_emails_from_csv(csv_path, "Email")
        # Check outputs.
        expected = ["alice@example.com", "erin@example.com"]
        self.assertEqual(actual, expected)

    def test_missing_column(self) -> None:
        # Prepare inputs.
        csv_path = self._create_csv("GitHub user\nalice\n")
        # Run test and check outputs.
        with self.assertRaises(AssertionError):
            dshgsygogr._extract_emails_from_csv(csv_path, "Email")


# #############################################################################
# Test__split_emails
# #############################################################################


class Test__split_emails(hunitest.TestCase):
    """
    Test the difference between the passed emails and the group members.
    """

    def test_empty_group(self) -> None:
        # Prepare inputs.
        emails = ["a@x.com", "b@x.com"]
        members: Dict[str, str] = {}
        # Run test.
        actual = dshgsygogr._split_emails(emails, members)
        # Check outputs.
        expected = (["a@x.com", "b@x.com"], [], [], [])
        self.assertEqual(actual, expected)

    def test_mixed(self) -> None:
        # Prepare inputs.
        emails = ["a@x.com", "b@x.com"]
        members = {"b@x.com": "MEMBER", "c@x.com": "MEMBER"}
        # Run test.
        actual = dshgsygogr._split_emails(emails, members)
        # Check outputs.
        expected = (["a@x.com"], ["c@x.com"], ["b@x.com"], [])
        self.assertEqual(actual, expected)

    def test_owner_is_kept(self) -> None:
        """
        Test that an owner that is not in the passed emails is not removed.
        """
        # Prepare inputs.
        emails = ["a@x.com"]
        members = {"boss@x.com": "OWNER", "c@x.com": "MANAGER"}
        # Run test.
        actual = dshgsygogr._split_emails(emails, members)
        # Check outputs.
        expected = (["a@x.com"], ["c@x.com"], [], ["boss@x.com"])
        self.assertEqual(actual, expected)

    def test_duplicates(self) -> None:
        # Prepare inputs.
        emails = ["a@x.com", "a@x.com"]
        members: Dict[str, str] = {}
        # Run test.
        actual = dshgsygogr._split_emails(emails, members)
        # Check outputs.
        expected = (["a@x.com"], [], [], [])
        self.assertEqual(actual, expected)


# #############################################################################
# Test_sync_google_group
# #############################################################################


class Test_sync_google_group(hunitest.TestCase):
    """
    Test that the group is created and its members are synced.
    """

    def _run(
        self,
        emails: List[str],
        *,
        group_exists: bool,
        members: Dict[str, str],
        remove_extra: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, mock.Mock]:
        """
        Run `sync_google_group()` with a mocked Directory API.

        :param emails: emails that must be in the group
        :param group_exists: whether the group already exists
        :param members: map from email to role of the current members
        :return: the mocked functions that change the group
        """
        group_email = "team@example.com"
        with (
            mock.patch(f"{MODULE_PATH}._get_directory_service"),
            mock.patch(
                f"{MODULE_PATH}._group_exists", return_value=group_exists
            ),
            mock.patch(f"{MODULE_PATH}._get_members", return_value=members),
            mock.patch(f"{MODULE_PATH}._create_group") as m_create,
            mock.patch(f"{MODULE_PATH}._add_member") as m_add,
            mock.patch(f"{MODULE_PATH}._remove_member") as m_remove,
        ):
            dshgsygogr.sync_google_group(
                emails,
                group_email,
                "admin@example.com",
                remove_extra=remove_extra,
                dry_run=dry_run,
            )
        return {"create": m_create, "add": m_add, "remove": m_remove}

    def test_create_group(self) -> None:
        # Run test.
        m = self._run(["a@x.com", "b@x.com"], group_exists=False, members={})
        # Check outputs.
        self.assertEqual(m["create"].call_count, 1)
        self.assertEqual(
            [call.args[2] for call in m["add"].call_args_list],
            ["a@x.com", "b@x.com"],
        )
        m["remove"].assert_not_called()

    def test_sync_existing_group(self) -> None:
        # Prepare inputs.
        members = {"b@x.com": "MEMBER", "c@x.com": "MEMBER"}
        # Run test.
        m = self._run(["a@x.com", "b@x.com"], group_exists=True, members=members)
        # Check outputs.
        m["create"].assert_not_called()
        self.assertEqual(
            [call.args[2] for call in m["add"].call_args_list], ["a@x.com"]
        )
        self.assertEqual(
            [call.args[2] for call in m["remove"].call_args_list], ["c@x.com"]
        )

    def test_no_remove_extra(self) -> None:
        # Prepare inputs.
        members = {"c@x.com": "MEMBER"}
        # Run test.
        m = self._run(
            ["a@x.com"], group_exists=True, members=members, remove_extra=False
        )
        # Check outputs.
        self.assertEqual(m["add"].call_count, 1)
        m["remove"].assert_not_called()

    def test_owner_is_not_removed(self) -> None:
        # Prepare inputs.
        members = {"boss@x.com": "OWNER"}
        # Run test.
        m = self._run(["a@x.com"], group_exists=True, members=members)
        # Check outputs.
        m["remove"].assert_not_called()

    def test_dry_run(self) -> None:
        """
        Test that nothing is changed in a dry run.
        """
        # Prepare inputs.
        members = {"c@x.com": "MEMBER"}
        # Run test.
        m = self._run(
            ["a@x.com"], group_exists=False, members=members, dry_run=True
        )
        # Check outputs.
        m["create"].assert_not_called()
        m["add"].assert_not_called()
        m["remove"].assert_not_called()


# #############################################################################
# Test__parse
# #############################################################################


class Test__parse(hunitest.TestCase):
    """
    Test the command line options.
    """

    def test_defaults(self) -> None:
        # Prepare inputs.
        argv = [
            "--csv_file",
            "/tmp/github_users.csv",
            "--admin_email",
            "admin@example.com",
        ]
        # Run test.
        args = dshgsygogr._parse().parse_args(argv)
        # Check outputs.
        self.assert_equal(args.csv_file, "/tmp/github_users.csv")
        self.assert_equal(args.email_column, "Email")
        self.assert_equal(args.group_email, "gp_umd_ai_research@causify.ai")
        self.assertTrue(args.remove_extra)
        self.assertFalse(args.dry_run)

    def test_no_remove_extra(self) -> None:
        # Prepare inputs.
        argv = [
            "--csv_file",
            "users.csv",
            "--admin_email",
            "admin@example.com",
            "--no_remove_extra",
        ]
        # Run test.
        args = dshgsygogr._parse().parse_args(argv)
        # Check outputs.
        self.assertFalse(args.remove_extra)

    def test_csv_file_is_required(self) -> None:
        # Prepare inputs.
        argv = ["--admin_email", "admin@example.com"]
        # Run test and check outputs.
        with self.assertRaises(SystemExit):
            dshgsygogr._parse().parse_args(argv)


# #############################################################################
# Test__main
# #############################################################################


class Test__main(hunitest.TestCase):
    """
    Test that `_main()` passes the emails of the CSV to the sync.
    """

    def test_main(self) -> None:
        # Prepare inputs.
        csv_path = os.path.join(self.get_scratch_space(), "users.csv")
        hio.to_file(file_name=csv_path, txt="Email\nAlice@x.com\n\n")
        argv = [
            "sync_google_group.py",
            "--csv_file",
            csv_path,
            "--admin_email",
            "admin@example.com",
            "--group_email",
            "team@example.com",
            "--dry_run",
        ]
        parser = dshgsygogr._parse()
        # Run test.
        with (
            mock.patch("sys.argv", argv),
            mock.patch(f"{MODULE_PATH}.hdbg.init_logger"),
            mock.patch(f"{MODULE_PATH}.sync_google_group") as m_sync,
        ):
            dshgsygogr._main(parser)
        # Check outputs.
        m_sync.assert_called_once_with(
            ["alice@x.com"],
            "team@example.com",
            "admin@example.com",
            remove_extra=True,
            dry_run=True,
        )
