#!/usr/bin/env python3
import os
import gevent.monkey
gevent.monkey.patch_all()

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
