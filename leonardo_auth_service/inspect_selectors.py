import asyncio

from src.core.browser import browser_factory


async def inspect_page() -> None:
    print("🔍 Inspecting Leonardo.ai Login Page...")
    await browser_factory.start()
    context = await browser_factory.create_context()
    page = await context.new_page()

    try:
        await page.goto("https://app.leonardo.ai/auth/login")
        await asyncio.sleep(5)  # Wait for load / animations

        # Take a screenshot for visual confirmation
        await page.screenshot(path="debug_inspect.png")
        print("📸 Screenshot saved as debug_inspect.png")

        # List all inputs
        inputs = await page.query_selector_all("input")
        print(f"\n📥 Found {len(inputs)} inputs:")
        for i, el in enumerate(inputs):
            placeholder = await el.get_attribute("placeholder")
            name = await el.get_attribute("name")
            type_attr = await el.get_attribute("type")
            id_attr = await el.get_attribute("id")
            label = await el.get_attribute("aria-label")
            print(
                f"  {i+1}. ID: {id_attr}, Name: {name}, Type: {type_attr}, "
                f"Placeholder: {placeholder}, Label: {label}"
            )

        # List all buttons
        buttons = await page.query_selector_all("button")
        print(f"\n🖱️ Found {len(buttons)} buttons:")
        for i, el in enumerate(buttons):
            text = await el.inner_text()
            print(f"  {i+1}. Text: '{text.strip()}'")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await context.close()
        await browser_factory.stop()

if __name__ == "__main__":
    asyncio.run(inspect_page())
