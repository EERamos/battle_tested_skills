# Notebooks

Read this for `.ipynb` files and for `.py` files run cell by cell. It replaces the *Library* rules at this level; the *Any code* rules in SKILL.md still apply.

## Type hints
- Only on functions that another cell calls. In a `.py` notebook, `# %%` blocks or blocks under a section comment count as cells.
- **Why**: a notebook's bugs are in its data, not its signatures; annotating every throwaway line adds noise without catching anything.

## Code copied between notebooks
- Code that lives in two or more active notebooks moves to a module and is imported.
- Copies that were translated or renamed count as copies too.
- Search the whole project, not only the notebook's folder. Archived notebooks don't count.
- **Why**: copies drift; a fix lands in one and the other keeps producing the old number.
- **Verification**: search the project for the function's body or its distinctive lines, not only its name.

## Saved outputs
- Check that saved outputs come from the current code: re-run before committing.
- Remove paths, server names and other people's data by fixing where they leak from (the print, the config), not by hand-editing the output.
- Clear only the outputs that leak; keep the rest as evidence.
- **Why**: a stale output documents code that no longer exists, and a hand-cleaned one leaks again on the next run.

## Results
- Results someone will quote or reuse go to a file the notebook itself writes. Exploratory prints don't count.
- Numbers quoted in generated text are read from the data, never typed in.
- **Why**: a typed number stays the same when the data changes.

## Tests
- If the notebook has tests, they run the notebook being delivered, with all its checks (`jupyter nbconvert --execute`, or `papermill`).
- Matching a previous version's output proves nothing.
- **Verification**: the test command executes the delivered file end to end and fails when one of its checks fails.

## Editing
- Edit an `.ipynb` as JSON (`nbformat`, or a notebook-aware editor), never with text tools such as `sed` or a regex.
- **Why**: one misplaced quote corrupts the whole file.
