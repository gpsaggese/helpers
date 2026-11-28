import logging
import os

import helpers.hio as hio
import helpers.hprint as hprint
import helpers.hunit_test as hunitest

import dev_scripts_helpers.google.gws_download_doc as dshggwdodo

_LOG = logging.getLogger(__name__)


# #############################################################################
# Test__run_gws
# #############################################################################


class Test__run_gws(hunitest.TestCase):
    """
    Test `gws_download_doc._run_gws()`.
    """

    def test1(self) -> None:
        """
        Test that the output of a successful command is returned.
        """
        # Prepare inputs.
        cmd = "echo hello"
        # Prepare outputs.
        expected = "hello"
        # Run test.
        actual = dshggwdodo._run_gws(cmd)
        # Check outputs.
        self.assert_equal(actual.strip(), expected)

    def test2(self) -> None:
        """
        Test that an authorization error asks to run `gws auth login`.
        """
        # Prepare inputs.
        cmd = """echo '{"reason": "authError"}'; exit 1"""
        # Prepare outputs.
        expected = "please run: gws auth login"
        # Run test.
        with self.assertRaises(PermissionError) as cm:
            dshggwdodo._run_gws(cmd)
        # Check outputs.
        self.assertIn(expected, str(cm.exception))


# #############################################################################
# Test__extract_images
# #############################################################################


class Test__extract_images(hunitest.TestCase):
    """
    Test `gws_download_doc._extract_images()`.
    """

    def helper(self, file_name: str, txt: str, expected: str) -> str:
        """
        Run `_extract_images()` on a Markdown file and check its content.

        :param file_name: name of the Markdown file to create
        :param txt: content of the Markdown file
        :param expected: expected content after the extraction
        :return: dir storing the Markdown file
        """
        # Prepare inputs.
        scratch_dir = self.get_scratch_space()
        md_file = os.path.join(scratch_dir, file_name)
        hio.to_file(md_file, hprint.dedent(txt))
        # Run test.
        dshggwdodo._extract_images(md_file)
        # Check outputs.
        actual = hio.from_file(md_file)
        self.assert_equal(actual, hprint.dedent(expected))
        return scratch_dir

    def test1(self) -> None:
        """
        Test that images of different types are saved and links updated.
        """
        # Prepare inputs.
        file_name = "doc.md"
        # "aGVsbG8=" and "d29ybGQ=" are "hello" and "world" in base64.
        txt = """
        ![][image1]
        ![][image2]

        [image1]: <data:image/png;base64,aGVsbG8=>
        [image2]: <data:image/jpeg;base64,d29ybGQ=>
        """
        # Prepare outputs.
        expected = """
        ![][image1]
        ![][image2]

        [image1]: <doc.figs/image1.png>
        [image2]: <doc.figs/image2.jpg>
        """
        # Run test.
        scratch_dir = self.helper(file_name, txt, expected)
        # Check outputs.
        figs_dir = os.path.join(scratch_dir, "doc.figs")
        with open(os.path.join(figs_dir, "image1.png"), "rb") as f:
            self.assertEqual(f.read(), b"hello")
        with open(os.path.join(figs_dir, "image2.jpg"), "rb") as f:
            self.assertEqual(f.read(), b"world")

    def test2(self) -> None:
        """
        Test that a file without images is unchanged and no dir is created.
        """
        # Prepare inputs.
        file_name = "doc.md"
        txt = """
        # Title

        [link]: <https://example.com>
        """
        # Prepare outputs.
        expected = txt
        # Run test.
        scratch_dir = self.helper(file_name, txt, expected)
        # Check outputs.
        figs_dir = os.path.join(scratch_dir, "doc.figs")
        self.assertFalse(os.path.exists(figs_dir))
