from tablo_downloader import apis
from tests import mock_api_responses
from unittest.mock import patch


@patch('tablo_downloader.apis.requests.get')
def test_local_server_info(mock_request):
    mock_request.side_effect = mock_api_responses.local_server_info
    res = apis.local_server_info()
    assert res['cpes'][0]['private_ip'] == mock_api_responses.PRIVATE_IP
    assert res['cpes'][0]['public_ip'] == mock_api_responses.PUBLIC_IP


@patch('tablo_downloader.apis.requests.get')
def test_server_settings(mock_request):
    mock_request.side_effect = mock_api_responses.server_settings
    res = apis.server_settings(mock_api_responses.PRIVATE_IP)
    assert res['audio'] == 'ac3'


@patch('tablo_downloader.apis.requests.get')
def test_server_information(mock_request):
    mock_request.side_effect = mock_api_responses.server_information
    res = apis.server_information(mock_api_responses.PRIVATE_IP)
    assert res['local_address'] == mock_api_responses.PRIVATE_IP
    assert res['model']['tuners'] == 2


@patch('tablo_downloader.apis.requests.get')
def test_server_capabilities(mock_request):
    mock_request.side_effect = mock_api_responses.server_capabilities
    res = apis.server_capabilities(mock_api_responses.PRIVATE_IP)
    assert 'recording_options' in res['capabilities']


@patch('tablo_downloader.apis.requests.get')
def test_server_channels(mock_request):
    mock_request.side_effect = mock_api_responses.server_channels
    res = apis.server_channels(mock_api_responses.PRIVATE_IP)
    for channel in res:
        assert channel.startswith('/guide/channels/')


@patch('tablo_downloader.apis.requests.get')
def test_server_recordings(mock_request):
    mock_request.side_effect = mock_api_responses.server_recordings
    res = apis.server_recordings(mock_api_responses.PRIVATE_IP)
    for channel in res:
        assert channel.startswith('/recordings/')


@patch('tablo_downloader.apis.requests.delete')
def test_delete_recording(mock_request):
    mock_request.return_value = mock_api_responses.MockResponse([], '')
    res = apis.delete_recording(mock_api_responses.PRIVATE_IP, '')
    assert not res


@patch('tablo_downloader.apis.requests.get')
def test_recording_details(mock_request):
    mock_request.side_effect = mock_api_responses.recording_details
    res = apis.recording_details(
        mock_api_responses.PRIVATE_IP,
        '/recording/123456')
    assert 'airing_details' in res
    assert 'episode' in res
    assert 'user_info' in res
    assert 'video_details' in res
