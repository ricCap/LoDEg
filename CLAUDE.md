# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

LoDEg is a log analytics tool for the LODE video-lecture platform. It has two parts:

- `src/lodegML/` — the standalone analytics library (Python 3). Its public API is the facade class `LodegSystem` in `system.py`.
- `src/lodeg_website/` — a Django WebApp that embeds a **copy** of the library at `src/lodeg_website/home/lodegML/`.

Pinned dependencies are in `requirements.txt` (Django 6, pandas 3, scikit-learn 1.9, matplotlib 3.11, pymongo 4; tested on Python 3.14), installed into `.venv/` (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`). A running MongoDB on `mongodb://127.0.0.1:27017` is required for almost everything, tests included.

## Commands

All run from the repo root via the `Makefile`:

```bash
make tests            # generate + mongoimport mock populations, then integration check, logs-integrity tests, unit tests with coverage
make tests i          # interactive: choose which test groups to skip
make tests system     # only test/unit/test_system.py
make check            # verify the WebApp copy of lodegML matches the standalone library
make to_web           # copy src/lodegML -> src/lodeg_website/home/lodegML (rewrites imports)
make from_web         # copy the WebApp library back to src/lodegML (rewrites imports)
make website [PORT]   # python manage.py runserver in src/lodeg_website
make doc              # sphinx-apidoc + html build into docs/
make pep8_check       # pep8 lint
make clean            # remove caches, exports, tools/tmp contents
```

Run a single test module or case (the test files add `src/lodegML` to `sys.path` themselves; mock data must already be imported into MongoDB, e.g. by a prior `make tests`):

```bash
python -m unittest discover -v -s ./test/unit -p test_extractions.py
```

```bash
cd test/unit && python -m unittest -v test_suite.TestPlayPausesExtraction
```

Notes:
- `tools/*.sh` use GNU `sed -i` and `md5sum`; on macOS they need GNU coreutils/sed (e.g. `gsed`) or will fail.
- `make tests` regenerates `test/populations/*.json` via `sample_population.py` / `website_test_population.py` and imports them into the `lodeg` DB (`mockup_population`, `mockup_lessons`, `web_mockup_population`, `web_mockup_lessons`).
- `test/system/test_integrity.py` runs `LodegSystem(debug=False)`, i.e. against the **real** `lodelogs` database.
- Coverage HTML is written to `docs/testsCoverage/` (committed).

## Architecture

### Dual library copies and the `# migrate` convention

The library exists twice: `src/lodegML/` (imports are flat, e.g. `import utility_queries as utils`) and `src/lodeg_website/home/lodegML/` (imports are package-relative, e.g. `from ..lodegML import utility_queries as utils`). `tools/lib_to_web.sh` / `web_to_lib.sh` rewrite **only import lines ending in `# migrate`** with sed. Therefore:

- Any new intra-library import must carry a trailing `# migrate` comment, in one of the forms the sed patterns handle (`import X  # migrate`, `from X import Y  # migrate`, `from configure.configurations import ...  # migrate`).
- Edit one copy, then sync with `make to_web` (or `make from_web`) and confirm with `make check`. Don't let the two drift.
- Exception: `system.py` does a lazy `from ..lodegML import cache` inside `LodegSystem.__init__` (only when a cache is configured) without the marker, so it only works in the WebApp package context.

### Data flow

`LodegSystem` (`system.py`) holds a nested dict tree and delegates work to modules:

```
systemInfo = {'courses': {course_id: courseInfo}, 'last_update': ...}
courseInfo = {'lessons_durations', 'users': {user_id: userInfo}, 'number_of_sessions', course-level stats...}
userInfo   = {'sessions': {session_id: sessionInfo}, user-level stats...}
sessionInfo= {'data': [raw log records], 'lesson_id', session-level stats...}
```

- `mongo_queries.py` — aggregation queries that populate those dicts from the logs and lessons collections.
- `data_extraction.py` — feature extraction at session/user/course level; entry points are `execute_{complete,courseInfo,userInfo,sessionInfo}_extraction`, which cascade downward. Invalid sessions (first record not of type `title`) raise `InvalidSessionException` and are dropped. Unknown lessons raise `LessonNotFoundExeption`, which triggers `mongo_queries.register_lesson` with a default 7200s duration (workaround for issue #52).
- `ml.py` — converts stats to pandas DataFrames (`migrateStatsToDataFrames`) and runs sklearn clustering.
- `auto_plot.py` — matplotlib/mpld3 plots; output depends on `plot_target` (`web` returns HTML/base64, `console` shows figures).
- `import_export.py` — JSON/pickle export/import of `systemInfo`; `cache.py` — Mongo/SQLite cache backends.

### Configuration

`configure/configurations.py` defines named modalities (`default`, `low_mem`, `console`, `web`) with keys like `query_mem_opt`, `keep_user_info`, `keep_session_data`, `ml_mem_opt`, `ml_autorun`, `plot_target`, `cache`, `debug`. `LodegSystem(modality, **overrides)` applies overrides only when the key exists and the type matches. Methods decorated with `_takes_config` read defaults for those keys from the system config and require them as keyword args.

`debug=True` connects to DB `lodeg` with the `web_mockup_*` collections; `debug=False` connects to DB `lodelogs` with `logs` / `lessons_metadata`.

### WebApp

`home/views.py` instantiates a single module-level `LodegSystem(modality='web', debug=False)` shared across requests. Django's own DB is SQLite (`db.sqlite3`, gitignored); `home.models.LodegUser` maps Django users to LODE user ids.
