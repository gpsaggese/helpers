#!/usr/bin/env python

r"""
Typeset the differences of a LaTeX paper between two git commits.

The PDF shows deleted text struck through in red and added text underlined in
blue. A changed figure is shown twice: the old one crossed out in red and the
new one framed in blue.

The versions to compare are specified with `--from_ref` (and optionally
`--to_ref`) or with one of these aliases, like in `i git_files`:
- `-l, --last_commit`: from `HEAD~1` to `HEAD`
- `-m, --modified`: from `HEAD` to the uncommitted (staged and unstaged) changes
  of the tracked files
- `-b, --branch`: from the tip of `origin/master` to `HEAD`
- `-n, --branch_point`: from where the branch diverged from `origin/master` to
  `HEAD`

The script:
- exports each commit (including submodules) into `tmp.diff_latex/` at the root
  of the repo, without changing the sources in the working tree
- renders the diagrams of each snapshot with `render_images.py` (Docker)
- merges the `\input` / `\include` files of each snapshot with `latexpand`
- names each image after its content, since `latexdiff` compares only the text
  and so it needs a different file name to detect a changed image
- limits the height of the changed figures, so that the old and the new version
  fit in a page
- marks up the changes with `latexdiff --graphics-markup=both`
- compiles the result with `latexmk`
- if the compilation fails, retries with less detailed markup:
  - `--math-markup=off`, which doesn't mark the changes in the equations
  - `--exclude-textcmd=textbf`, which doesn't mark the changes in the bold text,
    and can hide the deleted bold text
  - both options together
- deletes `tmp.diff_latex/` after a successful compilation, since its copies of
  the files of the repo break the tools that search files by name. A run that
  fails or skips `compile` keeps it, so it needs to be deleted by hand

With `--fast` the script trades accuracy for speed:
- it skips `render_images.py`, so an image that is not committed is replaced by
  an "Image not rendered" box
- it runs a single `pdflatex` pass instead of `latexmk`, so cross-references,
  citations, and the bibliography are not resolved

Only images included with `\includegraphics` are compared (e.g., not inline
TikZ drawings).

`latexpand`, `latexdiff`, and `latexmk` are part of MacTeX. `latexdiff
--flatten` is not used since it fails on macros like `\\input{#2}`.

Paths in `\input` are resolved from the root of the repo, as `run_latex.py`
does. Untracked files and uncommitted changes in submodules are never compared.

For a description of this file, see the file diff_latex.README.md

# Usage Example

- Show the changes of the last commit:
> diff_latex.py --input papers/Noesis/paper.tex -l

- Show the uncommitted changes:
> diff_latex.py --input papers/Noesis/paper.tex -m

- Show the changes of the branch since it diverged from `origin/master`:
> diff_latex.py --input papers/Noesis/paper.tex -n

- Compare a commit with `HEAD`:
> diff_latex.py --input papers/Noesis/paper.tex --from_ref HEAD~5

- Compare two commits and choose the output file:
> diff_latex.py --input papers/Noesis/paper.tex --from_ref 54845e3a \
    --to_ref d9d993ea --output Noesis.diff.pdf

- Generate a quick draft of the diff:
> diff_latex.py --input papers/Noesis/paper.tex -m --fast

- Generate only the `.tex` diff, without Docker:
> diff_latex.py --input papers/Noesis/paper.tex --from_ref HEAD~5 \
    --skip_action render_images --skip_action compile

Import as:

import dev_scripts_helpers.documentation.diff_latex as dshddila
"""

import argparse
import glob
import hashlib
import logging
import os
import re
import shlex
import shutil
import tempfile
from typing import List, Set, Tuple

import helpers.hdbg as hdbg
import helpers.hgit as hgit
import helpers.hio as hio
import helpers.hparser as hparser
import helpers.hprint as hprint
import helpers.hselect_action as hselacti
import helpers.hselect_input_output as hseinout
import helpers.hsystem as hsystem

_LOG = logging.getLogger(__name__)

# Match `\includegraphics[<options>]{<path>}`, where the options are optional.
_INCLUDEGRAPHICS_RE = re.compile(
    r"""
    \\includegraphics(?P<star>\*?)\s*
    (?:\[(?P<opts>[^\]]*)\]\s*)?    # Options.
    \{(?P<path>[^}]*)\}             # Path, possibly on its own line.
    """,
    re.VERBOSE,
)

# #############################################################################
# Actions
# #############################################################################

