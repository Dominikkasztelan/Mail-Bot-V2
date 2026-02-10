import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add root to sys.path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from shared.browser.core.factory import BrowserCore
from shared.browser.core.stealth.injector import StealthConfig

# Popular bot detection test sites
TEST_SITES = [
    {
        "name": "Sannysoft",
        "url": "https://bot.sannysoft.com/",
        "description": "Comprehensive bot detection tests"
    },
    {
        "name": "PixelScan",
        "url": "https://pixelscan.net/",
        "description": "Advanced fingerprinting and bot detection"
    },
    {
        "name": "Are You Headless",
        "url": "https://arh.antoinevastel.com/bots/areyouheadless",
        "description": "Headless browser detection"
    },
    {
    "name": "Browser Info Bot Test",
        "url": "https://deviceandbrowserinfo.com/are_you_a_bot",
        "description": "Device and browser bot detection"
    },
    {
        "name": "BrowserScan",
        "url": "https://www.browserscan.net/bot-detection",
        "description": "Browser fingerprinting and bot detection"
    }
]

async def test_all_sites():
    logger.info("🎬 Testing stealth on multiple bot detection sites...")
    
    # Use full stealth config
    stealth = StealthConfig(
        spoof_webgl=True,
        mask_navigator=True,
        canvas_noise=True,
        audio_noise=True
    )
    
    # Launch in HEADED mode
    browser = BrowserCore(headless=False, stealth_config=stealth)
    
    try:
        await browser.start()
        context = await browser.create_context()
        page = await context.new_page()
        
        for i, site in enumerate(TEST_SITES, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🌐 [{i}/{len(TEST_SITES)}] Testing: {site['name']}")
            logger.info(f"📝 Description: {site['description']}")
            logger.info(f"🔗 URL: {site['url']}")
            logger.info(f"{'='*60}\n")
            
            await page.goto(site['url'])
            
            logger.info(f"✅ Loaded {site['name']}")
            logger.info(f"⏳ Waiting 15 seconds for you to review the results...")
            
            # Wait 15 seconds per site for user to review
            await asyncio.sleep(15)
        
        logger.info("\n" + "="*60)
        logger.info("✅ All sites tested!")
        logger.info("🔄 Returning to Sannysoft for final review...")
        logger.info("="*60 + "\n")
        
        # Return to Sannysoft for final comparison
        await page.goto(TEST_SITES[0]['url'])
        
        logger.info("👀 Browser will stay open for 300 seconds for final review.")
        logger.info("Press Ctrl+C to close earlier.")
        
        await asyncio.sleep(300)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        await browser.stop()
        logger.info("👋 Browser closed.")

if __name__ == "__main__":
    asyncio.run(test_all_sites())
