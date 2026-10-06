# Data and pandas

Read this when the code loads, transforms or caches tabular data. It adds to the *Any code* rules in SKILL.md (NaN handling lives there).

## Loading
- Check dtypes right after loading, and set them explicitly (`dtype=`, `parse_dates=`) instead of trusting inference.
- Align indexes explicitly before operating on two frames or series (`a.align(b, join="inner")`, or `reindex`), never by implicit alignment.
- **Why**: pandas aligns on labels without warning; a misaligned operation returns NaN or the wrong row, not an error.
- **Verification**: after each load, `df.dtypes` matches the expected schema; every binary operation between two frames follows an explicit `align`/`reindex` or a shared index built on purpose.

## Operating
- Don't iterate rows for arithmetic (`iterrows`, `itertuples` loops, `apply(axis=1)`); use vectorized operations.
- Take `.copy()` when you slice a frame you will modify, and don't chain assignments (`df[a][b] = x`); use `df.loc[rows, col] = x`.
- A ratio whose denominator has no meaning at ≤ 0 (P/E, debt/EBITDA) is masked to NaN, and the masked cases are counted and reported. Signed ratios where a negative denominator is valid (a hedge ratio, a change over a negative base) stay as they are.
- **Why**: row loops are slow and hide logic; chained assignment may write to a temporary copy; a P/E over negative earnings looks like a valid number.
- **Verification**: grep `iterrows`, `itertuples`, `axis=1` and `][`-assignments; every ratio of the first kind has its mask and a count next to it.

## Caches
- A cache key includes every input that changes the content: as-of date, universe, parameters, and the code version when the logic changes.
- A set of ids goes into the key as a hash of the sorted ids, never as their count.
- If the cache is built from a file, the key also includes that file's version, or its size and modification time.
- **Why**: a key that misses an input returns stale data that looks fresh.
- **Verification**: change one input at a time and confirm the key changes.

## Native crashes
- A crash inside a native library (segfault, abort) can't be caught with `try`/`except`. Test the risky call in a subprocess and check its return code.
- **Why**: the parent process dies with no traceback, and the `except` never runs.
