"""Tests for albumgrab.discovery (artist-discovery adapter scenarios).

Recorded ytmusicapi payload fixtures (tests/fixtures/discovery/) are fed
through a stub backend; the REAL YTMusicCatalog mapping code is exercised
with NO network access. The live browse chain is verified separately
(task 2.7, `live` marker).
"""

import json
from pathlib import Path

from albumgrab.discovery import AlbumRef, Artist, YTMusicCatalog

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "discovery"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class StubYTMusic:
    """Returns recorded payloads; records the query for assertion."""

    def __init__(
        self,
        search_results: list | None = None,
        artist: dict | None = None,
        album: dict | None = None,
    ) -> None:
        self.search_results = search_results or []
        self.artist_payload = artist or {}
        self.album_payload = album or {}
        self.searched_for: str | None = None
        self.fetched_channel: str | None = None
        self.fetched_album: str | None = None

    def search(self, query: str, filter: str | None = None) -> list:  # ytmusicapi kwarg name
        self.searched_for = query
        return self.search_results

    def get_artist(self, channel_id: str) -> dict:
        self.fetched_channel = channel_id
        return self.artist_payload

    def get_album(self, browse_id: str) -> dict:
        self.fetched_album = browse_id
        return self.album_payload


def test_search_artist_maps_recorded_hit() -> None:
    stub = StubYTMusic(search_results=[load_fixture("search_artist_hit.json")])
    catalog = YTMusicCatalog(stub)
    artist = catalog.search_artist("Radiohead")
    assert stub.searched_for == "Radiohead"
    assert artist is not None
    assert artist.name == "Radiohead"
    assert artist.channel_id == "UCr_iyUANcn9OX_yy9piYoLw"


def test_search_artist_no_match_returns_none() -> None:
    catalog = YTMusicCatalog(StubYTMusic(search_results=load_fixture("search_artist_no_match.json")))
    assert catalog.search_artist("Zzxys The Unfindable") is None


def test_search_artist_skips_results_without_browse_id() -> None:
    payload = load_fixture("search_artist_hit.json")
    catalog = YTMusicCatalog(StubYTMusic(search_results=[{"artist": "Broken"}, payload]))
    artist = catalog.search_artist("Radiohead")
    assert artist is not None
    assert artist.channel_id == "UCr_iyUANcn9OX_yy9piYoLw"


def test_list_albums_maps_recorded_shelf_entries() -> None:
    stub = StubYTMusic(
        artist={"albums": load_fixture("artist_albums_shelf.json")},
        search_results=[load_fixture("search_artist_hit.json")],
    )
    catalog = YTMusicCatalog(stub)
    artist = catalog.search_artist("Radiohead")
    assert artist is not None
    albums = catalog.list_albums(artist)
    assert stub.fetched_channel == "UCr_iyUANcn9OX_yy9piYoLw"
    assert [album.title for album in albums] == [
        "KID A MNESIA",
        "A Moon Shaped Pool",
        "The King Of Limbs",
    ]
    assert [album.year for album in albums] == ["2021", "2016", "2011"]
    assert [album.browse_id for album in albums] == [
        "MPREb_E7NpKw54NIT",
        "MPREb_zwdwliUWiJm",
        "MPREb_0MasdQ0OscT",
    ]
    # Unauthenticated shelf payloads carry no trackCount: mapped as None.
    assert all(album.track_count is None for album in albums)


def test_list_albums_maps_track_count_when_payload_provides_it() -> None:
    shelf = load_fixture("artist_albums_shelf.json")
    shelf["results"][0]["trackCount"] = 12
    catalog = YTMusicCatalog(StubYTMusic(artist={"albums": shelf}))
    albums = catalog.list_albums(Artist("Radiohead", "UCr_iyUANcn9OX_yy9piYoLw"))
    assert albums[0].track_count == 12
    assert albums[1].track_count is None


def test_list_albums_artist_without_albums_yields_empty_list() -> None:
    catalog = YTMusicCatalog(StubYTMusic(artist={"albums": {"results": []}}))
    albums = catalog.list_albums(Artist("Radiohead", "UCr_iyUANcn9OX_yy9piYoLw"))
    assert albums == []


def test_get_album_maps_recorded_header_and_tracks() -> None:
    stub = StubYTMusic(album=load_fixture("album_full.json"))
    catalog = YTMusicCatalog(stub)
    album = catalog.get_album(AlbumRef("MPREb_E7NpKw54NIT", "KID A MNESIA", "2021", None))
    assert stub.fetched_album == "MPREb_E7NpKw54NIT"
    assert album.title == "KID A MNESIA"
    assert album.year == "2021"
    assert album.track_count == 34
    assert album.audio_playlist_id == "OLAK5uy_m8Yan_MSAia_ZYmZpl6xm1AINDg8LF1NI"
    # Cover URL = highest-resolution thumbnail (last entry).
    assert album.cover_url is not None
    assert album.cover_url.endswith("w544-h544-l90-rj")
    assert len(album.tracks) == 2
    first = album.tracks[0]
    assert first.video_id == "d9zk2j3JPK4"
    assert first.title == "Everything In Its Right Place"
    assert first.track_number == 1
    assert first.is_available is True


def test_get_album_marks_unavailable_tracks() -> None:
    catalog = YTMusicCatalog(StubYTMusic(album=load_fixture("album_with_unavailable_track.json")))
    album = catalog.get_album(AlbumRef("MPREb_E7NpKw54NIT", "KID A MNESIA", "2021", None))
    assert album.tracks[0].is_available is True
    assert album.tracks[1].is_available is False


def test_get_album_degrades_when_cover_and_playlist_absent() -> None:
    payload = load_fixture("album_full.json")
    del payload["audioPlaylistId"]
    payload["thumbnails"] = []
    catalog = YTMusicCatalog(StubYTMusic(album=payload))
    album = catalog.get_album(AlbumRef("MPREb_x", "Album", None, None))
    assert album.cover_url is None
    assert album.audio_playlist_id is None