_VALID_ACTIONS = [
    "render_images",
    "compile",
]
_DEFAULT_ACTIONS = _VALID_ACTIONS[:]

# #############################################################################
# Git snapshots
# #############################################################################


def _select_refs(
    repo_dir: str,
    from_ref: str,
    to_ref: str,
    alias: str,
    *,
    dry_run: bool = False,
) -> Tuple[str, str]:
    """
    Find the two versions to compare.

    :param repo_dir: root of the git repo
    :param from_ref: old commit, used when there is no alias
    :param to_ref: new commit, used when there is no alias (empty for `HEAD`)
    :param alias: empty, `last_commit`, `modified`, `branch`, or `branch_point`
    :param dry_run: don't create the commit with the uncommitted changes
    :return: old and new commit
    """
    _LOG.debug(hprint.func_signature_to_str())
    git = f"git -C {shlex.quote(repo_dir)}"
    if alias == "last_commit":
        from_ref, to_ref = "HEAD~1", "HEAD"
    elif alias == "modified":
        from_ref = "HEAD"
        if dry_run:
            to_ref = "<uncommitted changes>"
        else:
            # Create a commit with the staged and unstaged changes, without
            # modifying the working tree or the stash list.
            _, to_ref = hsystem.system_to_string(f"{git} stash create")
            to_ref = to_ref.strip()
            hdbg.dassert_ne(to_ref, "", "There are no uncommitted changes")
    elif alias == "branch":
        from_ref, to_ref = "origin/master", "HEAD"
    elif alias == "branch_point":
        cmd = f"{git} merge-base origin/master HEAD"
        _, from_ref = hsystem.system_to_one_line(cmd)
        to_ref = "HEAD"
    else:
        hdbg.dassert_eq(alias, "", "Invalid alias")
        to_ref = to_ref or "HEAD"
    return from_ref, to_ref


def _list_files(repo_dir: str, ref: str) -> List[List[str]]:
    """
    List the entries of a commit.

    :param repo_dir: root of the git repo
    :param ref: commit to list
    :return: list of `[type, sha, path]`, where `type` is `blob` for a file and
        `commit` for a submodule
    """
    cmd = f"git -C {shlex.quote(repo_dir)} ls-tree -r -z --full-tree {ref}"
    _, txt = hsystem.system_to_string(cmd)
    entries = []
    for record in txt.split("\0"):
        if record.strip():
            # Each record is `<mode> <type> <sha>\t<path>`.
            info, path = record.split("\t", 1)
            _, type_, sha = info.split()
            entries.append([type_, sha, path])
    return entries


def _export_commit(
    repo_dir: str,
    ref: str,
    dst_dir: str,
    paper_dir: str,
) -> None:
    """
    Export the files of a commit needed to build a paper.

    The repo can be large, so only the LaTeX support files and the content of
    the paper dir are exported. Submodules are exported at the commit recorded
    in `ref`.

    :param repo_dir: root of the git repo
    :param ref: commit to export
    :param dst_dir: dir where to export the files
    :param paper_dir: dir of the paper, relative to `repo_dir` (empty for the
        root)
    """
    latex_exts = (".tex", ".sty", ".cls", ".bib", ".bst", ".bbl")
    paper_prefix = paper_dir + "/" if paper_dir else ""
    files = []
    for type_, sha, path in _list_files(repo_dir, ref):
        if type_ == "commit":
            # A submodule: export it recursively, if it is initialized.
            sub_dir = os.path.join(repo_dir, path)
            if os.path.exists(os.path.join(sub_dir, ".git")):
                _export_commit(sub_dir, sha, os.path.join(dst_dir, path), "")
            else:
                _LOG.warning("Submodule '%s' is not initialized", path)
        elif path.endswith(latex_exts) or (
            paper_dir and path.startswith(paper_prefix)
        ):
            files.append(path)
    hio.create_dir(dst_dir, incremental=True)
    if files:
        tar_file = os.path.join(dst_dir, "tmp.diff_latex.export.tar")
        cmd = [
            f"git -C {shlex.quote(repo_dir)}",
            "--literal-pathspecs",
            "archive",
            f"-o {shlex.quote(tar_file)}",
            ref,
            "--",
        ] + [shlex.quote(file_) for file_ in files]
        hsystem.system(" ".join(cmd))
        cmd = f"tar -xf {shlex.quote(tar_file)} -C {shlex.quote(dst_dir)}"
        hsystem.system(cmd)
        os.remove(tar_file)


