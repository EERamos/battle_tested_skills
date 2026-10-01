---
name: python-standards
description: Robust Python coding standards scaled to the kind of code — library, unattended script, or notebook and analysis. Enums, dataclasses, Protocols, dependency injection, composition, type annotations, exceptions and warnings, NaN handling, explicit dates and paths, pandas, notebooks, pytest/hypothesis/mutation testing. Use whenever writing, refactoring, or reviewing ANY Python code — modules, scripts, notebooks, agents, CLI tools, tests, or Python embedded in a larger task — even if the user doesn't mention standards, typing, or best practices.
---

# Robust Python

Operating rules for all Python code. Where a rule can be checked mechanically, its section ends with a **Verification** — how to prove it held.

## Pick the level first

The bar depends on what the code is. Decide before writing.

| Level | What it is | What applies |
|---|---|---|
| **Library** | Code that other code imports: packages, modules, agents, CLI internals | Everything in this file |
| **Script** | Runs on its own and produces an output: a pipeline step, a scheduled job, a backtest runner | *Any code*; type annotations; pytest for the logic that decides the output |
| **Notebook / analysis** | An `.ipynb`, or a `.py` run cell by cell | *Any code* and [references/notebooks.md](references/notebooks.md). No enums, Protocols, test suites or mutation testing: a notebook's bugs live in its data, not its design |

If the level is unclear, pick the lighter one and say which you picked.

Code that loads, transforms or caches tabular data also follows [references/data.md](references/data.md), at any level.

## Reporting checks
- Report only what ran. A check whose tool is missing (no `mypy`, no `ruff`, Hypothesis not installed) is reported as **not run**, never as passed; then check by reading the code, and say that is what you did.
- **Why**: a "passed" that never ran stops the next person from looking.

## Any code

These hold for every file, however small.

### Exceptions and warnings
- No bare `except:` and no `except Exception: pass`. Catch the exceptions you can name and handle.
- Don't turn an error into a default value (`except KeyError: return 0`) unless that default is the documented meaning of "missing".
- Don't silence every warning at once (`warnings.filterwarnings("ignore")`); filter by category and message.
- A `warnings.catch_warnings(record=True)` block re-emits whatever it does not handle.
- **Why**: a swallowed error turns into a wrong number downstream, far from its cause.
- **Verification**: grep `except:`, `except Exception`, `filterwarnings("ignore"` and `record=True`; every hit names its exception or category, or re-raises/re-emits.

### NaN as well as None
- A value taken from a DataFrame, Series or NumPy array can be NaN, not only None. Check it with `pd.isna(x)` (or `math.isnan` for a plain float), never with `x is None` alone.
- `.mean()` and `.sum()` skip NaN without telling you: count them first (`s.isna().sum()`) and decide what a missing value means.
- `value or fallback` does not protect you: NaN is truthy.
- No guard is needed where a NaN already shows up as a FAIL in the output.
- **Why**: NaN spreads quietly; an average over a half-empty column still looks like a valid number.
- **Verification**: every value read from a DataFrame or array that reaches a branch or an aggregate has an `isna` check, or a NaN count, before it.

### Explicit dates, parameters and paths
- No hidden "today": `date.today()` / `datetime.now()` may stamp when something ran, never decide which data to use. Pass the as-of date in.
- Each path and each parameter is defined once for the whole project (one config module; in a single-file script or notebook, one constants block at the top) and used from there.
- What is written is read back through the same path variable.
- **Why**: a hidden "today" makes yesterday's run impossible to reproduce; a path typed twice drifts and the reader opens a stale file.
- **Verification**: grep `today()`, `now()` and string literals ending in a file extension; each hit is a run stamp or lives in the single definition.

### Checks end in a verdict
- A check (validation, reconciliation, a test script) prints PASS or FAIL and exits non-zero on FAIL.
- Expected differences are named in the code with their reason, never eyeballed.
- **Why**: a check that only prints numbers depends on someone reading them every time.
- **Verification**: run it on a known-bad input; the exit code is non-zero.

### The simplest change that works
- A fix touches what the fix needs. No renames, refactors or cleanup of unrelated code in the same change.
- **Why**: mixed diffs hide the line that matters and make a revert risky.

