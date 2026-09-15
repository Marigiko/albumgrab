# Delta for cli-runtime

## ADDED Requirements

### Requirement: CLI entry point

The system SHALL provide an `albumgrab` command that takes an artist name argument and an output directory option, reports the resolved output root at run start, and then runs the discover → select → download → tag pipeline.

#### Scenario: Invocation runs the pipeline

- GIVEN ffmpeg is present and YouTube Music is reachable
- WHEN the user runs `albumgrab "Some Artist" --output ./music` and selects albums
- THEN the pipeline runs to completion and tagged MP3s appear under `./music`

### Requirement: Preflight checks

Before any network work or download, the system MUST check required binaries. If ffmpeg (or ffprobe) is missing, the system MUST print a clear actionable message and exit non-zero without downloading. If Deno is missing, the system MUST print a warning that downloads may degrade and continue.

#### Scenario: Missing ffmpeg hard-fails

- GIVEN ffmpeg is not on PATH
- WHEN the user starts any run
- THEN the system explains ffmpeg is required, exits non-zero, and downloads nothing

#### Scenario: Missing deno warns but continues

- GIVEN ffmpeg present and Deno absent
- WHEN the user starts a run
- THEN the system warns that YouTube downloads may throttle or fail
- AND the run proceeds

### Requirement: Progress display

During processing, the system SHALL show per-track progress — current track vs. total for the album, plus the track title — so the user can follow a long run.

#### Scenario: Progress shown

- GIVEN a selected album with 10 tracks
- WHEN track 3 is being processed
- THEN the display shows position 3 of 10 and the track title

### Requirement: XDG configuration with defaults

The system MUST load `config.toml` from the XDG config directory (`~/.config/albumgrab/`, honoring `XDG_CONFIG_HOME`). A missing config file MUST NOT be an error: built-in defaults apply. The config MUST drive rate-limit behavior — sleep interval between requests, ordered player-client list, and backoff-and-retry on HTTP 429 — and MAY point to an optional cookies file. Invalid config values MUST fail with a clear message identifying the offending key.

#### Scenario: Defaults without config file

- GIVEN no config file exists in the XDG directory
- WHEN a run starts
- THEN built-in defaults apply and the run proceeds normally

#### Scenario: Rate-limit knobs honored

- GIVEN a config specifying a sleep interval and a player-client list
- WHEN downloads run
- THEN requests are paced by the sleep interval and clients are used in the configured order

#### Scenario: 429 backoff

- GIVEN YouTube responds 429 during a run
- WHEN the system receives the response
- THEN it backs off and retries per the configured policy instead of crashing

#### Scenario: Invalid config rejected

- GIVEN a config file with an invalid value for a known key
- WHEN a run starts
- THEN the system reports the offending key with a clear message and exits non-zero

### Requirement: Honest quality-ceiling notice

The system SHOULD surface at startup or in help output, and the README MUST state, that output is transcoded from ~128 kbps YouTube source streams and is therefore quality-capped. User-facing copy MUST NOT claim lossless or "CD quality" output.

#### Scenario: Notice displayed

- GIVEN a user starts the CLI or reads the README
- WHEN they consult the user-facing copy
- THEN the ~128 kbps source-quality ceiling is stated and no lossless claim appears
