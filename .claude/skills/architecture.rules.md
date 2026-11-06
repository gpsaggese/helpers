Conventions for software architecture and code organization

# ARCH1: Layers and Dependencies

## `ARCH1.1`: Organize Code in Layers

- Split code into layers. Each layer has one responsibility:
  - **Script**: parse CLI arguments (`_parse()`)
  - **Orchestration**: call the other layers in order (`_main()`)
  - **Business logic**: algorithms and data transformations, no I/O
  - **Infrastructure**: file I/O, system calls, databases, external APIs
  - **Utilities**: generic helpers and data structures
- Point dependencies one way:
  - Script calls orchestration
  - Orchestration calls business logic and infrastructure
  - Business logic and infrastructure call only utilities
- Pass data from infrastructure to business logic through arguments
- Business logic accepts data, not paths: `analyze_dataset(df: pd.DataFrame)`, not
  `analyze_dataset(path: str)`
- This enables testing business logic without I/O, swapping data sources or formats,
  and reusing logic in other scripts
- Test business logic with plain inputs. Test infrastructure with real files
  - See `.claude/skills/testing.rules.md`
- **Bad** (I/O and printing mixed with computation)
  ```python
  def process_data(input_file: str) -> None:
      with open(input_file) as f:
          data = json.load(f)
      result = complex_calculation(data)
      print(result)
  ```
- **Good** (one function per layer; `_main()` calls them in order)
  ```python
  def _read_input(input_file: str) -> Dict[str, Any]:
      """
      Infrastructure layer: read the input file.
      """
      with open(input_file) as f:
          return json.load(f)


  def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
      """
      Business logic layer: compute the result.
      """
      return complex_calculation(data)


  def _write_output(result: Dict[str, Any], output_file: str) -> None:
      """
      Infrastructure layer: write the result.
      """
      with open(output_file, "w") as f:
          json.dump(result, f)


  def _main(parser: argparse.ArgumentParser) -> None:
      """
      Orchestration layer: call the other layers in order.
      """
      args = parser.parse_args()
      data = _read_input(args.input_file)
      result = process_data(data)
      _write_output(result, args.output_file)
  ```

## `ARCH1.2`: Keep Interfaces Between Layers Minimal

- Pass only the data the callee needs, not a context object
- No callbacks from an inner layer to an outer layer
- No bidirectional dependencies between layers
- **Bad** (the callee depends on and mutates `context`)
  ```python
  def process(context: Any) -> None:
      context.data = transform(context.data)
      context.log(f"Processed {context.count} items")
      context.state = "done"
  ```
- **Good** (one input, one output)
  ```python
  def process(data: pd.DataFrame) -> pd.DataFrame:
      """
      Transform the data.
      """
      return transform(data)


  # The caller manages logging and state.
  processed = process(data)
  ```

## `ARCH1.3`: Enforce Dependency Direction

- No import cycles between modules
- Do not import a higher-layer module from a lower-layer module
- Put types shared by several modules (dataclasses, enums, constants) in a leaf
  module that imports no project module
- A unit test parses the imports of every module and fails on a forbidden import
- **Bad** (`report.py` imports `pipeline.py`, which imports `report.py`)
  ```python
  # report.py
  import pipeline

  def render(df: pd.DataFrame) -> str:
      return df.to_string(max_rows=pipeline.MAX_ROWS)
  ```
- **Good** (both modules import the leaf module `project_types.py`)
  ```python
  # report.py
  import project_types

  def render(df: pd.DataFrame) -> str:
      return df.to_string(max_rows=project_types.MAX_ROWS)
  ```

## `ARCH1.4`: Split Modules by Responsibility

- Give each module one responsibility. Name it after that responsibility
- In helpers, name modules `h<module>` (e.g., `hdownload.py`). Elsewhere, follow the
  project's naming
- **Bad** (unrelated functions in one module)
  ```python
  # hutils.py
  def download_data() -> pd.DataFrame:
      ...

  def train_model(df: pd.DataFrame) -> Model:
      ...

  def generate_report(model: Model) -> str:
      ...
  ```
