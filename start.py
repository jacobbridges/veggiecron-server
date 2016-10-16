#!/usr/bin/env python3.5
"""
Where it all begins..
"""

import asyncio

from tornado.platform.asyncio import AsyncIOMainLoop

from src.server import ServerApp


if __name__ == '__main__':

    # Create a tornado IOLoop that corresponds to the asyncio event loop
    loop = asyncio.get_event_loop()
    AsyncIOMainLoop().install()

    # Run the main app
    app = ServerApp(loop)
    loop.create_task(app.setup_db())
    loop.call_soon(app.run)

    # Start the asyncio event loop
    try:
        loop.run_forever()
    finally:
        app.db.close()
