"""Run the GridLock server on the local loopback interface."""

import uvicorn

from server.settings import Settings


if __name__ == "__main__":
    settings = Settings.from_env()
    uvicorn.run("server.app:create_app", factory=True, host="127.0.0.1", port=settings.port)