- **Good** (one module per responsibility)
  ```python
  # hdownload.py: data fetching.
  def download_data() -> pd.DataFrame:
      ...

  # hmodel.py: ML training.
  def train_model(df: pd.DataFrame) -> Model:
      ...

  # hreport.py: report generation.
  def generate_report(model: Model) -> str:
      ...
  ```

# ARCH2: Data Flow and Interfaces

## `ARCH2.1`: Pass Data Through Arguments and Return Values

- Make every data dependency explicit in the signature. Use type hints
- Document the expected format in the docstring (e.g., required DataFrame columns)
- Never pass data between functions through globals
- **Bad** (hidden global state: `stage2()` needs `stage1()` to run first)
  ```python
  _data: Optional[pd.DataFrame] = None

  def stage1() -> None:
      global _data
      _data = fetch()

  def stage2() -> None:
      global _data
      _data = transform(_data)
  ```
- **Good** (data flows through arguments and return values)
  ```python
  def stage1() -> pd.DataFrame:
      """
      Fetch the data from the source.

      :return: DataFrame with columns 'feature', 'target'
      """
      return fetch()


  def stage2(data: pd.DataFrame) -> pd.DataFrame:
      """
      Transform the fetched data.

      :param data: DataFrame with columns 'feature', 'target'
      :return: DataFrame with the added column 'prediction'
      """
      return transform(data)


  # In the orchestration layer.
  data = stage1()
  data = stage2(data)
  ```

## `ARCH2.2`: Bundle Parameters Into a Config Dataclass

- Use a config dataclass when a function has more than 3 parameters that tune its
  behavior
- Keep required inputs in the signature. Move options to the config
- Make config fields required, unless
  `## Use Default Values Rarely and Force Keyword-Only Via `\*``in`.claude/skills/coding.rules.md`
  allows a default
- The config states WHAT to do. The code implements HOW. Do not store expressions or
  code in config values
- **Bad** (too many keyword-only options in the signature)
  ```python
  def transform(
      data: pd.DataFrame,
      *,
      scale: bool,
      normalize: bool,
      remove_outliers: bool,
      handle_missing: str,
      log_transform: bool,
  ) -> pd.DataFrame:
      ...
  ```
- **Good** (the config groups related options)
  ```python
  @dataclass
  class TransformConfig:
      scale: bool
      normalize: bool
      remove_outliers: bool
      handle_missing: str
      log_transform: bool


  def transform(data: pd.DataFrame, config: TransformConfig) -> pd.DataFrame:
      """
      Apply the transformations selected in the config.
      """
      ...
  ```
- **Bad** (the config embeds logic as a string)
  ```python
  config = {"transform": "if value > 0 then log(value) else 0"}
  ```
- **Good** (the config declares intent, the code implements it)
  ```python
  @dataclass
  class Config:
      transform_type: str  # "log" or "none".


  if config.transform_type == "log":
      result = log_transform(data)
  ```

## `ARCH2.3`: Return and Pass Dataclasses, Not Tuples

- Return a dataclass or `NamedTuple` for 3 or more values, or for values with
  different meanings
- Use a plain tuple only for a pair of same-kind values, e.g., `(train_df, test_df)`
- Group inputs that always travel together in one dataclass
- **Bad** (the order of the 4 returned values is implicit)
  ```python
  def analyze(data: pd.Series) -> Tuple[float, float, int, float]:
      return mean, std, count, median
  ```
- **Good** (the fields are named)
  ```python
  @dataclass
  class Statistics:
      mean: float
      std: float
      count: int
      median: float


  def analyze(data: pd.Series) -> Statistics:
      """
      Compute the summary statistics of the data.

      :param data: input values
      :return: mean, std, count, and median of the values
      """
      return Statistics(mean=..., std=..., count=..., median=...)
  ```
- **Bad** (the relation between the 3 lists is implicit)
  ```python
  def analyze(
      values: List[float],
      indices: List[int],
      timestamps: List[datetime],
  ) -> Any:
      ...
  ```
- **Good** (one object owns the related data)
  ```python
  @dataclass
  class TimeSeries:
      values: List[float]
      indices: List[int]
      timestamps: List[datetime]


  def analyze(series: TimeSeries) -> Statistics:
      ...
  ```

## `ARCH2.4`: Do Not Modify Inputs

