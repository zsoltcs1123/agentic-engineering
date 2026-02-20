import asyncio

from dotenv import load_dotenv

from gateflow import RawLLMEngine


async def _run() -> None:
    engine = RawLLMEngine()
    result = await engine.run(
        prompt="Say hello in one sentence.",
        working_directory=".",
        allowed_tools=[],
        permission_mode="default",
    )
    print(f"Output: {result.output}")
    print(f"Tokens: {result.token_usage}")
    print(f"Duration: {result.duration_s:.2f}s")


def main() -> None:
    load_dotenv()
    asyncio.run(_run())


if __name__ == "__main__":
    main()
