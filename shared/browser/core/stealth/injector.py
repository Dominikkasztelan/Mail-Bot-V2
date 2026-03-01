# ruff: noqa: E501
import logging
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import BrowserContext, Page


@dataclass
class StealthConfig:
    mask_navigator: bool = True
    spoof_webgl: bool = True
    canvas_noise: bool = True
    audio_noise: bool = True
    languages: list[str] = field(default_factory=lambda: ["pl-PL", "pl", "en-US", "en"])
    vendor: str = "Google Inc."
    renderer: str = "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)"
    platform: str = "Win32"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class StealthInjector:
    """
    Injects stealth scripts into browser pages via CDP (Chrome DevTools Protocol).

    IMPORTANT: We use CDP's Page.addScriptToEvaluateOnNewDocument instead of
    Playwright's add_init_script / page.add_init_script because the latter causes
    net::ERR_NAME_NOT_RESOLVED in Patchright on Windows/Python 3.13. CDP injection
    operates below Playwright's API layer and does not trigger this bug.

    Additional CDP commands used:
    - Emulation.setAutomationOverride(false) — removes the native C++ webdriver flag
      that JS-level overrides cannot hide from deep scanners like fp-collect.
    """

    def __init__(self, config: Any):
        self.config = config
        self._stealth_script = self._build_stealth_script()

    def _build_stealth_script(self) -> str:
        """Build the complete stealth JS v5.0, pre-rendered with config values."""
        languages = str(self.config.languages).replace("'", '"')
        language = self.config.languages[0] if self.config.languages else "en-US"

        script = """
            // ============================================================
            // STEALTH INJECTION v5.0 - CDP Edition + Canvas Noise + WebDriver Fix
            // ============================================================
            (function() {
                try {
                    const CONFIG = {
                        languages: %LANGUAGES%,
                        language: '%LANGUAGE%',
                        platform: '%PLATFORM%',
                        vendor: '%VENDOR%',
                        renderer: '%RENDERER%',
                        userAgent: '%USER_AGENT%',
                        hardwareConcurrency: navigator.hardwareConcurrency || 8,
                        deviceMemory: navigator.deviceMemory || 8
                    };

                    // --- Seeded PRNG for deterministic canvas noise per session ---
                    // Uses a session-unique seed so each browser run produces different
                    // canvas hashes (looks like real GPU variance), but is stable
                    // within a single page load.
                    const _seed = (Math.random() * 0xFFFFFFFF) | 0;
                    const _prng = (function() {
                        let s = _seed;
                        return function() {
                            s = (s ^ (s << 13)) >>> 0;
                            s = (s ^ (s >> 17)) >>> 0;
                            s = (s ^ (s << 5)) >>> 0;
                            return s / 0x100000000;
                        };
                    })();

                    // --- Advanced toString spoofing ---
                    const originalToStr = Function.prototype.toString;
                    const stripProxy = (fn, name) => {
                        const safeToString = () => `function ${name || fn.name || 'check'}() { [native code] }`;
                        return new Proxy(fn, {
                            apply: (target, thisArg, args) => target.apply(thisArg, args),
                            get: (target, prop) => {
                                if (prop === 'toString') return new Proxy(originalToStr, {
                                    apply: () => safeToString()
                                });
                                return target[prop];
                            }
                        });
                    };

                    // ==========================================================
                    // 1. NAVIGATOR PROTOTYPE OVERRIDE
                    // Note: webdriver is intentionally set to undefined (not false)
                    // to match the native descriptor of non-automated Chromium.
                    // The actual C++ flag is removed via CDP Emulation.setAutomationOverride.
                    // ==========================================================
                    const overrideProto = (proto, table) => {
                        for (const [prop, value] of Object.entries(table)) {
                            try {
                                Object.defineProperty(proto, prop, {
                                    get: () => value,
                                    enumerable: true,
                                    configurable: true
                                });
                            } catch(e) {}
                        }
                    };

                    overrideProto(Navigator.prototype, {
                        languages: CONFIG.languages,
                        language: CONFIG.language,
                        platform: CONFIG.platform,
                        vendor: "Google Inc.",
                        userAgent: CONFIG.userAgent,
                        webdriver: undefined,
                        hardwareConcurrency: CONFIG.hardwareConcurrency,
                        deviceMemory: CONFIG.deviceMemory,
                        maxTouchPoints: 0
                    });


                    // Note: we do NOT use `delete navigator.webdriver` or Object.defineProperty
                    // on the navigator INSTANCE here. Doing so creates a visible own property
                    // descriptor (even with value `undefined`) that detectors like Sannysoft
                    // "WebDriver (New)" detect as "present (failed)".
                    // The prototype override above (webdriver: undefined) is enough to show "missing".



                    // ==========================================================
                    // 2. WEBGL SPOOFING
                    // ==========================================================
                    const getParameterProxyHandler = {
                        apply: function(target, thisArg, args) {
                            const param = args[0];
                            if (param === 37445 || param === 7936) return "Google Inc. (NVIDIA)";
                            if (param === 37446 || param === 7937) return CONFIG.renderer;
                            return target.apply(thisArg, args);
                        }
                    };

                    const originalGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = stripProxy(function(type, attributes) {
                        let ctx = originalGetContext.apply(this, arguments);
                        if (ctx && (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2')) {
                            try {
                                if (!ctx._spoofed) {
                                    ctx.getParameter = new Proxy(ctx.getParameter, getParameterProxyHandler);
                                    ctx._spoofed = true;
                                }
                            } catch(e) {}
                        }
                        return ctx;
                    }, 'getContext');

                    // ==========================================================
                    // 3. CANVAS FINGERPRINT NOISE
                    // Hooks getImageData, toDataURL, toBlob to add imperceptible
                    // pixel-level noise — breaks automated canvas fingerprinting
                    // while remaining visually transparent to humans.
                    // ==========================================================
                    const applyCanvasNoise = (imageData) => {
                        const data = imageData.data;
                        // Modify ~1 in 500 pixels by ±1 on a random channel
                        for (let i = 0; i < data.length; i += 4) {
                            if (_prng() < 0.002) {
                                const channel = Math.floor(_prng() * 3); // R, G, or B
                                const delta = _prng() > 0.5 ? 1 : -1;
                                data[i + channel] = Math.max(0, Math.min(255, data[i + channel] + delta));
                            }
                        }
                        return imageData;
                    };

                    // Hook CanvasRenderingContext2D.getImageData
                    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = stripProxy(function() {
                        return applyCanvasNoise(origGetImageData.apply(this, arguments));
                    }, 'getImageData');

                    // Hook HTMLCanvasElement.toDataURL
                    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = stripProxy(function() {
                        const ctx2d = this.getContext('2d');
                        if (ctx2d) {
                            const imageData = ctx2d.getImageData(0, 0, this.width, this.height);
                            applyCanvasNoise(imageData);
                            ctx2d.putImageData(imageData, 0, 0);
                        }
                        return origToDataURL.apply(this, arguments);
                    }, 'toDataURL');

                    // Hook HTMLCanvasElement.toBlob
                    const origToBlob = HTMLCanvasElement.prototype.toBlob;
                    HTMLCanvasElement.prototype.toBlob = stripProxy(function(callback, ...args) {
                        const ctx2d = this.getContext('2d');
                        if (ctx2d) {
                            const imageData = ctx2d.getImageData(0, 0, this.width, this.height);
                            applyCanvasNoise(imageData);
                            ctx2d.putImageData(imageData, 0, 0);
                        }
                        return origToBlob.apply(this, [callback, ...args]);
                    }, 'toBlob');

                    // ==========================================================
                    // 4. WORKER INJECTION
                    // ==========================================================
                    const OriginalWorker = window.Worker;
                    const originalCreateObjectURL = URL.createObjectURL;
                    const blobRegistry = new Map();

                    URL.createObjectURL = stripProxy(function(blob) {
                        const url = originalCreateObjectURL.apply(this, arguments);
                        if (blob instanceof Blob) blobRegistry.set(url, blob);
                        return url;
                    }, 'createObjectURL');

                    const workerPayload = `
                        (function() {
                            try {
                                const cfg = ${JSON.stringify(CONFIG)};
                                // In Worker context, navigator is self.navigator
                                const nav = self.navigator;
                                const proto = Object.getPrototypeOf(nav);
                                const def = (p, v) => Object.defineProperty(proto, p, { get: () => v, enumerable: true, configurable: true });
                                def('userAgent', cfg.userAgent); def('platform', cfg.platform);
                                def('vendor', "Google Inc."); def('languages', cfg.languages);
                                def('language', cfg.language); def('webdriver', undefined);
                                def('hardwareConcurrency', cfg.hardwareConcurrency);
                                def('deviceMemory', cfg.deviceMemory);
                                // Delete webdriver from own properties of navigator instance
                                try { delete nav.webdriver; } catch(e) {}
                                try {
                                    Object.defineProperty(nav, 'webdriver', {
                                        get: () => undefined, set: undefined,
                                        enumerable: false, configurable: true
                                    });
                                } catch(e) {}
                                ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate',
                                 '$cdc_asdjflasutopfhvcZLmcfl_', '__nightmare'].forEach(k => {
                                    try { delete self[k]; } catch(e){}
                                });
                            } catch(e) {}
                        })();
                    `;

                    window.Worker = stripProxy(function Worker(scriptURL, options) {
                        let blobToInject = (scriptURL instanceof Blob) ? scriptURL : blobRegistry.get(scriptURL) || null;
                        let finalURL;
                        if (blobToInject) {
                            finalURL = originalCreateObjectURL(new Blob([workerPayload + '\\n', blobToInject], { type: 'application/javascript' }));
                        } else {
                            finalURL = originalCreateObjectURL(new Blob([`${workerPayload}\\nimportScripts('${scriptURL}');`], { type: 'application/javascript' }));
                        }
                        return new OriginalWorker(finalURL, options);
                    }, 'Worker');
                    window.Worker.prototype = OriginalWorker.prototype;

                    // ==========================================================
                    // 5. CHROME EMULATION
                    // ==========================================================
                    if (!window.chrome) {
                        Object.defineProperty(window, 'chrome', {
                            value: {
                                app: { isInstalled: false },
                                runtime: {},
                                loadTimes: stripProxy(() => ({
                                    requestTime: Date.now()/1000, startLoadTime: Date.now()/1000,
                                    finishLoadTime: Date.now()/1000, firstPaintTime: Date.now()/1000,
                                    firstPaintAfterLoadTime: 0, navigationType: 'Other',
                                    wasFetchedViaSpdy: false, wasNpnNegotiated: false,
                                    npnNegotiatedProtocol: 'unknown', wasAlternateProtocolAvailable: false,
                                    connectionInfo: 'http/1.1', commitLoadTime: Date.now()/1000,
                                    finishDocumentLoadTime: Date.now()/1000
                                }), 'loadTimes'),
                                csi: stripProxy(() => ({ onloadT: Date.now(), pageT: Date.now(), startE: Date.now(), tran: 15 }), 'csi')
                            },
                            writable: true, enumerable: true, configurable: true
                        });
                    }

                    // ==========================================================
                    // 6. PERMISSIONS
                    // ==========================================================
                    if (navigator.permissions && navigator.permissions.query) {
                        const origQuery = navigator.permissions.query;
                        navigator.permissions.query = stripProxy(function(descriptor) {
                            if (descriptor.name === 'notifications') return Promise.resolve({ state: 'default', onchange: null });
                            return origQuery.apply(this, arguments);
                        }, 'query');
                    }

                    // ==========================================================
                    // 7. DEEP TRACE CLEANUP
                    // ==========================================================
                    const traceKeys = [
                        '__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate',
                        '__webdriver_script_func', '__webdriver_script_fn',
                        '$cdc_asdjflasutopfhvcZLmcfl_', '$chrome_asyncScriptInfo',
                        '_phantom', '__nightmare', '_selenium', 'callPhantom', '_Selenium_IDE_Recorder'
                    ];
                    traceKeys.forEach(p => {
                        try { delete window[p]; } catch(e){}
                        try { delete document[p]; } catch(e){}
                    });

                } catch(e) {
                    console.error('[Stealth] Fatal Init Error', e);
                }
            })();
        """

        script = script.replace("%LANGUAGES%", languages)
        script = script.replace("%LANGUAGE%", language)
        script = script.replace("%PLATFORM%", self.config.platform)
        script = script.replace("%VENDOR%", self.config.vendor)
        script = script.replace("%RENDERER%", self.config.renderer)
        script = script.replace("%USER_AGENT%", self.config.user_agent)

        return script

    async def apply_stealth_via_cdp(self, page: Page) -> None:
        """
        Inject stealth script + disable native webdriver flag via CDP.

        Uses two CDP commands:
        1. Page.addScriptToEvaluateOnNewDocument — JS stealth payload
        2. Emulation.setAutomationOverride(false) — removes C++ webdriver flag
           that JS-level overrides cannot hide from deep scanners like fp-collect.
        """
        try:
            client = await page.context.new_cdp_session(page)
            await client.send("Page.enable")

            # Inject JS stealth payload (webdriver, WebGL, canvas noise, worker, chrome obj)
            await client.send("Page.addScriptToEvaluateOnNewDocument", {
                "source": self._stealth_script
            })

            # Kill the native C++ webdriver flag — this is what fp-collect detects
            try:
                await client.send("Emulation.setAutomationOverride", {"enabled": False})
            except Exception:
                # setAutomationOverride may not be available in all Chromium builds
                pass

        except Exception as e:
            logging.getLogger(__name__).warning(f"[Stealth] CDP injection failed: {e}")

    async def apply_stealth(self, context: BrowserContext) -> None:
        """
        Register CDP stealth on all new pages in this context via event listener.
        Every new page created from this context will automatically receive
        full stealth injection before any navigation occurs.
        """
        async def _on_page(page: Page) -> None:
            await self.apply_stealth_via_cdp(page)

        context.on("page", _on_page)