- Do not modify an argument in place. Return a new object
- Allow in-place functions only when a copy costs too much (e.g., a huge
  `pd.DataFrame`)
  - Name them with the suffix `_inplace`
  - State in the docstring that they modify the input
- **Bad** (changes the caller's DataFrame)
  ```python
  def normalize(df: pd.DataFrame) -> pd.DataFrame:
      """
      Normalize the DataFrame in place.
      """
      value = df["value"]
      df["value"] = (value - value.mean()) / value.std()
      return df
  ```
- **Good** (returns a normalized copy)
  ```python
  def normalize(df: pd.DataFrame) -> pd.DataFrame:
      """
      Return a normalized copy of the DataFrame.
      """
      df_norm = df.copy()
      value = df_norm["value"]
      df_norm["value"] = (value - value.mean()) / value.std()
      return df_norm
  ```

# ARCH3: Pipelines

## `ARCH3.1`: Split Sequential Processing Into Stages

- Use a pipeline of stages for 3 or more sequential steps
- Design each stage to:
  - Have one responsibility
  - Take its input as an argument and return its output
  - Be idempotent: running it twice gives the same result
  - Depend on other stages only through its input
- This enables testing each stage alone and adding, removing, or reordering stages
- Pass data by return value only when all stages always run together. For selectable
  stages, see `ARCH3.3`
- **Bad** (one function mixes all stages)
  ```python
  def run() -> None:
      data = fetch_from_api()
      data = transform(data)
      save_to_storage(data)
      remove_temp_files()
  ```
- **Good** (one function per stage; the orchestration passes the data)
  ```python
  def _download() -> pd.DataFrame:
      """
      Download the data from the source.
      """
      return fetch_from_api()


  def _process(data: pd.DataFrame) -> pd.DataFrame:
      """
      Transform and validate the data.
      """
      return transform(data)


  def _upload(data: pd.DataFrame) -> None:
      """
      Upload the processed data to the destination.
      """
      save_to_storage(data)


  # In the orchestration layer.
  data = _download()
  data = _process(data)
  _upload(data)
  ```

## `ARCH3.2`: Select Stages with Hselect_action

- Use `helpers.hselect_action` so users can run a subset of stages
  - Flags: `--action`, `--skip_action`, `--all_actions`, `--clear_actions`
  - See `.claude/skills/script.rules.md` `### Action Selection`
- Define each action as a private function `_<action_name>()`
  - E.g., the action `"download"` runs `_download()`
- Define `_VALID_ACTIONS` (all stages) and `_DEFAULT_ACTIONS` (stages that run by
  default) at the top of the script
- List valid actions in run order, and document that order
- Register actions in `_parse()` and run them in `_main()`
- **Bad** (no way to skip or select a stage)
  ```python
  def _main(parser: argparse.ArgumentParser) -> None:
      args = parser.parse_args()
      _download()
      _process()
      _upload()
      _cleanup()
  ```
- **Good** (the user selects the stages)
  ```python
  import helpers.hselect_action as hselacti

  _VALID_ACTIONS = ["download", "process", "upload", "cleanup"]
  _DEFAULT_ACTIONS = ["download", "process", "upload"]


  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(...)
      hselacti.add_action_arg(parser, _VALID_ACTIONS, _DEFAULT_ACTIONS)
      return parser


  def _main(parser: argparse.ArgumentParser) -> None:
      args = parser.parse_args()
      actions = hselacti.select_actions(
          args, _VALID_ACTIONS, _DEFAULT_ACTIONS
      )
      while actions:
          action = actions[0]
          to_execute, actions = hselacti.mark_action(action, actions)
          if not to_execute:
              continue
          if action == "download":
              _download(args.raw_file)
          elif action == "process":
              _process(args.raw_file, args.processed_file)
          elif action == "upload":
              _upload(args.processed_file)
          elif action == "cleanup":
              _cleanup(args.raw_file, args.processed_file)
  ```

## `ARCH3.3`: Pass Data Between Selectable Stages Through Files

- Assume users can skip any stage that `hselect_action` makes selectable
- Do not rely on the return value of another stage
- Each stage reads its input from a file and writes its output to a file. Take the
  paths from CLI arguments
- This lets you run one stage alone on the output of an earlier run
- **Bad** (`--skip_action download` leaves `data` undefined)
  ```python
  if action == "download":
      data = _download()
  elif action == "process":
      data = _process(data)
  ```
- **Good** (each stage reads and writes files, so any stage runs alone)
  ```python
  if action == "download":
      _download(args.raw_file)
  elif action == "process":
      _process(args.raw_file, args.processed_file)
  ```

## `ARCH3.4`: Split a Pipeline Into Executables

- Split a pipeline into one executable per stage when any of these holds:
  - Stages have different dependencies (e.g., one needs a GPU, another only `pandas`)
  - Stages have different runtimes (e.g., one takes hours, another seconds)
  - Stages run on different schedules (e.g., daily download, weekly report)
  - The script is too large to read or test
- Executables communicate only through files on disk. Pass paths as CLI arguments. Do
  not share state through imports or globals
- This enables re-running one stage, running stages on different machines or
  containers, and inspecting intermediate results
- Otherwise keep one script with `hselect_action`. Inside an executable, use
  `hselect_action` for its internal stages
- **Bad** (one script mixes stages with different dependencies and schedules)
  ```bash
  > run_pipeline.py --all_actions
  ```
- **Good** (one executable per stage, linked by files on disk)
  ```bash
  > download_data.py --output tmp.raw.json
  > train_model.py --input tmp.raw.json --output tmp.model.pkl
  > generate_report.py --input tmp.model.pkl --output tmp.report.md
  ```

## `ARCH3.5`: Sequence Executables with a Driver Script

- Write a driver script when users run the same 3 or more executables in the same
  order
- Write the driver in bash first: `run_<flow>.sh`. Follow
  `.claude/skills/bash.rules.md`
- Convert the driver to Python (`run_<flow>.py`) when any of these holds:
  - Users need to run only some steps through the driver
  - The driver needs an option other than the directory
  - The driver must forward `-v` or `--dry_run`
  - The driver needs a conditional or loop, not only a straight sequence
  - The driver exceeds 50 lines
- Keep the executables runnable alone
- The driver holds only sequencing, no business logic
- Take one directory as argument. Derive every intermediate file path from it
- Stop at the first failing step (e.g., `set -e` in bash)
- In a Python driver:
  - Call each executable with `hsystem.system()`
  - Forward `-v` and `--dry_run`. See `# Standard Argument Helpers` and `# Dry Run`
    in `.claude/skills/script.rules.md`
  - Use `hselect_action` with one action per executable, named after it. See
    `ARCH3.2`
- **Bad** (the user types each command and repeats the paths by hand)
  ```bash
  > download_data.py --output tmp.raw.json
  > train_model.py --input tmp.raw.json --output tmp.model.pkl
  > generate_report.py --input tmp.model.pkl --output tmp.report.md
  ```
- **Good** (a bash driver: one command, paths derived from one directory)
  ```bash
  #!/bin/bash
  # """
  # Run the flow: download the data, train the model, and generate the report.
  #
  # Usage: run_flow.sh <DIR>
  # """

  set -e

  DIR=$1
  mkdir -p "$DIR"

  # Download the data.
  download_data.py --output "$DIR/raw.json"
  # Train the model.
  train_model.py --input "$DIR/raw.json" --output "$DIR/model.pkl"
  # Generate the report.
  generate_report.py --input "$DIR/model.pkl" --output "$DIR/report.md"
  ```
- **Good** (after conversion to Python, a user runs one step alone)
  ```bash
  > run_flow.py --dir tmp.flow
  > run_flow.py --dir tmp.flow --clear_actions --action train_model
  ```

## `ARCH3.6`: Number the Output Files of Each Executable

- Name each file that an executable writes in the output dir
  `NN-<stage>.<what>.<ext>`
  - `NN`: two-digit order of the executable in the pipeline
  - `<stage>`: name of the stage that writes the file
  - `<what>`: content of the file
- Give the stages of one executable the same `NN`, e.g., the stages `rate` and
  `report` of one script both get `04`
- Use `00` for the copy of the input of the pipeline
- Keep the numbers and the names in one module of path getters
  - Executables and tests call the getters and never repeat a string literal
- Put the files of one item (e.g., one paper) in a subdir, and name each file after
  the item with no number
- This makes a listing of the output dir read in pipeline order, and shows which
  executable wrote each file
- Do not hide the files of a stage in a `state/` dir
  - Keep in a subdir only what is not a result of a stage, e.g., a cache or logs
- **Bad** (free names, and the issues of a stage in a state dir)
  ```text
  papers.csv
  state/issues.download.json
  report.csv
  ```
- **Good** (the number gives the order, the stage gives the writer)
  ```text
  00-paper_list.csv
  01-resolve.paper_list.json
  02-download.issues.json
  04-report.report.csv
  papers/<BASE>.pdf
  ```

## `ARCH3.7`: Take `--output_dir` for Several Files and `--output` for One

- Let the user choose where the files go, and let the executable choose the names,
  per `ARCH3.6`
- If an executable writes several files, take `--output_dir` only
- If an executable writes one file, take one of these:
  - `--output_dir`: the executable infers the file name
  - `-o/--output`: the user gives the path of the file
  - Accept exactly one of them with
    `parser.add_mutually_exclusive_group(required=True)`
- Read the input of a later executable with `-i/--input`
  - Default to the file that the executable of the earlier stage wrote in
    `--output_dir`, so the user does not repeat the path
- Follow `.claude/skills/script.rules.md` for the flags `-i` and `-o`
- **Bad** (the user names each file of one executable by hand)
  ```bash
  > resolve_papers.py --input list.csv --output papers.csv --issues_output issues.csv
  > download_papers.py --input papers.csv --output_dir run_1
  ```
- **Good** (several files: one dir, the names are inferred, the next stage finds its
  input)
  ```bash
  > resolve_papers.py --input list.csv --output_dir run_1
  > download_papers.py --output_dir run_1
  ```
- **Good** (one file: the user can give the dir or the file)
  ```bash
  > make_summary.py --input run_1/01-resolve.paper_list.json --output_dir run_1
  > make_summary.py --input run_1/01-resolve.paper_list.json --output summary.json
  ```

## `ARCH3.8`: Use JSON for Intermediate Files

- Write a file that another executable reads as JSON
  - JSON holds lists and nested data with their types
  - People and programs both read it
- Write CSV only for a file that a person opens in a spreadsheet
  - E.g., the final report, or an input list that the user writes
- Do not join a list into one cell (e.g., `a|b`)
  - An item that holds the separator breaks the read
- Put a `schema_version` key in every JSON file, and check it on read
  - A file from an old version then fails with a clear message
- **Bad** (a list in one CSV cell)
  ```text
  title,authors
  Some Title,Smith|Jones
  ```
- **Good** (a JSON array)
  ```json
  {"schema_version": 1, "title": "Some Title", "authors": ["Smith", "Jones"]}
  ```

## `ARCH3.9`: End Each Stage with a Summary of Its Output

- End each stage with a summary of what it did
  - The user then does not read the whole log or list the output dir to know
- The summary answers three questions:
  - What output files did the stage generate?
    - List the path of every output file, e.g., both the results file and the issues
      file
    - Give the number of files written in the run if the stage writes one file per
      unit
  - How many units did the stage process?
    - A unit is the item that the stage loops over, e.g., a record, a paper, or an
      input line
    - Give the units in the input, the units skipped, and the units processed in the
      run
  - How many units did it complete successfully?
    - Give the units that completed and the units that failed
    - Point to the file that says why each unit failed
- Put each unit in exactly one group, so that the groups add up to the units in the
  input:
  - Skipped: done in an earlier run, or an earlier stage failed for the unit
  - Completed successfully
  - Failed
- Write the same text to the log and to the file `NN-<stage>.summary.txt` in the
  output dir, per `ARCH3.6`
  - Write the file also when no unit fails, so the user knows that the stage ended
  - Overwrite it at each run, so it describes the last run
- In a dry run, log what the stage would process and write no file
- Put the time that the stage took in the summary, per `ARCH3.10`
- Build the text in one function from a dataclass of counts, per `ARCH2.3`
  - Each stage fills the dataclass in its own loop, and one test checks the format of
    all the stages
- **Bad** (one count of failures: no files, no skipped units, no processed units)
  ```text
  Download: 2 of 20 papers failed
  ```
- **Good** (the three answers, and a rerun shows the units that it skipped)
  ```text
  Stage `download` summary
    Papers in input:        20
    Skipped, done before:   12
    Processed in this run:   8
    Completed successfully:  6
    Failed:                  2
    Elapsed time: 1 min 15.3 sec
    Output files written in this run:
      'run_1/papers/<BASE>.pdf': 6 files
      'run_1/papers/<BASE>.md': 6 files
    Issues file: 'run_1/02-download.issues.json' (2 issues)
    Summary file: 'run_1/02-download.summary.txt'
  ```

## `ARCH3.10`: Report How Long Each Stage Took

- Measure the wall-clock time of each stage and report it
  - A slow stage (a network call, an LLM call) is otherwise hidden in the log
  - The user then sees which stage to speed up, and how much a rerun saved
- Start the timer at the top of the function of the stage, and read it when you
  build the summary, per `ARCH3.9`
  - Use `helpers.htimer.Timer`, not `time.time()` arithmetic in each stage
- Keep the time in the dataclass of the summary, per `ARCH2.3`, as `elapsed_sec`
  - The log and the file `NN-<stage>.summary.txt` then show the same time
  - In a dry run, show no time, since the stage processes nothing
- Format the time in one function that all the stages and the driver call
  - Show one decimal digit for the seconds, and drop the leading units that are
    zero: `12.3 sec`, `1 min 15.3 sec`, `1 h 2 min 5.0 sec`
  - Round before you split the units, so that `59.96` is `1 min 0.0 sec` and not
    `60.0 sec`
- Let a driver script that runs the executables, per `ARCH3.5`, log at the end the
  time of each executable and the total
  - The time of an executable includes its start-up, so the total is a bit more
    than the sum of the times in the summaries of the stages
- Test the time without a flaky test:
  - Replace the time in the summary files with `<TIME>` in the helper that reads
    them
  - Test the format function on fixed values, including the edges at 60 seconds
    and at 1 hour
  - Test one stage with a real wait, and check that its time is at least the wait
- **Bad** (no time: the user cannot tell which stage is slow)
  ```text
  Stage `extract` summary
    Papers in input:        20
    Completed successfully: 20
  ```
- **Bad** (a raw float that the user must convert, and a different format in each
  stage)
  ```text
  Stage `extract` summary: took 4523.8812 s
  Stage `download` summary: 1:15
  ```
- **Good** (one format, in the summary of every stage)
  ```text
  Stage `extract` summary
    Papers in input:        20
    Completed successfully: 20
    Elapsed time: 1 h 15 min 23.9 sec
  ```
- **Good** (the driver adds the time of each executable and the total)
  ```text
  Time of each action
    resolve_papers:   12.3 sec
    download_papers:  1 min 5.0 sec
    Total:            1 min 17.3 sec
  ```

# ARCH4: Validation

## `ARCH4.1`: Validate at the Boundary

- Validate user input and option combinations in `_main()`, right after parsing
- Use `hdbg.dassert_*` with a message, not `if ... raise`. See
  `.claude/skills/coding.rules.md` `# Error Handling and Assertions`
- Do not repeat input checks in inner layers
- Keep a cheap `dassert` in an inner layer only for an invariant that, if broken,
  gives a wrong result without an error
- **Bad** (the same check in every layer)
  ```python
  def download(url: str) -> bytes:
      hdbg.dassert_ne(url, "", "URL required")
      ...


  def fetch(url: str) -> bytes:
      hdbg.dassert_ne(url, "", "URL required")
      ...
  ```
- **Bad** (an invalid option combination fails deep in the processing)
  ```python
  def process(config: Config) -> None:
      hdbg.dassert(
          not config.output_dir or config.format,
          "--format is required when --output_dir is specified",
      )
  ```
- **Good** (`_main()` validates once; the inner layers trust the input)
  ```python
  def _main(parser: argparse.ArgumentParser) -> None:
      """
      Orchestration layer: validate at the boundary, then delegate.
      """
      args = parser.parse_args()
      hdbg.dassert_ne(args.url, "", "--url must not be empty")
      hdbg.dassert(
          not args.output_dir or args.format,
          "--format is required when --output_dir is specified",
      )
      data = download(args.url)
      ...
  ```