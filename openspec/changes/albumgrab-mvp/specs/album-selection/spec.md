# Delta for album-selection

## ADDED Requirements

### Requirement: Numbered multi-select prompt

The system MUST present the album list as a numbered prompt that accepts a single line of multi-select input and SHALL select the union of all referenced albums.

#### Scenario: Single number

- GIVEN a listed album numbered 3
- WHEN the user enters "3"
- THEN only album 3 is selected

#### Scenario: Inclusive range

- GIVEN albums numbered 1 to 6
- WHEN the user enters "2-5"
- THEN albums 2, 3, 4, and 5 are selected (inclusive bounds)

#### Scenario: Mixed list with deduplication

- GIVEN albums numbered 1 to 7
- WHEN the user enters "1,3-5,5,7"
- THEN albums 1, 3, 4, 5, and 7 are selected, each exactly once

#### Scenario: "all" keyword

- GIVEN any non-empty album list
- WHEN the user enters "all" (case-insensitive)
- THEN every album in the list is selected

### Requirement: Invalid selection handling

The system MUST reject invalid selection input with an error naming the offending token, and SHALL re-prompt without aborting the run. Out-of-range numbers, non-numeric tokens, malformed ranges, and empty input MUST be treated as invalid.

#### Scenario: Out-of-range number rejected

- GIVEN an album list of 4 albums
- WHEN the user enters "9"
- THEN the system reports "9" as out of range and re-prompts

#### Scenario: Garbage token rejected

- GIVEN any album list
- WHEN the user enters "1,x,2"
- THEN the system reports "x" as invalid and re-prompts, selecting nothing

#### Scenario: Inverted range rejected

- GIVEN any album list
- WHEN the user enters "5-2"
- THEN the system reports the range as invalid and re-prompts
