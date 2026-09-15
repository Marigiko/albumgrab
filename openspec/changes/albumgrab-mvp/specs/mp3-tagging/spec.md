# Delta for mp3-tagging

## ADDED Requirements

### Requirement: ID3v2 tag frame set

Every produced MP3 MUST carry an ID3v2 tag containing: title (TIT2), artist (TPE1), album (TALB), track position (TRCK), release year/date (TDRC), album artist (TPE2), and genre (TCON) where the source provides genre metadata. Frames SHALL be populated from the album/track metadata; TRCK SHALL reflect the track's position within its album.

#### Scenario: Tags written

- GIVEN a transcoded MP3 for a track with known album metadata
- WHEN the system tags the file
- THEN all required frames are present and readable with the correct values

#### Scenario: Track position tagged

- GIVEN track 4 of a 12-track album
- WHEN the system tags the file
- THEN the TRCK frame identifies position 4 within the album

### Requirement: Cover art embedding

The system MUST embed the album's cover image as a front-cover (APIC) frame in each MP3. If cover art cannot be retrieved, the system SHALL still write the text frames, warn the user, and continue.

#### Scenario: Cover embedded

- GIVEN a track of an album with retrievable cover art
- WHEN the system finishes tagging the file
- THEN the MP3 contains an APIC frame of picture type front cover

#### Scenario: Missing cover art degrades gracefully

- GIVEN an album whose cover art cannot be retrieved
- WHEN the system processes its tracks
- THEN files are still tagged with the text frames, a warning is shown, and the run continues
