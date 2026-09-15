# Tasks: albumgrab-mvp

Date: 2026-09-15 | Phase: sdd-tasks | Store: both (this file + engram `sdd/albumgrab-mvp/tasks`)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,300–1,500 total (incl. full 35-scenario strict-TDD suite; refines proposal's 600–900) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 (each ≤400 est. changed lines, incl. tests) |
| Delivery strategy | auto-chain |
| Chain strategy | pending — user confirms stacked-to-main vs feature-branch-chain before apply |

```text
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High
```

Decision needed before apply: No (auto-chain; chain_strategy pending user confirmation). Per-slice estimates: Slice 1 ≈ 360 · Slice 2 ≈ 340 · Slice 3 ≈ 380 · Slice 4 ≈ 395. These are planning guards: if any slice trends >400 at apply, trim order = split its test file into a follow-up `test:` commit inside the same chain.

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Scaffold + pure config & layout/sanitization | PR 1 | `uv run pytest tests/unit/test_config.py tests/unit/test_layout.py` | N/A — pure functions, pytest only (per design test-strategy "Unit (pure)") | Revert PR 1; greenfield, nothing downstream |
| 2 | Selection parsing + discovery adapter + preflight | PR 2 | `uv run pytest tests/unit/test_selection.py tests/unit/test_discovery.py tests/unit/test_preflight.py` | Manual 5-min live browse check (task 2.7), network-marked | Revert PR 2; PR 1 modules untouched |
| 3 | CLI entry + selection re-prompt loop + tagging | PR 3 | `uv run pytest tests/unit/test_cli.py tests/unit/test_tagging.py` | CliRunner + FakeCatalog; tmp-path MP3 fixture | Revert PR 3; CLI returns to stub; PR 1–2 pure modules stay valid |
| 4 | Downloader + pipeline + report + README | PR 4 | `uv run pytest` (full suite = acceptance) | CliRunner e2e with FakeCatalog/FakeDownloader (real network mocked in CI) | Revert PR 4; interactive browse/select (PR 3 state) still works |

Base boundaries — stacked-to-main: each PR targets `main`, merged 1→4. feature-branch-chain: draft tracker `feature/albumgrab-mvp` (no-merge); PR 1 base = tracker; PR 2 base = PR 1 branch; PR 3 base = PR 2 branch; PR 4 base = PR 3 branch. If a child diff shows previous slices, retarget/rebase before review.

Threat matrix: all four rows N/A per design — no RED tasks manufactured; sanitizer invariant tests (1.4) carry the subprocess/shell boundary. Serial downloads only — no concurrency task exists by design (rejected alternative); do not add a concurrency knob or flag.

## Phase 1 [Slice 1 — PR 1]: Scaffold + Pure Foundations

- [x] 1.1 Scaffold `pyproject.toml` (deps pinned: `ytmusicapi>=1.12`, `yt-dlp>=2026.7`, `mutagen`, `typer`; dev: pytest, ruff, pytest-cov; `[project.scripts] albumgrab`; ruff line-length 100; pytest markers `live` skipped by default), `.gitignore`, `src/albumgrab/__init__.py`, minimal `src/albumgrab/cli.py` stub (Typer app; fleshed out in Slice 3). AC: `uv run pytest` (empty pass) and `uv run albumgrab --help` both work.
- [x] 1.2 [RED] `tests/unit/test_config.py`: defaults apply with no config file (cli-runtime "defaults"); `XDG_CONFIG_HOME` honored; unknown key rejected naming the key; invalid value rejected naming the key (closed schema); `resolve_output_root` precedence CLI > `[output] root` > `./albumgrab-music`. AC: fails for the right reason (ImportError → assertion).
- [x] 1.3 [GREEN] `src/albumgrab/config.py`: frozen `Config` dataclass, `DEFAULTS`, `load()` + validation, `resolve_output_root()`. AC: 1.2 green; every failure message names the offending key.
- [x] 1.4 [RED] `tests/unit/test_layout.py` invariant-pinned: invalid + control chars → `_`; reserved device names (case-insensitive) suffixed `_`; >120 chars truncated; trailing dots/spaces stripped; empty → `untitled`; `NN` prefix and `.mp3` never altered; `build_track_path` → `{output}/{artist}/{album}/03 - Song.mp3`; `ensure_album_dir` creates missing dirs (tmp_path). AC: fails first.
- [x] 1.5 [GREEN] `src/albumgrab/layout.py`: `sanitize_segment`, `build_track_path`, `ensure_album_dir(mkdir(parents=True, exist_ok=True))`. AC: 1.4 green — library-layout scenarios L1–L5 pass.
- [x] 1.6 [REFACTOR] `uv run ruff check .` clean; `uv run pytest --cov` ≥80% on slice modules; commit `feat: scaffold albumgrab package` + `feat: config and layout pure modules` (tests with code).

**Slice boundary** — Start: empty repo. Finish: installable package, config + layout pure modules green. Verify: `uv run pytest` green. Rollback: revert PR 1.

## Phase 2 [Slice 2 — PR 2]: Selection Parsing + Discovery + Preflight

- [x] 2.1 [RED] `tests/unit/test_selection.py` — all 7 album-selection scenarios: single number; inclusive range "2-5"; mixed "1,3-5,5,7" dedup once each; "all" case-insensitive; out-of-range "9"; garbage "1,x,2" names "x"; inverted "5-2". AC: fails first; asserts `InvalidSelection(token)`.
- [x] 2.2 [GREEN] `src/albumgrab/selection.py`: `parse_selection(raw, count) -> list[int]` raising `InvalidSelection(token)`, union + dedup, sorted. AC: 2.1 green.
- [x] 2.3 [RED] `tests/unit/test_discovery.py` with recorded ytmusicapi payload fixtures (no network): payload → `Artist`/`AlbumRef` (title, year, trackCount)/`Album` (tracks[], audio_playlist_id, cover_url) mapping; no-match search → `None`. AC: fails first.
- [x] 2.4 [GREEN] `src/albumgrab/discovery.py`: metadata dataclasses + `Catalog` protocol + `YTMusicCatalog` (`search_artist`, `list_albums`, `get_album`) per design interfaces. AC: 2.3 green; unit tests hit no network.
- [x] 2.5 [RED] `tests/unit/test_preflight.py` (monkeypatch `shutil.which`): ffmpeg or ffprobe missing → actionable error, abort before downloads (cli-runtime "missing ffmpeg"); Deno missing → warning, continue. AC: fails first.
- [x] 2.6 [GREEN] `src/albumgrab/preflight.py`: ffmpeg/ffprobe hard check, Deno soft warn. AC: 2.5 green.
- [x] 2.7 **Live smoke check (verification task)**: 5-minute unauthenticated YT Music browse via `YTMusicCatalog` on real network — search one artist → list albums → `get_album` one album; record result in PR description. AC: real browse chain confirmed end-to-end; no downloads performed; CI equivalent stays mocked (`live` marker skipped). *(PASS 2026-09-15: Daft Punk → 10 albums → "Random Access Memories (Drumless Edition)" 13 tracks, cover + audioPlaylistId present, zero downloads.)*
- [ ] 2.8 [REFACTOR] ruff clean; coverage ≥80% slice modules; commits `feat: selection parser`, `feat: ytmusicapi catalog adapter`, `feat: preflight checks` (each with its tests).

**Slice boundary** — Start: PR 1 merged. Finish: parse/browse/preflight units green + live browse verified. Verify: `uv run pytest` green. Rollback: revert PR 2.

## Phase 3 [Slice 3 — PR 3]: CLI Entry + Selection Loop + Tagging

- [ ] 3.1 [RED] `tests/unit/test_cli.py` (CliRunner + FakeCatalog): unknown artist → "artist not found" + exit 1 with zero downloads (artist-discovery); albums listed numbered with title, year, track count; zero albums → "No albums found for '<artist>'" + exit 0 (graceful); resolved output root echoed at run start; ~128 kbps quality-ceiling notice shown, no lossless claim (cli-runtime "notice"). AC: fails first.
- [ ] 3.2 [RED] prompt-loop tests in `test_cli.py`: simulated stdin — invalid token, out-of-range, inverted range each name the offending token and re-prompt until valid input; valid input proceeds (album-selection rejection scenarios at loop level). AC: fails first.
- [ ] 3.3 [GREEN] `src/albumgrab/cli.py` (replaces stub): Typer app (artist arg, `--output` opt), preflight call, config load, echo root, search → exit 1 on None, numbered listing, zero-albums graceful exit 0, prompt loop **owned by cli** (catches `InvalidSelection`, re-prompts), notice line. AC: 3.1 + 3.2 green. Note: zero-albums check moves into pipeline in 4.4 per design ownership — tests unchanged (REFACTOR move).
- [ ] 3.4 [RED] `tests/unit/test_tagging.py` (tmp_path minimal MP3 fixture): read-back of TIT2/TPE1/TALB/TRCK/TDRC/TCON/TPE2 with correct values; TRCK "4/12" for track 4 of 12; APIC present with `PictureType.COVER_FRONT`; missing cover → text frames still written + warning, no crash (all 4 mp3-tagging scenarios). AC: fails first.
- [ ] 3.5 [GREEN] `src/albumgrab/tagging.py`: pure `compose_frames(album, track)` + `write_tags(path, frames, cover_bytes | None)` (mutagen raw ID3 frames; EasyID3 not used). AC: 3.4 green.
- [ ] 3.6 [REFACTOR] ruff clean; coverage ≥80% slice modules; commits `feat: interactive cli with selection loop`, `feat: id3 tagging with cover embed` (tests with code).

**Slice boundary** — Start: PR 2 merged. Finish: `albumgrab "Artist"` browses, lists, re-prompts, selects; tagging standalone green. Verify: `uv run pytest` green. Rollback: revert PR 3.

## Phase 4 [Slice 4 — PR 4]: Downloader + Pipeline + Report + README

- [ ] 4.1 [RED] `tests/unit/test_downloader.py`: opts assert `format: bestaudio/best`, `FFmpegExtractAudio` → mp3, per-track `outtmpl`, no `EmbedThumbnail` (tagging is ours), cookies/ffmpeg_location passthrough; playlist fallback invoked when `video_id` is None and `audio_playlist_id` exists (track-acquisition "fallback"); **source-caps assertion** — lossy-source transcode opts only, no lossless claim anywhere (track-acquisition "source caps"). AC: fails first.
- [ ] 4.2 [GREEN] `src/albumgrab/downloader.py`: `Downloader` protocol + `YtDlpDownloader` (in-process) + opts builder + playlist fallback matched by position/title. AC: 4.1 green.
- [ ] 4.3 [RED] `tests/unit/test_pipeline.py` (CliRunner e2e, FakeCatalog + FakeDownloader): happy path → exactly one MP3 per available track at its layout path; region-locked track skipped, others downloaded, run completes; end-of-run report names each skipped track with album + reason + counts; download failure recorded, remaining tracks + album continue; 429 → backoff `backoff_base`×attempt up to `retries`, then record + continue (monkeypatched sleep); sleep pacing + ordered `player_client` reflected in opts; progress line "[3/10] Track Title"; zero-albums regression still exit 0. AC: fails first.
- [ ] 4.4 [GREEN] `src/albumgrab/pipeline.py`: strictly serial run loop, `ensure_album_dir` once per album before first write, per-track `build_track_path` → download → tag → `TrackOutcome`, backoff retry, knobs → downloader opts, progress echo, cover fetched once per album (stdlib urllib; failure → warn, text frames only), `RunReport.render`, exit 0 whenever run completes; absorbs zero-albums check from cli (design ownership). AC: 4.3 green — track-acquisition T1–T6 and cli-runtime C1/C4/C6/C7 pass.
- [ ] 4.5 [RED+GREEN] `tests/unit/test_report.py` + `src/albumgrab/report.py`: `TrackOutcome`, `RunReport.render` — one row per skipped/failed track `{artist, album, "NN title", stage, reason}` + downloaded/skipped/failed counts. AC: red then green; pure module.
- [ ] 4.6 `README.md`: usage, prerequisites (ffmpeg+ffprobe required, Deno ≥2.0 warn-only), **~128 kbps source-quality ceiling stated; no lossless/CD-quality claim** (README half of cli-runtime "notice"); rollback = delete output dir + XDG config. AC: notice scenario fully covered.
- [ ] 4.7 [REFACTOR] full suite `uv run pytest` green; `uv run pytest --cov` ≥80% (sdd-verify gate); ruff clean; commits `feat: yt-dlp downloader adapter`, `feat: serial pipeline with report`, `docs: readme with quality ceiling` (tests with code).

**Slice boundary** — Start: PR 3 merged. Finish: full pipeline e2e green with fakes; README complete. Verify: `uv run pytest` green (acceptance). Rollback: revert PR 4 → interactive browse/select still works.

## Spec Scenario Traceability (35/35)

Layers per design "Testing Strategy" table — not re-invented here.

| Capability (count) | Scenarios | Tasks |
|---|---|---|
| library-layout (5) | layout applied · dirs on demand · invalid chars · reserved name · overlong | 1.4, 1.5 |
| album-selection (7) | single · range · mixed dedup · all · out-of-range · garbage · inverted | 2.1, 2.2 (+ 3.2, 3.3 loop) |
| artist-discovery (4) | known resolves · unknown fails · albums listed · zero albums | 2.3, 2.4 (adapter) + 3.1, 3.3 (CLI) |
| mp3-tagging (4) | tags written · TRCK 4/12 · APIC cover · missing-cover degrade | 3.4, 3.5 |
| cli-runtime (9) | invocation runs pipeline · ffmpeg hard-fail · deno warn · progress · defaults · knobs · 429 backoff · invalid config · notice | 1.2/1.3 (defaults, invalid config) · 2.5/2.6 (ffmpeg, deno) · 3.1/3.3 (notice, echo) · 4.3/4.4 (invocation, progress, knobs, 429) · 4.6 (README notice) |
| track-acquisition (6) | download+transcode · source caps · playlist fallback · region-locked skip · skip report · error contained | 4.1, 4.2 (opts, fallback, caps) + 4.3, 4.4 (e2e) |

Live smoke: task 2.7 (slice introducing the discovery adapter). Total = 35 scenarios, every one mapped to at least one task's tests.
