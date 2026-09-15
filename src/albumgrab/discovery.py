"""YouTube Music discovery adapter (Slice 2).

``Catalog`` is the protocol the rest of the app codes against (pipeline,
Slice 3 CLI); ``YTMusicCatalog`` maps raw ytmusicapi payloads onto the
metadata dataclasses. All unit tests run against recorded fixtures with no
network access; the live browse chain is smoke-checked at apply time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Artist:
    """A resolved artist identity (artist-discovery: resolution by name)."""

    name: str
    channel_id: str


@dataclass(frozen=True)
class AlbumRef:
    """One album in an artist's listing; ``track_count`` when the payload has it."""

    browse_id: str
    title: str
    year: str | None
    track_count: int | None


@dataclass(frozen=True)
class TrackRef:
    """One track of an album (design interface: TrackRef)."""

    video_id: str | None
    title: str
    track_number: int
    is_available: bool


@dataclass(frozen=True)
class Album:
    """Full album: header metadata plus tracks, playlist fallback, and cover."""

    browse_id: str
    title: str
    year: str | None
    track_count: int | None
    tracks: list[TrackRef]
    audio_playlist_id: str | None
    cover_url: str | None


class Catalog(Protocol):
    """Discovery boundary used by cli/pipeline (design: Catalog protocol)."""

    def search_artist(self, name: str) -> Artist | None: ...

    def list_albums(self, artist: Artist) -> list[AlbumRef]: ...

    def get_album(self, ref: AlbumRef) -> Album: ...


class YTMusicCatalog:
    """``Catalog`` adapter over an unauthenticated ytmusicapi client."""

    def __init__(self, client: Protocol | None = None) -> None:
        if client is None:
            from ytmusicapi import YTMusic

            client = YTMusic()
        self._client = client

    def search_artist(self, name: str) -> Artist | None:
        """Resolve a free-text name to the first artist result with a browseId."""
        for result in self._client.search(name, filter="artists"):
            browse_id = result.get("browseId")
            if browse_id:
                return Artist(name=result.get("artist") or name, channel_id=browse_id)
        return None

    def list_albums(self, artist: Artist) -> list[AlbumRef]:
        """List the artist's album shelf; order preserved, track_count optional."""
        shelf = self._client.get_artist(artist.channel_id).get("albums") or {}
        return [
            AlbumRef(
                browse_id=entry["browseId"],
                title=entry["title"],
                year=entry.get("year"),
                track_count=entry.get("trackCount"),
            )
            for entry in shelf.get("results") or []
        ]

    def get_album(self, ref: AlbumRef) -> Album:
        """Fetch the full album: tracks, audio playlist fallback id, cover URL."""
        payload = self._client.get_album(ref.browse_id)
        return Album(
            browse_id=ref.browse_id,
            title=payload.get("title", ""),
            year=payload.get("year"),
            track_count=payload.get("trackCount"),
            tracks=[
                TrackRef(
                    video_id=track.get("videoId"),
                    title=track.get("title", ""),
                    track_number=track.get("trackNumber") or 0,
                    is_available=bool(track.get("isAvailable", False)),
                )
                for track in payload.get("tracks") or []
            ],
            audio_playlist_id=payload.get("audioPlaylistId"),
            cover_url=_cover_url(payload.get("thumbnails")),
        )


def _cover_url(thumbnails: list | None) -> str | None:
    """Highest-resolution thumbnail URL (last entry), or None when absent."""
    if not thumbnails:
        return None
    return thumbnails[-1].get("url")
