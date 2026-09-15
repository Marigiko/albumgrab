# Proposal: albumgrab-mvp

Date: 2026-09-15 | Phase: sdd-propose | Store: both (this file + engram `sdd/albumgrab-mvp/proposal`)

## Intent

CLI `albumgrab`: artist name → YouTube Music album list → multi-select → download every track of selected albums as MP3 (ID3v2 tags + embedded album art), organized under an output directory. Why: existing tools are Spotify-driven or tag-incomplete (spotDL fork rejected in exploration); all four pillars (ytmusicapi, yt-dlp, mutagen, ffmpeg) verified GREEN against current docs.

**Honest quality ceiling (user-facing):** YouTube serves ~128 kbps AAC/Opus; MP3 output is a lossy→lossy transcode capped by the source. README/UI must state this; never claim "CD quality".

## Scope

### In Scope

- Artist search + album listing (ytmusicapi, unauthenticated)
- Numbered multi-select album picker (ranges, "all")
- Per-track yt-dlp download → MP3 transcode → mutagen ID3v2 + APIC cover
- `{output}/{artist}/{album}/{NN - track}.mp3` layout + filename sanitization
- Preflight (ffmpeg hard-fail, deno soft-warn), XDG config dir, rate-limit knobs as config
- Skip + end-of-run report for unavailable/region-locked tracks

### Out of Scope (non-goals)

- No Spotify/non-YouTube sources; no GUI; no TUI framework; no Liked-songs/playlist sync
- No OAuth in MVP (browser.json/cookies stay optional config upgrades)
- No singles/videos artist pages, lyrics, watch mode

## Capabilities

> Contract with sdd-spec. `openspec/specs/` is empty (greenfield) → all capabilities NEW.

### New Capabilities

- `artist-discovery`: resolve artist by name; list albums (year, trackCount)
- `album-selection`: numbered multi-select prompt; parse ranges/"all"
- `track-acquisition`: per-track videoId download, MP3 transcode, playlist fallback (video-only albums), skip+report
- `mp3-tagging`: raw ID3v2 frames (TIT2/TPE1/TALB/TRCK/TDRC/TCON/TPE2) + APIC cover embed
- `library-layout`: output organization + cross-platform sanitization rules
- `cli-runtime`: Typer entry point, preflight, progress display, XDG + rate-limit config

### Modified Capabilities

- None (greenfield; no existing specs)

## Approach

Own thin CLI (exploration's chosen route): Typer over ytmusicapi + yt-dlp + mutagen. **Auto mode:** the 8 exploration design questions are resolved below as ASSUMPTIONS — sdd-design confirms or overrides each.

| # | Question | Assumed resolution |
|---|----------|--------------------|
| 1 | Selection UX | Numbered multi-select prompt; no Textual |
| 2 | Output layout | `{artist}/{album}/{NN - track}.mp3` |
| 3 | Unavailable track | Skip + report; never fail the whole album |
| 4 | Download unit | Per-track videoIds; `audioPlaylistId` fallback for video-only albums |
| 5 | Config location | XDG `~/.config/albumgrab/` (config.toml; browser.json/cookies optional) |
| 6 | Rate limiting | sleep_interval + player_client cycling + 429 backoff, config-driven |
| 7 | yt-dlp invocation | In-process API (progress_hooks), loose pin `>=2026.7`, adapter-isolated for subprocess swap |
| 8 | Tagging path | Raw ID3 frames only (EasyID3 lacks APIC) |

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `pyproject.toml` | New | Package, deps, `albumgrab` entry point, pytest/ruff config |
| `src/albumgrab/` | New | CLI + discovery/selection/download/tagging/layout modules |
| `tests/` | New | Strict-TDD suite (`uv run pytest`) |
| `README.md` | New | Usage, prerequisites, quality-ceiling notice |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| ytmusicapi YT-layout breakage | Medium | Floor pin `>=1.12`, narrow smoke tests, fast bumps |
| yt-dlp churn / missing Deno | High | Loose pin, preflight warning, adapter isolation |
| Anti-bot escalation (429/403/PO tokens) | Medium | Config-driven cycling/sleep; optional cookies |
| Availability/region gaps | High (certain) | Skip+report is spec'd behavior |

## Rollback Plan

- Git: no source commits on `main` yet; each chained PR slice independently revertable (Conventional Commits).
- Dependencies: floor pins — revert lockfile to last-green `ytmusicapi`/`yt-dlp`.
- Architecture: yt-dlp behind a downloader adapter → swap in-process for subprocess without touching CLI/tagging layers.
- Data: writes confined to output dir + XDG config; rollback = delete both.

## Dependencies

- Python 3.11+/uv; `ytmusicapi>=1.12`, `yt-dlp>=2026.7`, `mutagen`, `typer`; dev: pytest, ruff, pytest-cov
- Binaries: ffmpeg+ffprobe (required), Deno ≥ 2.0 (yt-dlp YouTube requirement since 2025.11.12; warn-only preflight)

## Testing Approach

Strict TDD (`uv run pytest`, RED-GREEN-REFACTOR). Unit-testable with fakes: selection parsing, sanitization, tag composition (mutagen on temp files), layout paths, config loading, preflight checks. Live YT Music browsing/downloads: smoke tests mocked in CI, real-network runs marked optional; 5-minute unauthenticated smoke check during apply (per exploration).

## Delivery Forecast

Whole tool ≈ 600–900 changed lines incl. tests → exceeds the 400-line review budget as one slice. **Decision needed before apply: No** (auto-chain pre-selected) · **Chained PRs recommended: Yes** · **400-line budget risk: High**. sdd-tasks MUST slice chained work units (e.g., scaffold+discovery → selection+layout → download+tagging → preflight+config+docs).

## Success Criteria

- [ ] `albumgrab "<artist>"` lists albums; multi-select (ranges/"all") honored
- [ ] Every MP3 carries ID3v2 tags + embedded cover at `{output}/{artist}/{album}/{NN - track}.mp3`
- [ ] Unavailable tracks skipped + reported; partial failures don't abort the run
- [ ] Preflight: ffmpeg hard-fails, deno warns
- [ ] `uv run pytest` green, coverage ≥ 80%; README states the ~128 kbps ceiling
