import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:]))