### Mutable defaults
- No mutable default literals anywhere: function arguments (`def f(x=[])`) as well as dataclass fields. Default to `None` and build inside, or use `field(default_factory=...)`.
- **Verification**: `ruff` rule `B006`, or grep signatures for `=[]`, `={}` and `=set()`.

### Batch jobs finish before you read them
- A batch (backtest, backfill, bulk export) must finish completely, with its exit code checked, before its results are read or reported.
- **Why**: partial output looks like full output; a backtest read halfway describes a different strategy.
- **Verification**: the reader checks a completion marker (exit code, expected row count, a done file) before loading results.

## Library level: defining your own types

Everything below applies to library code. Scripts take *Type annotations*, *Constraining types*, *Collections* and *Testing (pytest)* from here; notebooks take none of it.

### Enums
- Use `enum.Enum` and `enum.auto()`. No magic numbers or raw strings for categories.
- Style: `class MyEnum(Enum):` with UPPERCASE member names.

### Data classes
- Use `@dataclass`. Prefer `frozen=True` for immutability.
- Type-hint all fields. Use `field(default_factory=...)` for mutable defaults (never mutable default literals).

### Classes
- Enforce invariants: the class keeps its data in a valid state.
- **Verification**: Test that violates an invariant fails (class prevents it or raises).

### Protocols and interfaces
- Use `typing.Protocol` for structural subtyping. Avoid deep inheritance.
- Use `@runtime_checkable` only when you need `isinstance` checks.
- A class can satisfy a Protocol without inheriting from it (duck typing with safety).

### Dependency injection
- Pass dependencies (objects/services) into functions or constructors; do not instantiate them inside the consumer.
- Use type hints to declare the interface of the injected dependency.

### Composition
- Prefer "Has-A" over "Is-A". Build complex behavior by combining small, focused objects.
- Avoid god objects; delegate responsibilities to composed parts.

### Static analysis
- Use a linter and formatter (e.g. `ruff` for both; `pylint`/`flake8` + `black` are fine if the project already uses them). Automate; don't rely on manual style review.
- **Verification**: Run the linter on complex code and refactor until it passes.

### Testing (pytest)
- Use pytest. Write unit tests. Arrange-Act-Assert. Use fixtures for setup.
- Test behavior and properties, not only single data points.
- **Verification**: Run `pytest`; all tests pass and failures have clear messages.

### Property-based testing (hypothesis)
- Use Hypothesis when it is installed (or the project already depends on it); don't add the dependency just to satisfy this rule. Define strategies (e.g. `st.integers()`, `st.lists()`) for generated data.
- Aim to find edge cases (e.g. division by zero, empty lists) that examples miss.
- **Verification**: Run a hypothesis test that exposes a bug (e.g. wrong handling of zero or empty input).

### Mutation testing
- Use mutmut or similar when the deliverable is the tests themselves (a new suite, or a request to harden one). Reason about mutant survival.
- Focus: testing the tests — the suite should detect logic changes.
- **Verification**: Introduce a small bug (mutate code); the test suite must fail.

### Type annotations (PEP 484)
- **Mandatory**: type hints on function arguments and return values.
  - `def greet(name: str) -> str:`
- Annotate variables only when inference is ambiguous. Annotations = machine-verified docs.
- **Verification**: Run `mypy`; fix any type mismatch errors.

### Constraining types
- Use `T | None` and `A | B` (PEP 604, Python 3.10+); `Optional`/`Union` only on older interpreters. Use `Literal` where needed. Use `Any` sparingly.
- Explicitly handle `None`: unwrap or check before use. Avoid `Any`; it weakens type checking.
- **Verification**: Every `| None` value is checked or unwrapped before use.

### Collections
- Annotate inner types: `list[int]`, `dict[str, int]`. Never raw `list`/`dict` in annotations.
- Prefer abstract types for parameters: `Iterable` or `Sequence` for read-only inputs.

### Type checker config
- Configure `mypy.ini` or `pyproject.toml` (e.g. `--disallow-untyped-defs`, `--no-implicit-optional`).
- **Verification**: Changing a strictness flag should change mypy output as expected.
