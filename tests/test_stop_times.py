#!/usr/bin/env python

"""Test `crtm_api` module."""

from crtm_poll import crtm_api

from aiohttp import ClientSession
from aioresponses import aioresponses
import os
import pytest


class TestAPI:
    def test_can_log_fetch(self, tmpdir):
        fetch_path = 'fetch_log'
        file = tmpdir.join(fetch_path)
        crtm_api.stop_times.fetch_log(file, 'a', 'b', 'c')
        assert file.readlines()[1] == 'a,b,c'

    def test_can_not_log_fetch(self, tmpdir):
        fetch_path = 'fetch_log'
        file = tmpdir.join(fetch_path)
        crtm_api.stop_times.fetch_log(None, 'a', 'b', 'c')
        assert not os.path.isfile(file)

    @pytest.mark.asyncio
    async def test_can_fetch_ok_stop(self):
        with aioresponses() as m:
            m.get('https://www.crtm.es/widgets/api/GetStopsTimes.php?'
                  'codStop=8_17491&orderBy=2&stopTimesByIti=3&type=1',
                  status=200, body='test')
            session = ClientSession()
            fetch_conf = {
                    'log': None,
                    'timeout': 10,
                    'max_connections': 1}
            resp_text = await crtm_api.stop_times.fetch('8_17491', session,
                                                        fetch_conf)
            assert 'test' in resp_text
            await session.close()
