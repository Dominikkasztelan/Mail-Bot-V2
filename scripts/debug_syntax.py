import asyncio

from shared.browser.core.stealth.injector import StealthConfig, StealthInjector


async def dump_script():
    config = StealthConfig()
    injector = StealthInjector(config)

    # Mock context
    class MockContext:
        async def add_init_script(self, script):
            print("Script received, length:", len(script))
            with open("dumped_stealth.js", "w", encoding="utf-8") as f:
                f.write(script)

    await injector.apply_stealth(MockContext())
    print("Dumped to dumped_stealth.js")

if __name__ == "__main__":
    asyncio.run(dump_script())
