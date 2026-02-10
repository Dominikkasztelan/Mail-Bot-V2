# ruff: noqa: E501
from dataclasses import dataclass, field
from typing import Any

from playwright.async_api import BrowserContext


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
    Injects stealth scripts into browser context to prevent bot detection.
    """

    def __init__(self, config: Any):
        self.config = config

    async def apply_stealth(self, context: BrowserContext) -> None:
        """
        Apply all stealth modifications to the browser context.
        """
        await self._mask_navigator(context)

    async def _inject(self, context: BrowserContext, script: str) -> None:
        """Helper to inject script into context."""
        await context.add_init_script(script)

    async def _mask_navigator(self, context: BrowserContext) -> None:
        """
        HARDENED navigator masking with:
        - Advanced Proxy (hides toString, name, length)
        - Robust Worker Injection (Blob/DataURI fallback)
        - Prototype-level consistency
        - WebGL Spoofing (Vendor/Renderer + Link fallback)
        """
        script = """
            // ============================================================
            // STEALTH INJECTION v3.1 - WebGL & Worker Hardening
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

                    // --- Advanced Utils ---
                    const stripProxy = (fn, name, length) => {
                        const originalToStr = Function.prototype.toString;
                        const safeToString = () => `function ${name || fn.name || 'check'}() { [native code] }`;

                        const handlers = {
                            apply: (target, thisArg, args) => target.apply(thisArg, args),
                            construct: (target, args) => new target(...args),
                            get: (target, prop) => {
                                if (prop === 'toString') return new Proxy(originalToStr, {
                                    apply: () => safeToString()
                                });
                                return target[prop];
                            }
                        };

                        // Mask the proxy's own toString behavior
                        return new Proxy(fn, handlers);
                    };

                    // 1. NAVIGATOR PROTOTYPE OVERRIDE
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
                        vendor: "Google Inc.", // Navigator.vendor is usually Google Inc. in Chrome
                        userAgent: CONFIG.userAgent,
                        webdriver: false,
                        hardwareConcurrency: CONFIG.hardwareConcurrency,
                        deviceMemory: CONFIG.deviceMemory,
                        maxTouchPoints: 0
                    });

                    // 2. WEBGL SPOOFING (Context & Parameter Hook)
                    const spoofWebGL = () => {
                        const getParameterProxyHandler = {
                            apply: function(target, thisArg, args) {
                                const param = args[0];
                                // WebGL 1.0 & 2.0 Constants
                                // UNMASKED_VENDOR_WEBGL = 37445
                                // UNMASKED_RENDERER_WEBGL = 37446
                                // VENDOR = 7936
                                // RENDERER = 7937

                                if (param === 37445 || param === 7936) return "Google Inc. (NVIDIA)";
                                if (param === 37446 || param === 7937) return CONFIG.renderer;

                                return target.apply(thisArg, args);
                            }
                        };

                        const originalGetContext = HTMLCanvasElement.prototype.getContext;

                        HTMLCanvasElement.prototype.getContext = stripProxy(function(type, attributes) {
                            // 1. Try to get real context
                            let context = originalGetContext.apply(this, arguments);

                            // 2. Fallback if context is null (Software/Headless fail)
                            if (!context && (type === 'webgl' || type === 'experimental-webgl')) {
                                console.log('[Stealth] WebGL Context null, creating mock...');
                                context = {
                                    getParameter: function(p) {
                                         if (p === 37445 || p === 7936) return "Google Inc. (NVIDIA)";
                                         if (p === 37446 || p === 7937) return CONFIG.renderer;
                                         return 0; // Default for others
                                    },
                                    getExtension: function(name) {
                                        if (name === 'WEBGL_debug_renderer_info') {
                                            return { UNMASKED_VENDOR_WEBGL: 37445, UNMASKED_RENDERER_WEBGL: 37446 };
                                        }
                                        return null;
                                    },
                                    canvas: this,
                                    drawingBufferWidth: 1920,
                                    drawingBufferHeight: 1080,
                                    // Add minimal dummy functions to prevent immediate crashes
                                    enable: function(){},
                                    disable: function(){},
                                    clearColor: function(){},
                                    createBuffer: function(){ return {}; },
                                    bindBuffer: function(){},
                                    bufferData: function(){},
                                    viewport: function(){},
                                    createShader: function(){ return {}; },
                                    shaderSource: function(){},
                                    compileShader: function(){},
                                    createProgram: function(){ return {}; },
                                    attachShader: function(){},
                                    linkProgram: function(){},
                                    useProgram: function(){},
                                    getProgramParameter: function(){ return true; },
                                    getShaderParameter: function(){ return true; },
                                    clear: function(){},
                                    drawArrays: function(){},
                                    createTexture: function(){ return {}; },
                                    bindTexture: function(){},
                                    texParameteri: function(){},
                                    texImage2D: function(){},
                                    uniform1i: function(){},
                                    uniform1f: function(){},
                                    getUniformLocation: function(){ return {}; },
                                    enableVertexAttribArray: function(){},
                                    vertexAttribPointer: function(){}
                                };
                            }

                            // 3. If context exists (real or mock), proxy getParameter
                            if (context && (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2')) {
                                try {
                                    if (!context._spoofed) {
                                        context.getParameter = new Proxy(context.getParameter, getParameterProxyHandler);
                                        context._spoofed = true;
                                    }
                                } catch(e) {}
                            }

                            return context;
                        }, 'getContext', 1);
                    };
                    spoofWebGL();

                    // 3. WORKER INJECTION (HYBRID: BLOB + DATA URI)
                    const injectWorkerStealth = () => {
                        const OriginalWorker = window.Worker;
                        const blobRegistry = new Map();

                        const originalCreateObjectURL = URL.createObjectURL;
                        URL.createObjectURL = stripProxy(function(blob) {
                            const url = originalCreateObjectURL.apply(this, arguments);
                            if (blob instanceof Blob) blobRegistry.set(url, blob);
                            return url;
                        }, 'createObjectURL', 1);

                        const workerPayload = `
                            (function() {
                                try {
                                    const CONFIG = ${JSON.stringify(CONFIG)};
                                    const proto = Object.getPrototypeOf(navigator);

                                    const override = (p, v) => Object.defineProperty(proto, p, { get: () => v, enumerable: true, configurable: true });

                                    override('userAgent', CONFIG.userAgent);
                                    override('appVersion', CONFIG.userAgent.replace('Mozilla/', ''));
                                    override('platform', CONFIG.platform);
                                    override('vendor', "Google Inc.");
                                    override('languages', CONFIG.languages);
                                    override('language', CONFIG.language);
                                    override('webdriver', false);
                                    override('hardwareConcurrency', CONFIG.hardwareConcurrency);
                                    override('deviceMemory', CONFIG.deviceMemory);

                                    ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate'].forEach(k => { try { delete self[k]; } catch(e){} });

                                    try { self.postMessage({ type: 'STEALTH_INIT_SUCCESS' }); } catch(e){}
                                } catch (e) {
                                    try { self.postMessage({ type: 'STEALTH_INIT_ERROR', error: e.toString() }); } catch(err){}
                                }
                            })();
                        `;

                        window.Worker = stripProxy(function Worker(scriptURL, options) {
                            let blobToInject = null;

                            if (scriptURL instanceof Blob) {
                                blobToInject = scriptURL;
                            } else if (typeof scriptURL === 'string' && blobRegistry.has(scriptURL)) {
                                blobToInject = blobRegistry.get(scriptURL);
                            }

                            let finalURL;
                            if (blobToInject) {
                                const parts = [workerPayload + '\\n', blobToInject];
                                const combinedBlob = new Blob(parts, { type: 'application/javascript' });
                                finalURL = originalCreateObjectURL(combinedBlob);
                            } else {
                                const finalScript = `${workerPayload}\\nimportScripts('${scriptURL}');`;
                                const combinedBlob = new Blob([finalScript], { type: 'application/javascript' });
                                finalURL = originalCreateObjectURL(combinedBlob);
                            }

                            return new OriginalWorker(finalURL, options);
                        }, 'Worker', 2);
                        window.Worker.prototype = OriginalWorker.prototype;
                    };
                    injectWorkerStealth();

                    // 4. CHROME EMULATION
                    if (!window.chrome) {
                        const mock = {
                            app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' } },
                            runtime: { OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' }, OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' }, PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }, PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' }, PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' }, RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' } },
                            loadTimes: stripProxy(() => ({ commitLoadTime: Date.now()/1000, connectionInfo: 'http/1.1', finishDocumentLoadTime: Date.now()/1000, finishLoadTime: Date.now()/1000, firstPaintAfterLoadTime: 0, firstPaintTime: Date.now()/1000, navigationType: 'Other', npnNegotiatedProtocol: 'unknown', requestTime: Date.now()/1000, startLoadTime: Date.now()/1000, wasAlternateProtocolAvailable: false, wasFetchedViaSpdy: false, wasNpnNegotiated: false }), 'loadTimes'),
                            csi: stripProxy(() => ({ onloadT: Date.now(), pageT: Date.now(), startE: Date.now(), tran: 15 }), 'csi')
                        };
                        Object.defineProperty(window, 'chrome', { value: mock, writable: true, enumerable: true, configurable: true });
                    }

                    // 5. PERMISSIONS
                    if (navigator.permissions && navigator.permissions.query) {
                        const originalQuery = navigator.permissions.query;
                        navigator.permissions.query = stripProxy(function(descriptor) {
                            if (descriptor.name === 'notifications') return Promise.resolve({ state: 'default', onchange: null });
                            return originalQuery.apply(this, arguments);
                        }, 'query', 1);
                    }

                    // 6. CLEANUP TRACES
                    const traceProps = ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate', 'webdriver'];
                    traceProps.forEach(p => {
                        try { delete window[p]; } catch(e){}
                        try { delete document[p]; } catch(e){}
                        try { delete navigator[p]; } catch(e){}
                    });

                } catch(e) {
                    console.error('[Stealth] Fatal Init Error', e);
                }
            })();
        """

        # Replace placeholders
        languages = str(self.config.languages).replace("'", '"')
        language = self.config.languages[0] if self.config.languages else 'en-US'
        user_agent = self.config.user_agent

        script = script.replace("%LANGUAGES%", languages)
        script = script.replace("%LANGUAGE%", language)
        script = script.replace("%PLATFORM%", self.config.platform)
        script = script.replace("%VENDOR%", self.config.vendor)
        script = script.replace("%RENDERER%", self.config.renderer)
        script = script.replace("%USER_AGENT%", user_agent)

        await self._inject(context, script)
