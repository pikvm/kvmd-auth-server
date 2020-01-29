#!/usr/bin/env python3
# ========================================================================== #
#                                                                            #
#    KVMD-Auth-Server - The basic HTTP/MySQL auth server for Pi-KVM.         #
#                                                                            #
#    Copyright (C) 2020  Maxim Devaev <mdevaev@gmail.com>                    #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation, either version 3 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                            #
# ========================================================================== #


import contextlib
import inspect
import argparse
import logging
import logging.config

from typing import Dict
from typing import Callable
from typing import AsyncGenerator
from typing import Optional
from typing import Any

import aiohttp.web
import aiomysql
import yaml


# =====
_logger = logging.getLogger("kvmd-auth-server")


# =====
class BadRequestError(Exception):
    pass


def _make_response(text: str, status: int=200) -> aiohttp.web.Response:
    return aiohttp.web.Response(text=f"{text}\r\n", status=status)


_ATTR_EXPOSED = "exposed"
_ATTR_EXPOSED_METHOD = "exposed_method"
_ATTR_EXPOSED_PATH = "exposed_path"


def _exposed(http_method: str, path: str) -> Callable:
    def make_wrapper(handler: Callable) -> Callable:
        async def wrapper(self: "_Server", request: aiohttp.web.Request) -> aiohttp.web.Response:
            try:
                return (await handler(self, request))
            except BadRequestError as err:
                return _make_response(f"BAD REQUEST: {str(err)}", 400)
            except Exception as err:
                _logger.exception("Unhandled API exception")
                return _make_response(f"SERVER ERROR: {type(err).__name__}: {str(err)}", 500)

        setattr(wrapper, _ATTR_EXPOSED, True)
        setattr(wrapper, _ATTR_EXPOSED_METHOD, http_method)
        setattr(wrapper, _ATTR_EXPOSED_PATH, path)
        return wrapper
    return make_wrapper


class _Server:
    def __init__(self, auth_query: str, db_params: Dict[str, Any]) -> None:
        self.__auth_query = auth_query
        self.__db_params = db_params
        self.__db_pool: Optional[aiomysql.Pool] = None

    def make_app(self) -> aiohttp.web.Application:
        app = aiohttp.web.Application()
        app.on_cleanup.append(self.__cleanup)
        for name in dir(self):
            method = getattr(self, name)
            if inspect.ismethod(method) and getattr(method, _ATTR_EXPOSED, False):
                app.router.add_route(
                    getattr(method, _ATTR_EXPOSED_METHOD),
                    getattr(method, _ATTR_EXPOSED_PATH),
                    method,
                )
        return app

    async def __cleanup(self, _: aiohttp.web.Application) -> None:
        if self.__db_pool:
            self.__db_pool.close()
            await self.__db_pool.wait_closed()

    @contextlib.asynccontextmanager
    async def __ensure_db_cursor(self) -> AsyncGenerator[aiomysql.Cursor, None]:
        if not self.__db_pool:
            self.__db_pool = await aiomysql.create_pool(**self.__db_params)
        async with self.__db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                yield cursor

    # =====

    @_exposed("GET", "/ping")
    async def __ping_handler(self, _: aiohttp.web.Request) -> aiohttp.web.Response:
        async with self.__ensure_db_cursor() as cursor:
            await cursor.execute("SELECT version()")
            await cursor.fetchone()
        return _make_response("OK")

    @_exposed("POST", "/auth")
    async def __auth_handler(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        data = await self.__get_json(request)
        credentials = {
            key: self.__get_credential(data, key)
            for key in ["user", "passwd", "secret"]
        }
        async with self.__ensure_db_cursor() as cursor:
            await cursor.execute(self.__auth_query, credentials)
            if len(await cursor.fetchall()) > 0:
                return _make_response("OK")
            return _make_response("FORBIDDEN", 403)

    async def __get_json(self, request: aiohttp.web.Request) -> Dict:
        try:
            return (await request.json())
        except Exception as err:
            raise BadRequestError(f"Can't parse JSON request: {str(err)}")

    def __get_credential(self, data: Dict, key: str) -> aiohttp.web.Response:
        value: Any = data.get(key)
        if value is None:
            raise BadRequestError(f"Missing {key!r}")
        value = str(value)
        if len(value) > 256:
            raise BadRequestError(f"Too long {key!r}")
        return value


# =====
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http-host", default="localhost")
    parser.add_argument("--http-port", default=8080, type=int)
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default=3306, type=int)
    parser.add_argument("--db-user", default="")
    parser.add_argument("--db-passwd", default="")
    parser.add_argument("--db-name", default="change_me")
    parser.add_argument("--auth-query", default="SELECT 1 FROM users WHERE user = %(user)s AND passwd = %(passwd)s AND secret = %(secret)s")
    parser.add_argument("-d", "--debug", action="store_const", const="DEBUG", dest="log_level")
    parser.set_defaults(log_level="INFO")

    options = parser.parse_args()

    logging.captureWarnings(True)
    logging.config.dictConfig(yaml.safe_load(f"""
        version: 1
        disable_existing_loggers: false

        formatters:
            console:
                (): logging.Formatter
                style: "{{"
                format: "{{asctime}} {{name:30.30}} {{levelname:>7}} --- {{message}}"

        handlers:
            console:
                level: DEBUG
                class: logging.StreamHandler
                stream: ext://sys.stdout
                formatter: console

        root:
            level: {options.log_level}
            handlers:
                - console
    """))

    aiohttp.web.run_app(
        app=_Server(
            auth_query=options.auth_query,
            db_params={
                "host": options.db_host,
                "port": options.db_port,
                "user": (options.db_user or None),
                "password": options.db_passwd,
                "db": options.db_name,
            },
        ).make_app(),
        host=options.http_host,
        port=options.http_port,
    )


if __name__ == "__main__":
    main()
