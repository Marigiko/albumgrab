# Delta for track-acquisition

## ADDED Requirements

### Requirement: Per-track download and MP3 transcode

For each track of a selected album, the system MUST download that track's audio using its own track identifier and transcode it to an MP3 file. The resulting MP3's fidelity SHALL be capped by the lossy source stream (~128 kbps); the system MUST NOT claim higher fidelity than the source provides.

#### Scenario: Track downloaded and transcoded

- GIVEN a selected album whose tracks each expose an identifier
- WHEN the system processes the album
- THEN each track yields exactly one MP3 file at its layout path

#### Scenario: Source caps output quality

- GIVEN a source stream of ~128 kbps
- WHEN the track is transcoded to MP3
- THEN the output is a transcode of that stream and no higher quality is claimed

### Requirement: Video-only album fallback

When an album does not expose per-track identifiers but exposes an audio playlist identifier, the system SHALL fall back to that audio playlist to obtain each track's audio.

#### Scenario: Fallback produces all tracks

- GIVEN a video-only album with an audio playlist identifier
- WHEN the system processes that album
- THEN audio is obtained via the playlist fallback
- AND one tagged MP3 per track is still produced

### Requirement: Skip and report on unavailable tracks

The system MUST skip tracks that are unavailable or region-locked, recording the track and the reason. A skipped or failed track MUST NOT abort the remaining tracks, the album, or the run. At the end of the run, the system SHALL print a report listing every skipped track with its reason.

#### Scenario: Region-locked track skipped

- GIVEN an album with one region-locked track among otherwise available tracks
- WHEN the system processes the album
- THEN the region-locked track is skipped, all other tracks are downloaded, and the run completes

#### Scenario: End-of-run skip report

- GIVEN a run in which at least one track was skipped
- WHEN the run finishes
- THEN the report names each skipped track with its album and reason

#### Scenario: Download error contained

- GIVEN a track whose download fails mid-run
- WHEN the failure occurs
- THEN the failure is recorded, remaining tracks continue, and the album is not aborted
