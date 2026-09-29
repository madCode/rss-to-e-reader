# rss-to-e-reader

A library that turns RSS feeds and reading lists into an e-reader document:
Collectors gather `ArticleMetadata`, a ListCreator picks and orders it, an
ArticleFetcher turns it into Articles, a FileCreator writes the file and a
Sender delivers it. See README.md.

CI (`.github/workflows/python-mypy-unittest.yml`) runs:

    mypy .
    python -m coverage run --source=base_classes,default_modules,custom_modules -m unittest discover -s tests -p "*_test.py"
    diff-cover coverage.xml --compare-branch=origin/main --fail-under=90

so new lines need tests covering at least 90% of them.

## Comments

A comment is for what the code can't say itself:

- **Why** it is written this way: a constraint, a trade-off, or what goes
  wrong with the obvious alternative.
- **The non-obvious:** a gotcha, an invariant, a surprising dependency.
- **A summary of complex code,** so a reader doesn't have to trace it.

Not:

- **Restating the code.** `# loop over the articles`, `# return the path`,
  or a comment that repeats a well-named function's name in prose. A label
  that says what an ambiguous name refers to is not restating: it tells the
  reader something the name doesn't.
- **Anything that belongs in a PR description or PR comment:** history
  ("used to", "the original version", "since the rewrite"), what was removed
  or deliberately not done and why, and review back-and-forth. That stays
  attached to the change in the PR and the commit message.

A consequence is fine; a changelog is not. "Compare as strings: tt-rss gives
ints, configs may give either" explains the code that is there. "This used
to compare ints" does not.

Docstrings on public classes and functions (the numpy-style `Parameters`
sections) are API documentation, not comments: keep them, and keep them
accurate when a signature changes.

## Tests

A test should be able to catch a plausible regression.

- Test behaviour, not structure: no tests that only check something was
  deleted (`hasattr(...)` is False) or that a comment exists.
- Don't feed code inputs it can never receive just to make a test fail on
  the old version.
- When a change has no behaviour to test (a deletion, a comment, docs), say
  so in the PR rather than inventing a test.
