# Delta for artist-discovery

## ADDED Requirements

### Requirement: Artist resolution by name

The system MUST accept a free-text artist name, search YouTube Music's artist catalog unauthenticated, and resolve it to a single artist identity for browsing. If no artist matches, the system MUST fail with a clear message and a non-zero exit code before any download occurs.

#### Scenario: Known artist resolves

- GIVEN an artist name that matches a YouTube Music artist
- WHEN the user searches with that name
- THEN the system resolves one artist identity to browse
- AND no error is reported

#### Scenario: Unknown artist fails cleanly

- GIVEN an artist name matching no YouTube Music artist
- WHEN the user searches with that name
- THEN the system prints a clear "artist not found" message
- AND exits non-zero without downloading anything

### Requirement: Album listing

For a resolved artist, the system SHALL list the artist's albums, each showing title, release year, and track count, as a numbered list suitable for selection.

#### Scenario: Albums listed with metadata

- GIVEN a resolved artist that has albums on YouTube Music
- WHEN the system lists the artist's albums
- THEN each entry shows a number, title, year, and track count

#### Scenario: Artist without albums

- GIVEN a resolved artist with zero albums
- WHEN the system lists the artist's albums
- THEN the system reports that no albums were found and exits gracefully
