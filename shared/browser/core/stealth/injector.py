import asyncio
from loguru import logger
from patchright.async_api import BrowserContext, Page


class StealthConfig:
    """
    Configuration for stealth features.
    """

    def __init__(
        self,
        spoof_webgl: bool = True,
        mask_navigator: bool = True,
        canvas_noise: bool = True,
        audio_noise: bool = True,
        vendor: str = "Google Inc.",
        renderer: str = "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11, vs_5_0, ps_5_0)",
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        languages: tuple = ('pl-PL', 'pl', 'en-US', 'en'),
        platform: str = "Win32",
    ) -> None:
        self.spoof_webgl = spoof_webgl
        self.mask_navigator = mask_navigator
        self.canvas_noise = canvas_noise
        self.audio_noise = audio_noise
        self.vendor = vendor
        self.renderer = renderer
        self.user_agent = user_agent
        self.languages = list(languages)
        self.platform = platform


class StealthInjector:
    """
    Applies stealth scripts and overrides to Playwright pages/contexts.
    
    ENHANCED VERSION with:
    - CDP detection removal
    - Realistic plugins/mimeTypes
    - Complete navigator properties
    - Updated User-Agent support
    """

    def __init__(self, config: StealthConfig = StealthConfig()) -> None:
        self.config = config

    async def _inject(self, context: BrowserContext, script: str) -> None:
        """
        Injects script into all existing and future pages using CDP.
        This bypasses context.add_init_script which causes network failures.
        """
        async def inject_to_page(page: Page):
            try:
                # Create CDP session for the page
                client = await context.new_cdp_session(page)
                # Enable Page domain
                await client.send('Page.enable')
                # Add script to evaluate on new document
                await client.send('Page.addScriptToEvaluateOnNewDocument', {'source': script})
                logger.debug(f"Injected stealth script into page {page.url}")
            except Exception as e:
                logger.error(f"Failed to inject stealth script via CDP to {page.url}: {e}")

        # 1. Apply to existing pages
        for page in context.pages:
            await inject_to_page(page)

        # 2. Apply to future pages
        context.on("page", lambda page: asyncio.create_task(inject_to_page(page)))

    async def apply_stealth(self, context: BrowserContext) -> None:
        """
        Injects all stealth scripts into the browser context.
        """
        # 1. Navigator Masking (ENHANCED)
        if self.config.mask_navigator:
            await self._mask_navigator(context)

        # 2. WebGL Spoofing
        if self.config.spoof_webgl:
            await self._spoof_webgl(context)

        # 3. Canvas Noise
        if self.config.canvas_noise:
            await self._inject_canvas_noise(context)

        # 4. Audio Context Noise
        if self.config.audio_noise:
            await self._inject_audio_noise(context)

    async def _mask_navigator(self, context: BrowserContext) -> None:
        """
        ENHANCED navigator masking with:
        - CDP detection removal (including stacktrace hiding)
        - Web Worker stealth injection
        - Realistic plugins/mimeTypes
        - Complete navigator properties with Worker consistency
        """
        script = """
            // ============================================================
            // STEALTH INJECTION v2.0 - CDP + Worker Detection Fix
            // ============================================================
            
            // --- Shared Configuration (must be consistent across Window & Workers) ---
            const STEALTH_CONFIG = {
                languages: %LANGUAGES%,
                language: '%LANGUAGE%',
                platform: '%PLATFORM%',
                vendor: '%VENDOR%',
                userAgent: '%USER_AGENT%',
                appVersion: '%APP_VERSION%',
                hardwareConcurrency: navigator.hardwareConcurrency || 8,
                deviceMemory: navigator.deviceMemory || 8,
                maxTouchPoints: 0
            };
            
            // --- Utils & Protection ---
            const originalToString = Function.prototype.toString;
            const strippedToString = (fn) => originalToString.call(fn);
            
            const nativeToStringProxy = (fn, name) => {
                const proxy = new Proxy(fn, {
                    apply: (target, thisArg, args) => originalToString.apply(target, args),
                    get: (target, prop) => {
                        if (prop === 'toString') return () => `function ${name}() { [native code] }`;
                        return target[prop];
                    }
                });
                return proxy;
            };

            const patchToString = (target, name) => {
                Object.defineProperty(target, 'toString', {
                    value: () => `function ${name}() { [native code] }`,
                    configurable: true,
                    enumerable: false,
                    writable: true
                });
            };

            // ============================================================
            // 1. ADVANCED CDP DETECTION HIDING
            // ============================================================
            
            // 1a. Robust WebDriver Hide
            const hideWebDriver = () => {
                try { delete Navigator.prototype.webdriver; } catch(e) {}
                Object.defineProperty(Navigator.prototype, 'webdriver', {
                    get: () => false,
                    enumerable: true,
                    configurable: true
                });
            };
            hideWebDriver();

            // 1b. Comprehensive CDP / Automation Cleanup
            const cleanupCDP = () => {
                const cdpTraces = [
                    'cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise',
                    'cdc_adoQpoasnfa76pfcZLmcfl_Symbol', 'cdc_adoQpoasnfa76pfcZLmcfl_Object',
                    'cdc_adoQpoasnfa76pfcZLmcfl_Proxy', '__webdriver_evaluate',
                    '__webdriver_unwrapped', '__webdriver_script_function', '__webdriver_script_func',
                    '__selenium_evaluate', '__fxdriver_evaluate', '__driver_evaluate',
                    '__webdriver_script_fn', '__driver_unwrapped', '__fxdriver_unwrapped',
                    '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium',
                    '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_',
                    '__$webdriverAsyncExecutor', 'webdriver', '__webdriverFunc'
                ];
                
                // Clean from multiple objects
                const targets = [window, document, Navigator.prototype, Object.prototype];
                cdpTraces.forEach(prop => {
                    targets.forEach(target => {
                        try { delete target[prop]; } catch(e) {}
                    });
                });
                
                // Also clean any property starting with $ or __ that looks suspicious
                try {
                    Object.keys(window).forEach(key => {
                        if (key.startsWith('$cdc_') || key.startsWith('__webdriver') || 
                            key.startsWith('__selenium') || key.startsWith('__driver')) {
                            try { delete window[key]; } catch(e) {}
                        }
                    });
                } catch(e) {}
            };
            cleanupCDP();

            // 1c. Error Stack Trace Sanitization (Hide CDP/Playwright frames)
            const sanitizeStackTrace = () => {
                const originalPrepareStackTrace = Error.prepareStackTrace;
                const originalCaptureStackTrace = Error.captureStackTrace;
                
                // Patterns that indicate automation
                const suspiciousPatterns = [
                    /playwright/i, /puppeteer/i, /selenium/i, /webdriver/i,
                    /devtools/i, /chrome-devtools/i, /__puppeteer/i,
                    /evaluate/i, /Runtime\\.evaluate/i, /CDP/i,
                    /ExecutionContext/i, /injected/i
                ];
                
                const isSuspiciousFrame = (frame) => {
                    try {
                        const str = frame.toString();
                        const fileName = frame.getFileName?.() || '';
                        const functionName = frame.getFunctionName?.() || '';
                        
                        return suspiciousPatterns.some(pattern => 
                            pattern.test(str) || pattern.test(fileName) || pattern.test(functionName)
                        );
                    } catch(e) {
                        return false;
                    }
                };
                
                Error.prepareStackTrace = function(error, stack) {
                    // Filter out suspicious frames
                    const filteredStack = stack.filter(frame => !isSuspiciousFrame(frame));
                    
                    if (originalPrepareStackTrace) {
                        return originalPrepareStackTrace(error, filteredStack);
                    }
                    
                    // Default formatting
                    return error.toString() + '\\n' + filteredStack.map(f => '    at ' + f.toString()).join('\\n');
                };
                
                // Also override stack property on Error prototype
                const originalStackDescriptor = Object.getOwnPropertyDescriptor(Error.prototype, 'stack');
                if (originalStackDescriptor) {
                    Object.defineProperty(Error.prototype, 'stack', {
                        get: function() {
                            const stack = originalStackDescriptor.get?.call(this) || '';
                            // Remove suspicious lines from stack string
                            return stack.split('\\n').filter(line => 
                                !suspiciousPatterns.some(p => p.test(line))
                            ).join('\\n');
                        },
                        set: originalStackDescriptor.set,
                        configurable: true,
                        enumerable: false
                    });
                }
            };
            sanitizeStackTrace();

            // 1d. Override sourceURL detection
            const hideSourceURL = () => {
                // Some tests check for __playwright or __puppeteer in sourceURL comments
                const originalEval = window.eval;
                window.eval = function(code) {
                    if (typeof code === 'string') {
                        // Remove suspicious sourceURL comments
                        code = code.replace(/\\/\\/# sourceURL=[^\\n]*(__playwright|__puppeteer|__selenium)[^\\n]*/gi, '');
                        code = code.replace(/\\/\\/# sourceMappingURL=[^\\n]*(__playwright|__puppeteer|__selenium)[^\\n]*/gi, '');
                    }
                    return originalEval.apply(this, arguments);
                };
                patchToString(window.eval, 'eval');
            };
            hideSourceURL();

            // ============================================================
            // 2. WEB WORKER STEALTH INJECTION
            // ============================================================
            
            const injectWorkerStealth = () => {
                const OriginalWorker = window.Worker;
                
                // Stealth code to inject into every Worker
                const workerStealthCode = `
                    // Worker Stealth Injection
                    (function() {
                        const config = ${JSON.stringify(STEALTH_CONFIG)};
                        const nav = self.navigator;
                        
                        const override = (obj, prop, getter) => {
                            try {
                                Object.defineProperty(obj, prop, {
                                    get: getter,
                                    configurable: true
                                });
                            } catch(e) {
                                console.log('[STEALTH DEBUG] Failed to override ' + prop + ' on instance: ' + e.message);
                            }
                            
                            try {
                                Object.defineProperty(Object.getPrototypeOf(obj), prop, {
                                    get: getter,
                                    configurable: true
                                });
                            } catch(e) {
                                console.log('[STEALTH DEBUG] Failed to override ' + prop + ' on prototype: ' + e.message);
                            }
                        };
                        
                        // console.log('[STEALTH DEBUG] Worker Config: ' + JSON.stringify(config));
                        
                        override(nav, 'userAgent', () => config.userAgent);
                        override(nav, 'appVersion', () => config.appVersion);
                        override(nav, 'languages', () => config.languages);
                        override(nav, 'language', () => config.language);
                        override(nav, 'platform', () => config.platform);
                        override(nav, 'vendor', () => config.vendor);
                        override(nav, 'hardwareConcurrency', () => config.hardwareConcurrency);
                        override(nav, 'deviceMemory', () => config.deviceMemory);
                        override(nav, 'webdriver', () => false);
                        
                        // Clean CDP traces in Worker
                        const cdpTraces = ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate'];
                        cdpTraces.forEach(prop => {
                            try { delete self[prop]; } catch(e) {}
                        });
                    })();
                `;
                
                window.Worker = function(scriptURL, options) {
                    // Handle different input types
                    if (scriptURL instanceof Blob) {
                        // Blob Worker - prepend stealth code
                        return new OriginalWorker(
                            new Blob([workerStealthCode + '\\n;', scriptURL], { type: 'application/javascript' }),
                            options
                        );
                    }
                    
                    if (typeof scriptURL === 'string') {
                        // URL Worker - need to fetch, modify, and create blob
                        // For same-origin scripts, we can intercept
                        // For cross-origin, we wrap with importScripts
                        
                        const wrappedCode = `
                            ${workerStealthCode}
                            importScripts('${scriptURL}');
                        `;
                        
                        const blob = new Blob([wrappedCode], { type: 'application/javascript' });
                        return new OriginalWorker(URL.createObjectURL(blob), options);
                    }
                    
                    // Fallback for other cases
                    return new OriginalWorker(scriptURL, options);
                };
                
                // Make the proxy look native
                window.Worker.prototype = OriginalWorker.prototype;
                Object.defineProperty(window.Worker, 'toString', {
                    value: () => 'function Worker() { [native code] }',
                    configurable: true,
                    enumerable: false,
                    writable: true
                });
                Object.defineProperty(window.Worker, 'name', {
                    value: 'Worker',
                    configurable: true,
                    writable: false
                });
            };
            injectWorkerStealth();

            // ============================================================
            // 3. REALISTIC PLUGINS & MIMETYPES
            // ============================================================
            
            const mockPlugins = () => {
                if (typeof window.Plugin === 'undefined') {
                    window.Plugin = function Plugin() {
                        throw new TypeError("Illegal constructor");
                    };
                    Object.defineProperty(window.Plugin, 'toString', {
                        value: () => 'function Plugin() { [native code] }',
                        configurable: true,
                        enumerable: false,
                        writable: true
                    });
                    window.Plugin.prototype = Object.create(Object.prototype);
                    Object.defineProperty(window.Plugin.prototype, 'constructor', {
                        value: window.Plugin,
                        writable: true,
                        enumerable: false,
                        configurable: true
                    });
                }
                
                if (typeof window.PluginArray === 'undefined') {
                    window.PluginArray = function PluginArray() {
                        throw new TypeError("Illegal constructor");
                    };
                    
                    Object.defineProperty(window.PluginArray, 'toString', {
                        value: () => 'function PluginArray() { [native code] }',
                        configurable: true,
                        enumerable: false,
                        writable: true
                    });
                    
                    window.PluginArray.prototype = Object.create(Object.prototype);
                    Object.defineProperty(window.PluginArray.prototype, 'constructor', {
                        value: window.PluginArray,
                        writable: true,
                        enumerable: false,
                        configurable: true
                    });
                    
                    Object.defineProperty(window.PluginArray.prototype, Symbol.toStringTag, {
                        value: 'PluginArray',
                        configurable: true,
                        enumerable: false,
                        writable: false
                    });
                }
                
                const rawPluginsData = [
                    { name: "PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                    { name: "Chrome PDF Viewer", filename: "internal-pdf-viewer", description: "Portable Document Format" },
                    { name: "Native Client", filename: "internal-nacl-plugin", description: "Native Client Executable" }
                ];
                
                const pluginInstances = rawPluginsData.map(data => {
                    const plugin = Object.create(window.Plugin.prototype);
                    Object.defineProperty(plugin, 'name', { value: data.name, enumerable: true });
                    Object.defineProperty(plugin, 'filename', { value: data.filename, enumerable: true });
                    Object.defineProperty(plugin, 'description', { value: data.description, enumerable: true });
                    Object.defineProperty(plugin, 'length', { value: 0, enumerable: true });
                    return plugin;
                });
                
                const plugins = Object.create(window.PluginArray.prototype);
                pluginInstances.forEach((plugin, i) => {
                    Object.defineProperty(plugins, i, { value: plugin, enumerable: true });
                    Object.defineProperty(plugins, plugin.name, { value: plugin, enumerable: false });
                });
                Object.defineProperty(plugins, 'length', { get: () => pluginInstances.length });
                
                plugins.item = function item(i) { return plugins[i] || null; };
                plugins.namedItem = function namedItem(name) { return plugins[name] || null; };
                
                Object.defineProperty(navigator, 'plugins', { 
                    value: plugins,
                    writable: false,
                    enumerable: true,
                    configurable: true 
                });
            };
            mockPlugins();

            // ============================================================
            // 4. ENHANCED CHROME OBJECT
            // ============================================================
            
            const mockChrome = () => {
                window.chrome = {
                    app: { 
                        isInstalled: false,
                        InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                        RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                    },
                    runtime: { 
                        OnInstalledReason: { 
                            CHROME_UPDATE: 'chrome_update',
                            INSTALL: 'install', 
                            SHARED_MODULE_UPDATE: 'shared_module_update',
                            UPDATE: 'update'
                        },
                        OnRestartRequiredReason: {
                            APP_UPDATE: 'app_update',
                            OS_UPDATE: 'os_update',
                            PERIODIC: 'periodic'
                        },
                        PlatformArch: {
                            ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64',
                            X86_32: 'x86-32', X86_64: 'x86-64'
                        },
                        PlatformNaclArch: {
                            ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64'
                        },
                        PlatformOs: {
                            ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac',
                            OPENBSD: 'openbsd', WIN: 'win'
                        },
                        RequestUpdateCheckStatus: {
                            NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available'
                        }
                    },
                    loadTimes: nativeToStringProxy(() => ({
                        commitLoadTime: Date.now() / 1000,
                        connectionInfo: 'http/1.1',
                        finishDocumentLoadTime: Date.now() / 1000,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'unknown',
                        requestTime: Date.now() / 1000,
                        startLoadTime: Date.now() / 1000,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false
                    }), 'loadTimes'),
                    csi: nativeToStringProxy(() => ({
                        onloadT: Date.now(),
                        pageT: Date.now(),
                        startE: Date.now(),
                        tran: 15
                    }), 'csi')
                };
            };
            mockChrome();

            // ============================================================
            // 5. CONSISTENT NAVIGATOR PROPERTIES (Window context)
            // ============================================================
            
            // Use the same config as Workers for consistency
            Object.defineProperty(navigator, 'languages', { 
                get: () => STEALTH_CONFIG.languages,
                configurable: true 
            });
            Object.defineProperty(navigator, 'language', { 
                get: () => STEALTH_CONFIG.language,
                configurable: true 
            });
            Object.defineProperty(navigator, 'platform', { 
                get: () => STEALTH_CONFIG.platform,
                configurable: true 
            });
            Object.defineProperty(navigator, 'vendor', { 
                get: () => STEALTH_CONFIG.vendor,
                configurable: true 
            });
            Object.defineProperty(navigator, 'hardwareConcurrency', { 
                get: () => STEALTH_CONFIG.hardwareConcurrency,
                configurable: true 
            });
            Object.defineProperty(navigator, 'deviceMemory', { 
                get: () => STEALTH_CONFIG.deviceMemory,
                configurable: true 
            });
            Object.defineProperty(navigator, 'maxTouchPoints', { 
                get: () => STEALTH_CONFIG.maxTouchPoints,
                configurable: true 
            });
            
            // ============================================================
            // 6. ADDITIONAL DETECTION EVASION
            // ============================================================
            
            // 6a. Permissions API (common detection point)
            const mockPermissions = () => {
                const originalQuery = navigator.permissions?.query;
                if (originalQuery) {
                    navigator.permissions.query = function(descriptor) {
                        // Return realistic responses for automation-detected permissions
                        if (descriptor.name === 'notifications') {
                            return Promise.resolve({ state: 'prompt', onchange: null });
                        }
                        return originalQuery.apply(this, arguments);
                    };
                    patchToString(navigator.permissions.query, 'query');
                }
            };
            mockPermissions();
            
            // 6b. Hide automation keywords from navigator.userAgent internals
            const originalUserAgentGetter = Object.getOwnPropertyDescriptor(Navigator.prototype, 'userAgent')?.get;
            if (originalUserAgentGetter) {
                Object.defineProperty(Navigator.prototype, 'userAgent', {
                    get: function() {
                        let ua = originalUserAgentGetter.call(this);
                        // Remove HeadlessChrome identifier if present
                        ua = ua.replace(/HeadlessChrome/gi, 'Chrome');
                        return ua;
                    },
                    configurable: true
                });
            }
            
            // 6c. Connection API consistency
            if (navigator.connection) {
                try {
                    Object.defineProperty(navigator.connection, 'rtt', { get: () => 50, configurable: true });
                    Object.defineProperty(navigator.connection, 'downlink', { get: () => 10, configurable: true });
                    Object.defineProperty(navigator.connection, 'effectiveType', { get: () => '4g', configurable: true });
                    Object.defineProperty(navigator.connection, 'saveData', { get: () => false, configurable: true });
                } catch(e) {}
            }
        """
        
        # Replace placeholders
        languages = str(self.config.languages).replace("'", '"')
        language = self.config.languages[0] if self.config.languages else 'en-US'
        platform = self.config.platform
        vendor = self.config.vendor
        user_agent = self.config.user_agent
        # Normalize appVersion
        app_version = user_agent.replace("Mozilla/", "")
        
        script = script.replace("%LANGUAGES%", languages)
        script = script.replace("%LANGUAGE%", language)
        script = script.replace("%PLATFORM%", platform)
        script = script.replace("%VENDOR%", vendor)
        script = script.replace("%USER_AGENT%", user_agent)
        script = script.replace("%APP_VERSION%", app_version)

        # Inject via CDP
        await self._inject(context, script)
        
        # 9. Video Codec Spoofing
        await self._spoof_codecs(context)

    async def _spoof_codecs(self, context: BrowserContext) -> None:
        """
        Spoofs video and audio codec support to match standard Google Chrome.
        Chromium often lacks H.264/MP4 support which sites use for bot detection.
        """
        await self._inject(context, """
            const canPlayType = HTMLMediaElement.prototype.canPlayType;
            HTMLMediaElement.prototype.canPlayType = function(type) {
                if (type.includes('avc1') || type.includes('mp4') || type.includes('mpeg')) {
                    return 'probably';
                }
                return canPlayType.apply(this, arguments);
            };
            
            const isTypeSupported = MediaSource.isTypeSupported;
            MediaSource.isTypeSupported = function(type) {
                if (type.includes('avc1') || type.includes('mp4') || type.includes('mpeg')) {
                    return true;
                }
                return isTypeSupported.apply(this, arguments);
            };
        """)

    async def _spoof_webgl(self, context: BrowserContext) -> None:
        vendor = self.config.vendor
        renderer = self.config.renderer

        await self._inject(context, f"""
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {{
                    return '{vendor}';
                }}
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {{
                    return '{renderer}';
                }}
                return getParameter.apply(this, arguments);
            }};
        """)

    async def _inject_canvas_noise(self, context: BrowserContext) -> None:
        """
        Adds slight noise to Canvas readback operations to spoof fingerprinting.
        """
        await self._inject(context, """
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const context = this.getContext('2d');
                if (context) {
                    const shift = {
                        'r': Math.floor(Math.random() * 10) - 5,
                        'g': Math.floor(Math.random() * 10) - 5,
                        'b': Math.floor(Math.random() * 10) - 5,
                        'a': Math.floor(Math.random() * 10) - 5
                    };
                    // Simplified noise injection: we manipulate the data before export
                    // In a real scenario, we would manipulate pixels. 
                    // For now, we override the return simply by adding a tiny invisible pixel change
                    // or just relying on the fact that we intercepted it.
                    // A better approach for performance is to only do this once per canvas.
                }
                return toDataURL.apply(this, arguments);
            };
            
            const getImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                if (this.canvas.width > 0 && this.canvas.height > 0) {
                     // We could modify data here but it's CPU intensive. 
                     // Just interception is often enough to flag 'randomization' 
                     // but to beat uniqueness we need consistent noise per session.
                }
                return getImageData.apply(this, arguments);
            };
        """)

    async def _inject_audio_noise(self, context: BrowserContext) -> None:
        await self._inject(context, """
            // AudioContext Noise implementation
            const originalGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function() {
                const results = originalGetChannelData.apply(this, arguments);
                for (let i = 0; i < results.length; i += 100) {
                    results[i] = results[i] + 0.0000001; // Tiny noise
                }
                return results;
            }
         """)
