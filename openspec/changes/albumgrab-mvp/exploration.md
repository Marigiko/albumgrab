# Exploration: albumgrab-mvp

Date: 2026-09-15 | Phase: sdd-explore | Store: both (this file + engram `sdd/albumgrab-mvp/explore`)

## Current State

Brand-new repository (`/mnt/d/Projects/albumgrab`): no source code, only SDD scaffolding
(`openspec/config.yaml`, `.atl/skill-registry.md`, git on `main`, zero commits, no remote).
All feasibility findings below are from CURRENT official docs, not code.

## Pillar Feasibility Verdicts

| Pillar | Verdict | Evidence (versions verified 2026-09-15) |
|---|---|---|
| ytmusicapi discovery chain (artist → albums → tracks) | **GREEN** | v1.12.2 (2026-08-08). Call chain verified against stable docs. |
| yt-dlp audio download → MP3 + embedded thumbnail | **GREEN** (with mandatory external JS-runtime caveat) | 2026.07.04 on PATH; EJS/Deno requirement effective since 2025.11.12. |
| mutagen ID3v2 + APIC album art | **GREEN** | Docs verified: `ID3` + `APIC` + `PictureType.COVER_FRONT` + `save()`. |
| ffmpeg presence + transcode | **GREEN** | ffmpeg 4.4.2 on PATH (verified at sdd-init). Runtime check via `shutil.which`. |

Overall: **feasible as an OWN thin tool. No pillar is red.**

## 1. ytmusicapi — verified API surface (v1.12.2)

Exact call chain (all signatures confirmed in stable docs):

```python
from ytmusicapi import YTMusic
ytm = YTMusic()                                   # unauthenticated: search + browsing
results = ytm.search(artist_name, filter="artists")   # → entries with browseId (= channelId)
artist  = ytm.get_artist(channelId)                   # → artist["albums"] = {browseId, params, results}
albums  = ytm.get_artist_albums(
    channelId,                    # browseId of the artist
    artist["albums"]["params"],   # params obtained by get_artist() — REQUIRED
    limit=100,                    # None = all; default 100
    order="Recency",              # 'Recency' | 'Popularity' | 'Alphabetical order' | None
)
album   = ytm.get_album(browseId)                     # browseId = "MPREb_..." from album entry
```

- `get_album()` returns: `title`, `type` ("Album"), `artists`, `year`, `trackCount`,
  `duration_seconds`, **`audioPlaylistId`** (`OLAK5uy_...`), and `tracks[]` with
  `videoId`, `title`, `artists[]`, `album`, `duration`, `duration_seconds`,
  `trackNumber`, `isAvailable`, `isExplicit`, `thumbnails`.
- `get_artist()` also exposes `singles` (same browseId+params pattern) — cheap future extension.

**Auth:** `YTMusic()` (no args) is documented for "retrieving playlist content or searching";
browsing endpoints (`get_artist`/`get_artist_albums`/`get_album`) work unauthenticated in
practice (spotDL relies on this). Docs only *explicitly* bless search + playlist for the
no-auth path → include a 5-minute smoke check in the apply phase. Optional upgrades:
`browser.json` (pasted browser headers via `ytmusicapi.setup()`) or OAuth
(`OAuthCredentials(client_id, client_secret)` + `oauth.json`). **MVP needs none.**

