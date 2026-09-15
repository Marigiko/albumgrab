# Delta for library-layout

## ADDED Requirements

### Requirement: Output path layout

The system MUST store every track as `{output}/{artist}/{album}/{NN - track}.mp3`, where `NN` is the track's two-digit zero-padded position and `track` is the track title. The system SHALL create missing output directories on demand.

#### Scenario: Layout applied

- GIVEN artist "Example Artist", album "Example Album", track 3 titled "Song"
- WHEN the system stores the track
- THEN the file lands at `{output}/Example Artist/Example Album/03 - Song.mp3`

#### Scenario: Directories created on demand

- GIVEN the artist or album directory does not exist under the output root
- WHEN the first track of that album is stored
- THEN the missing directories are created automatically

### Requirement: Cross-platform filename sanitization

Every path segment (artist, album, track) MUST be sanitized for cross-platform safety: characters invalid on Windows (`< > : " / \ | ? *`) and control characters SHALL be replaced; reserved device names (CON, PRN, AUX, NUL, COM1–9, LPT1–9) SHALL be converted to a safe non-reserved variant; segments longer than 120 characters SHALL be truncated; trailing dots and spaces SHALL be removed. Sanitization MUST NOT alter the zero-padded `NN` prefix or the `.mp3` extension.

#### Scenario: Invalid characters replaced

- GIVEN a track title containing `?` and `:`
- WHEN the system builds the filename
- THEN neither invalid character appears in the stored path
- AND the file is written successfully on the current platform

#### Scenario: Reserved name made safe

- GIVEN a segment named "CON"
- WHEN the system builds the path
- THEN the stored segment is a safe variant that is not a reserved device name

#### Scenario: Overlong segment truncated

- GIVEN a track title longer than 120 characters
- WHEN the system builds the filename
- THEN the title segment is truncated to the cap and the file is written