# #############################################################################
# LaTeX processing
# #############################################################################


def _render_images(snapshot_dir: str, paper_dir: str, log_level: str) -> None:
    """
    Render the diagrams in the `.tex` files of a snapshot, in place.

    The rendered figures are not committed, so they need to be generated.

    :param snapshot_dir: root of the exported commit
    :param paper_dir: dir of the paper, relative to `snapshot_dir`
    :param log_level: verbosity to forward to `render_images.py`
    """
    exec_file = hgit.find_file_in_git_tree("render_images.py")
    pattern = os.path.join(snapshot_dir, paper_dir, "*.tex")
    for tex_file in sorted(glob.glob(pattern)):
        # Skip files without diagrams, so that they are not rewritten.
        if "```" in hio.from_file(tex_file):
            # `render_images.py` writes temporary files in the current dir, so
            # run it in the snapshot to keep the repo clean.
            cmd = (
                f"cd {shlex.quote(snapshot_dir)} && "
                f"{exec_file} --input {shlex.quote(tex_file)} -v {log_level}"
            )
            hsystem.system(cmd, suppress_output=False)


def _flatten(snapshot_dir: str, input_file: str, out_file: str) -> None:
    """
    Merge a LaTeX file and all the files that it includes into a single file.

    :param snapshot_dir: root of the exported commit
    :param input_file: main `.tex` file, relative to `snapshot_dir`
    :param out_file: file where to write the merged LaTeX
    """
    cmd = (
        f"cd {shlex.quote(snapshot_dir)} && "
        f"latexpand {shlex.quote(input_file)} "
        f"--output {shlex.quote(out_file)}"
    )
    # `latexpand` only warns about a missing included file, so show its output.
    hsystem.system(cmd, suppress_output=False)