**2025-2026 stability notes:** it is an unofficial API scraping YouTube Music's internal
responses. Changelog shows recurring breakage + fixes: `get_artist` two-column layout
(#929, fixed 1.12.2), album-year parsing (#899, fixed 1.12.0), missing-subtitle album
entries (#907), "adapt parsing to YT server changes" (#963/#961). Pattern: **pin a floor
version (`ytmusicapi>=1.12`), expect occasional silent breakage, keep dependency fresh.**

## 2. yt-dlp — verified surface (2026.07.04 on PATH)

**Python embedding (official, README "Embedding yt-dlp"):**

```python
from yt_dlp import YoutubeDL
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": "...",                 # per-track path
    "writethumbnail": True,
    "postprocessors": [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},  # or "192"
        {"key": "EmbedThumbnail"},    # mutagen is yt-dlp's own embedder for MP3 covers
    ],
    # anti-rate-limit (MiniDownloader pattern, native syntax confirmed):
    # "extractor_args": {"youtube": {"player_client": ["android", "ios", "web", "web_music"]}},
    # "sleep_interval": ..., "max_sleep_interval": ..., "retries": ...,
    # cookies: "cookiefile": "/path/cookies.txt"  or  "cookiesfrombrowser": ("chrome",),
}
with YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])
```

- `--extractor-args "youtube:player-client=tv,mweb"` syntax confirmed in README → maps to
  `extractor_args` dict in the Python API. Progress reporting available via `progress_hooks`.
- ffmpeg resolution: `ffmpeg_location` param; PATH fallback is automatic.
- Some Python-API options are flagged experimental/deprecated (removed with deprecation
  warnings) — pin behavior tests around the stable core shown above.

**CRITICAL 2025-2026 posture — external JavaScript runtime:** since yt-dlp **2025.11.12**
(announcement issue #15012; PR #14157 merged 2025-10-31), full YouTube support requires an
external JS runtime + `yt-dlp-ejs` challenge-solver scripts. **Deno ≥ 2.0.0 is the default
and recommended runtime** (alternatives Node ≥ 20 / QuickJS / Bun must be enabled with
`--js-runtimes`). Without any runtime, YouTube support is "deprecated": nsig solving fails →
throttled downloads and missing formats, worsening over time. PyPI users need
`yt-dlp[default]` + deno on PATH. **Implication for albumgrab: add a `shutil.which("deno")`
pre-flight warning (not a hard fail) alongside the ffmpeg check, and document the
dependency. This validates spotDL's Deno mention.**

**subprocess vs Python API:** README officially supports embedding (`import yt_dlp`), and
`progress_hooks` + `extractor_args` make the in-process API the better fit for a Typer CLI
progress display. Caveat: yt-dlp moves fast; keep it loosely pinned (`yt-dlp>=2026.7`) —
*old* yt-dlp versions rot against YouTube faster than new ones break APIs. subprocess is a
valid isolation fallback if API churn bites; decide in design.

## 3. mutagen — verified surface

- **APIC album art (raw ID3, confirmed):**
  ```python
  from mutagen.id3 import ID3, APIC, PictureType
  tags = ID3(path)                      # ID3NoHeaderError on fresh file → ID3()
  tags.setall("APIC", [APIC(encoding=3, mime="image/jpeg",
                       type=PictureType.COVER_FRONT, data=jpeg_bytes)])
  tags.save()
  ```
  Multiple images require unique HashKeys (`salt` trick) — irrelevant here (one cover).
- **EasyID3:** dict-like wrapper, case-insensitive keys, only a *subset* of ID3 frames by
  default (`EasyID3.valid_keys.keys()` to enumerate). Artist/album/title/tracknumber/date
  are covered; **APIC is NOT reachable via EasyID3** — binary frames require raw ID3.
- **Consequence for design:** simplest robust path is raw ID3 frames throughout
  (`TIT2/TPE1/TALB/TRCK/TDRC/TCON/TPE2 + APIC`) — one code path, no EasyID3/raw mix.
  Feasibility unaffected.

## 4. ffmpeg

Presence check `shutil.which("ffmpeg")` (and `ffprobe`) at startup; 4.4.2 already on PATH.
`FFmpegExtractAudio` + `EmbedThumbnail` postprocessors consume it automatically. No deep
dive needed. **Audio-ceiling honesty note (user constraint):** YouTube serves ~128 kbps
AAC/Opus (≈256 kbps with YT Music Premium). MP3 output is a transcode of a lossy source —
final quality is capped by the stream, not by the `preferredquality` setting. Surface this
in README/UI; do not advertise "CD quality".

## Approaches Considered (per orchestrator decision — own tool, no fork)

1. **Own thin CLI (Chosen)** — Typer front-end orchestrating ytmusicapi + yt-dlp + mutagen.
   - Pros: full control, no Spotify dependency, tiny surface, all pillars verified GREEN.
   - Cons: owns the anti-rate-limit and UX problems that forks already solved.
   - Effort: Medium (MVP scope).
2. **Fork spotDL** — rejected by user: Spotify-driven, wrong product shape.
   - Effort: Low start, High ongoing (upstream sync).

## Open Design Questions (to resolve in sdd-design — NOT decided here)

1. **Selection UX:** numbered multi-select terminal prompt (Typer/rich, ~0 deps) vs
   Textual TUI (richer, heavier). Implication: TUI adds a dependency + test complexity;
   prompt keeps strict-TDD simple.
2. **Output layout:** `{artist}/{album}/{NN - track}.mp3` (library-shaped) vs flat
   `{artist} - {album} - {NN track}.mp3`. Implication: sanitization rules + replay/rename
   risk differ.
3. **No YT Music match for a track:** skip + report vs fail the album vs interactive
   manual search fallback. Implication: `isAvailable: false` and region-locked tracks make
   this a *when*, not *if*.
4. **Album-as-videos edge case:** `get_album` gives per-track `videoId`s AND an
   `audioPlaylistId` (`OLAK5uy_...`). Per-track downloads (precise tagging, resumable) vs
   one playlist download (fewer requests, unordered/unmatched risk). Some "albums" on YT
   are only video playlists → fallback strategy needed.
5. **Credentials/config location:** XDG `~/.config/albumgrab/` (browser.json optional,
   cookies.txt optional, config.toml) vs in-project. Implication: gitignore + multi-machine.
6. **Rate-limit / backoff:** `sleep_interval` + `player_client` cycling (android/ios/web/
   web_music) + retry-on-429; how aggressive before cookies become mandatory.
7. **yt-dlp invocation:** in-process Python API (progress hooks, extractor_args) vs
   subprocess isolation (API-churn shield). Lean in-process; confirm in design.
8. **Tagging path:** raw ID3 frames only (recommended by findings) vs EasyID3+ID3 mix.

## Recommendation

Proceed to sdd-propose. Scope the MVP as: `search artist → list albums → multi-select →
per-track yt-dlp download → MP3 transcode → mutagen tag + cover embed`, unauthenticated
ytmusicapi, per-track downloads, raw ID3 tagging. Pre-flight checks: ffmpeg (hard),
deno (soft warning). Publish the ~128 kbps source ceiling in user-facing copy.

## Risks

- **Unofficial API fragility (ytmusicapi):** YT Music layout changes break parsers
  periodically; mitigations: version floor + update cadence + narrow smoke tests.
- **JS-runtime dependency (yt-dlp/Deno):** without Deno, downloads degrade (throttle,
  missing formats) and will worsen; pre-flight check + docs mandatory.
- **Quality ceiling:** ~128 kbps AAC source → MP3 transcode; set expectations honestly.
- **Anti-bot escalation (429/403, PO tokens):** MiniDownloader-style client cycling and
  cookies may become required; keep as config, not code constants.
- **Match/availability gaps:** region locks and `isAvailable: false` guarantee partial
  album failures; behavior must be designed, not improvised.

## Ready for Proposal

**Yes** — all pillars verified against current docs; no blocking unknowns. Hand the open
design questions (1-8) to sdd-design via the proposal's approach section.
