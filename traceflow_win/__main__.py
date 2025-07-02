import asyncio
import sys

from .traceflow_win import TraceflowWin


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m traceflow_win <destination> <path count>")
        sys.exit(1)

    dest = sys.argv[1]
    paths = sys.argv[2]
    paths = int(paths)

    tracer = TraceflowWin(dest, paths)
    results = await tracer.run()

    for path_id, hops in results.items():
        print(f"Path {path_id}: {hops}")

if __name__ == "__main__":
    asyncio.run(main())
