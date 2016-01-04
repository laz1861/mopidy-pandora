from __future__ import absolute_import, division, print_function, unicode_literals

import mock

from mopidy import backend as backend_api

from pandora import APIClient, BaseAPIClient

from mopidy_pandora import client, library, playback
from tests.conftest import get_backend, get_station_list_mock, request_exception_mock


def test_uri_schemes(config):
    backend = get_backend(config)

    assert 'pandora' in backend.uri_schemes


def test_init_sets_up_the_providers(config):
    backend = get_backend(config)

    assert isinstance(backend.api, client.MopidyAPIClient)

    assert isinstance(backend.library, library.PandoraLibraryProvider)
    assert isinstance(backend.library, backend_api.LibraryProvider)

    assert isinstance(backend.playback, playback.PandoraPlaybackProvider)
    assert isinstance(backend.playback, backend_api.PlaybackProvider)


def test_init_sets_preferred_audio_quality(config):
    config['pandora']['preferred_audio_quality'] = 'lowQuality'
    backend = get_backend(config)

    assert backend.api.default_audio_quality == BaseAPIClient.LOW_AUDIO_QUALITY


def test_on_start_logs_in(config):
    backend = get_backend(config)

    login_mock = mock.PropertyMock()
    backend.api.login = login_mock
    t = backend.on_start()
    t.join()

    backend.api.login.assert_called_once_with('john', 'smith')


def test_on_start_pre_fetches_lists(config):
    with mock.patch.object(APIClient, 'get_station_list', get_station_list_mock):
        backend = get_backend(config)

        backend.api.login = mock.PropertyMock()
        backend.api.get_genre_stations = mock.PropertyMock()

        assert backend.api.station_list_cache.currsize == 0
        assert backend.api.genre_stations_cache.currsize == 0

        t = backend.on_start()
        t.join()

        assert backend.api.station_list_cache.currsize == 1
        assert backend.api.get_genre_stations.called


def test_on_start_handles_request_exception(config, caplog):
    backend = get_backend(config, True)

    backend.api.login = request_exception_mock
    t = backend.on_start()
    t.join()

    # Check that request exceptions are caught and logged
    assert 'Error logging in to Pandora' in caplog.text()