def _hash_images(
    flat_file: str,
    search_dirs: List[str],
    dst_dir: str,
    *,
    use_placeholder: bool = False,
) -> Set[str]:
    r"""
    Name each image of a merged LaTeX file after its content.

    E.g., `\includegraphics{fig.png}` becomes
    `\includegraphics{diff_figs/1a2b3c4d5e6f7a8b.png}`, so that an image has the
    same name in two commits only if its content didn't change.

    :param flat_file: merged LaTeX file, modified in place
    :param search_dirs: dirs where to look for the images, in order
    :param dst_dir: root dir where to copy the images, under `diff_figs/`
    :param use_placeholder: replace a missing image with a box of text, so that
        the file can still be compiled
    :return: new paths of the images, relative to `dst_dir`
    """
    _LOG.debug(hprint.func_signature_to_str())
    hio.create_dir(os.path.join(dst_dir, "diff_figs"), incremental=True)
    new_paths: Set[str] = set()

    def _replace(match: re.Match) -> str:
        path = match.group("path").strip()
        # Skip the arguments of macro definitions, e.g., `{#2}`.
        if "#" in path or "\\" in path:
            return match.group(0)
        # LaTeX allows to omit the extension.
        candidates = [
            os.path.join(dir_, path + ext)
            for dir_ in search_dirs
            for ext in ["", ".pdf", ".png", ".jpg", ".jpeg"]
        ]
        src_files = [file_ for file_ in candidates if os.path.isfile(file_)]
        if not src_files:
            _LOG.warning("Can't find image '%s'", path)
            if use_placeholder:
                return r"\fbox{Image not rendered}"
            return match.group(0)
        with open(src_files[0], "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()[:16]
        ext = os.path.splitext(src_files[0])[1]
        new_path = f"diff_figs/{digest}{ext}"
        shutil.copyfile(src_files[0], os.path.join(dst_dir, new_path))
        new_paths.add(new_path)
        # Replace only the path, keeping the rest of the command.
        prefix = match.group(0)[: match.start("path") - match.start()]
        return prefix + new_path + "}"

    txt = hio.from_file(flat_file)
    txt = _INCLUDEGRAPHICS_RE.sub(_replace, txt)
    hio.to_file(flat_file, txt)
    return new_paths


def _limit_height(flat_file: str, image_paths: Set[str]) -> None:
    r"""
    Limit the height of some images of a merged LaTeX file.

    `latexdiff` stacks the old and the new version of a changed figure, which
    can be taller than a page.

    Only images sized by `width` (without `height`) are limited, since in this
    case adding a `height` with `keepaspectratio` can only shrink the image.

    :param flat_file: merged LaTeX file, modified in place
    :param image_paths: paths of the images to limit
    """
    _LOG.debug(hprint.func_signature_to_str())

    def _replace(match: re.Match) -> str:
        path = match.group("path")
        opts = match.group("opts") or ""
        if path not in image_paths or "width=" not in opts or "height=" in opts:
            return match.group(0)
        opts += r",height=0.4\textheight,keepaspectratio"
        star = match.group("star")
        return rf"\includegraphics{star}[{opts}]{{{path}}}"

    txt = hio.from_file(flat_file)
    txt = _INCLUDEGRAPHICS_RE.sub(_replace, txt)
    hio.to_file(flat_file, txt)


def _add_old_macros(old_flat_file: str, diff_file: str) -> None:
    r"""
    Define in the diff the macros that exist only in the old paper.

    `latexdiff` keeps the new preamble, so the deleted text can use a macro that
    is not defined anymore, which breaks the compilation. `\providecommand` has
    no effect on the macros that are still defined.

    Only macros defined with a one-line `\newcommand` are handled.

    :param old_flat_file: merged LaTeX of the old commit
    :param diff_file: LaTeX generated by `latexdiff`, modified in place
    """
    # Match e.g., `\newcommand{\foo}[1]{bar #1}`.
    macro_re = re.compile(
        r"""
        ^\\newcommand\*?\s*
        (\{\\[A-Za-z]+\}|\\[A-Za-z]+)   # Macro name, with or without braces.
        \s*(\[[^\]]*\])*                # Optional number of args and default.
        \s*\{.*\}$                      # Body.
        """,
        re.VERBOSE,
    )
    preamble = hio.from_file(old_flat_file).split(r"\begin{document}")[0]
    macros = []
    for line in preamble.split("\n"):
        line = line.strip()
        if macro_re.match(line) and line.count("{") == line.count("}"):
            macros.append(line.replace("newcommand", "providecommand", 1))
    txt = hio.from_file(diff_file)
    txt = txt.replace(
        r"\begin{document}", "\n".join(macros + [r"\begin{document}"]), 1
    )
    hio.to_file(diff_file, txt)


def _mark_up(
    old_flat_file: str,
    new_flat_file: str,
    diff_file: str,
    latexdiff_opts: str,
) -> None:
    """
    Generate the LaTeX file with the changes marked up.

    :param old_flat_file: merged LaTeX of the old commit
    :param new_flat_file: merged LaTeX of the new commit
    :param diff_file: output LaTeX file
    :param latexdiff_opts: options for `latexdiff`
    """
    _LOG.debug(hprint.func_signature_to_str())
    cmd = (
        f"latexdiff {latexdiff_opts} "
        f"{shlex.quote(old_flat_file)} {shlex.quote(new_flat_file)} "
        f"> {shlex.quote(diff_file)}"
    )
    hsystem.system(cmd)
    _add_old_macros(old_flat_file, diff_file)


def _compile(
    snapshot_dir: str, paper_dir: str, tex_file: str, *, fast: bool = False
) -> bool:
    """
    Compile a `.tex` file with as many passes as needed, or one if `fast`.

    :param snapshot_dir: root of the exported commit
    :param paper_dir: dir of the paper, relative to `snapshot_dir`
    :param tex_file: `.tex` file to compile, in `snapshot_dir`
    :param fast: run a single `pdflatex` pass instead of `latexmk`
    :return: whether the compilation succeeded
    """
    # Search files both relative to the paper dir (e.g., figures) and to the
    # root of the repo (e.g., shared styles). The trailing `:` keeps the default
    # TeX search path.
    search_path = shlex.quote(
        f"{os.path.join(snapshot_dir, paper_dir)}:{snapshot_dir}:"
    )
    env_vars = " ".join(
        f"{name}={search_path}"
        for name in ["TEXINPUTS", "BIBINPUTS", "BSTINPUTS"]
    )
    if fast:
        # Remove the files of a previous failed compilation, since `pdflatex`
        # reads them back and they can be broken.
        stem = os.path.join(snapshot_dir, os.path.splitext(tex_file)[0])
        for ext in [".aux", ".out", ".toc", ".nav", ".snm"]:
            if os.path.exists(stem + ext):
                os.remove(stem + ext)
        compiler = "pdflatex"
    else:
        # `-gg` removes the files of a previous failed compilation.
        compiler = "latexmk -gg -pdf"
    cmd = (
        f"cd {shlex.quote(snapshot_dir)} && "
        f"{env_vars} {compiler} -interaction=nonstopmode -halt-on-error "
        f"{shlex.quote(tex_file)}"
    )
    rc = hsystem.system(cmd, abort_on_error=False)
    return rc == 0


# #############################################################################
# Workflow
# #############################################################################


def _diff_latex(
    input_file: str,
    from_ref: str,
    to_ref: str,
    out_file: str,
    actions: List[str],
    log_level: str,
    *,
    alias: str = "",
    latexdiff_opts: str = "",
    fast: bool = False,
    dry_run: bool = False,
) -> None:
    """
    Generate the diff of a paper between two commits.

    :param input_file: main `.tex` file of the paper
    :param from_ref: old commit, used when there is no alias
    :param to_ref: new commit, used when there is no alias
    :param alias: alias for the commits to compare (see `_select_refs()`)
    :param out_file: output PDF, or empty for `<input>.diff.pdf` next to the
        input. The `.tex` diff is saved only if `compile` is skipped
    :param actions: actions to execute
    :param log_level: verbosity to forward to the called scripts
    :param latexdiff_opts: extra options for `latexdiff`, which override the
        ones used by default
    :param fast: skip `render_images` and compile with a single pass
    :param dry_run: only report what would be done
    """
    hdbg.dassert_file_exists(input_file)
    input_path = os.path.realpath(input_file)
    cmd = (
        f"git -C {shlex.quote(os.path.dirname(input_path))} "
        "rev-parse --show-toplevel"
    )
    _, repo_dir = hsystem.system_to_one_line(cmd)
    rel_input = os.path.relpath(input_path, os.path.realpath(repo_dir))
    paper_dir = os.path.dirname(rel_input)
    if not out_file:
        out_file = os.path.splitext(input_path)[0] + ".diff.pdf"
    if "compile" not in actions:
        out_file = os.path.splitext(out_file)[0] + ".tex"
    out_file = os.path.abspath(out_file)
    from_ref, to_ref = _select_refs(
        repo_dir, from_ref, to_ref, alias, dry_run=dry_run
    )
    if dry_run:
        _LOG.warning(
            "[DRY_RUN] Would diff '%s' from '%s' to '%s' into '%s'",
            rel_input,
            from_ref,
            to_ref,
            out_file,
        )
        return
    compiler = "pdflatex" if fast else "latexmk"
    for tool in ["latexpand", "latexdiff", compiler]:
        hdbg.dassert_is_not(
            shutil.which(tool), None, "Missing '%s': install MacTeX", tool
        )
    # The work dir is inside the repo so that Docker can mount it.
    root_dir = os.path.join(repo_dir, "tmp.diff_latex")
    hio.create_dir(root_dir, incremental=False)
    # Use a new dir at each run: `render_images.py` caches its results by file
    # path and so it doesn't regenerate a figure that was deleted.
    work_dir = tempfile.mkdtemp(prefix="run.", dir=root_dir)
    _LOG.info("Working in '%s': delete it if this run fails", root_dir)
    # Export and flatten each commit.
    flat_files = []
    snapshot_dirs = []
    for name, ref in [("old", from_ref), ("new", to_ref)]:
        # Resolve the ref to fail early on a typo.
        cmd = (
            f"git -C {shlex.quote(repo_dir)} rev-parse --verify "
            f"{shlex.quote(ref + '^{commit}')}"
        )
        _, sha = hsystem.system_to_one_line(cmd)
        _LOG.info("Exporting '%s' (%s)", ref, sha[:8])
        snapshot_dir = os.path.join(work_dir, name)
        _export_commit(repo_dir, sha, snapshot_dir, paper_dir)
        hdbg.dassert_file_exists(
            os.path.join(snapshot_dir, rel_input),
            "The input file doesn't exist in commit '%s'",
            ref,
        )
        if "render_images" in actions and not fast:
            _render_images(snapshot_dir, paper_dir, log_level)
        flat_file = os.path.join(work_dir, f"{name}.tex")
        _flatten(snapshot_dir, rel_input, flat_file)
        flat_files.append(flat_file)
        snapshot_dirs.append(snapshot_dir)
    # The diff is compiled in the new snapshot, to use the styles of the new
    # commit.
    new_dir = snapshot_dirs[1]
    # Name the images of both commits after their content, in the new snapshot.
    image_paths = [
        _hash_images(
            flat_file,
            [os.path.join(snapshot_dir, paper_dir), snapshot_dir],
            new_dir,
            use_placeholder=fast,
        )
        for flat_file, snapshot_dir in zip(flat_files, snapshot_dirs)
    ]
    # Limit the height of the images that are only in one of the commits.
    changed_paths = image_paths[0] ^ image_paths[1]
    _LOG.info("Found %d changed image files", len(changed_paths))
    for flat_file in flat_files:
        _limit_height(flat_file, changed_paths)
    # Mark up the changes. The user options come last to override the defaults.
    diff_file = os.path.join(new_dir, "tmp.diff_latex.diff.tex")
    opts = f"--graphics-markup=both {latexdiff_opts}"
    _mark_up(flat_files[0], flat_files[1], diff_file, opts)
    result_file = diff_file
    if "compile" in actions:
        tex_file = os.path.basename(diff_file)
        success = _compile(new_dir, paper_dir, tex_file, fast=fast)
        # The markup can generate invalid LaTeX, e.g., inside an equation, or
        # unbalanced braces when a `\textbf{...}` is moved. Retry with less
        # detailed markup.
        math_opts = [""]
        if "--math-markup" not in latexdiff_opts:
            math_opts.append("--math-markup=off")
        fallback_opts = [
            f"{text_opt} {math_opt}".strip()
            for text_opt in ["", "--exclude-textcmd=textbf"]
            for math_opt in math_opts
        ]
        # Skip the first combination, which has already been tried.
        for fallback_opt in fallback_opts[1:]:
            if success:
                break
            _LOG.warning(
                "Compilation failed: retrying with '%s', so some changes are "
                "not marked",
                fallback_opt,
            )
            _mark_up(
                flat_files[0],
                flat_files[1],
                diff_file,
                f"{opts} {fallback_opt}",
            )
            success = _compile(new_dir, paper_dir, tex_file, fast=fast)
        hdbg.dassert(
            success,
            "LaTeX compilation failed: see '%s'",
            os.path.splitext(diff_file)[0] + ".log",
        )
        result_file = os.path.splitext(diff_file)[0] + ".pdf"
        hdbg.dassert_file_exists(result_file)
    shutil.copyfile(result_file, out_file)
    _LOG.info("Created '%s'", out_file)
    # The snapshots contain copies of files of the repo, which break the tools
    # that search files by name (e.g., `hgit.find_file_in_git_tree()`).
    if "compile" in actions:
        shutil.rmtree(root_dir)
    else:
        # The `.tex` diff needs the images and styles of the snapshot.
        _LOG.warning("Keeping '%s': delete it after use", root_dir)


# #############################################################################
# CLI
# #############################################################################


def _parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=hparser.CustomHelpFormatter,
    )
    hseinout.add_input_output_args(parser, in_required=True, out_required=False)
    # Exactly one way of specifying the old version is needed.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from_ref", type=str, default="", help="Old git commit")
    for short_flag, alias, help_ in [
        ("-l", "last_commit", "Compare `HEAD~1` with `HEAD`"),
        ("-m", "modified", "Compare `HEAD` with the uncommitted changes"),
        ("-b", "branch", "Compare the tip of `origin/master` with `HEAD`"),
        ("-n", "branch_point", "Compare the branch point with `HEAD`"),
    ]:
        group.add_argument(
            short_flag,
            f"--{alias}",
            dest="alias",
            action="store_const",
            const=alias,
            default="",
            help=help_,
        )
    parser.add_argument(
        "--to_ref",
        type=str,
        default="",
        help="New git commit, only with `--from_ref`. Empty for `HEAD`",
    )
    parser.add_argument(
        "--latexdiff_opts",
        type=str,
        default="",
        help="Extra options for `latexdiff`, passed with `=` "
        "(e.g., --latexdiff_opts='--math-markup=whole')",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip rendering the images and run a single `pdflatex` pass",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )
    hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    hparser.add_verbosity_arg(parser)
    return parser


def _main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    hdbg.init_logger(verbosity=args.log_level, use_exec_path=True)
    if args.alias:
        hdbg.dassert_eq(
            args.to_ref, "", "`--to_ref` can be used only with `--from_ref`"
        )
    actions = hselacti.select_actions(args, _VALID_ACTIONS, _DEFAULT_ACTIONS)
    _diff_latex(
        args.input,
        args.from_ref,
        args.to_ref,
        args.output or "",
        actions,
        args.log_level,
        alias=args.alias,
        latexdiff_opts=args.latexdiff_opts,
        fast=args.fast,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    _main(_parse())
