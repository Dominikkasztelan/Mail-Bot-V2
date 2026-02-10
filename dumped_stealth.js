
            // ============================================================
            // STEALTH INJECTION v2.1 - Enhanced Headless & Worker Fix
            // ============================================================
            (function() {
                try {
                const STEALTH_CONFIG = {
                    languages: ["pl-PL", "pl", "en-US", "en"],
                    language: 'pl-PL',
                    platform: 'Win32',
                    vendor: 'Google Inc.',
                    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    hardwareConcurrency: navigator.hardwareConcurrency || 8,
                    deviceMemory: navigator.deviceMemory || 8,
                    maxTouchPoints: 0
                };
                
                // --- Utils ---
                const patchToString = (target, name) => {
                    if (!target) return;
                    try {
                        Object.defineProperty(target, 'toString', {
                            value: () => `function ${name}() { [native code] }`,
                            configurable: true,
                            enumerable: false,
                            writable: true
                        });
                    } catch(e) {}
                };

                const nativeToStringProxy = (fn, name) => {
                    const originalToString = Function.prototype.toString;
                    return new Proxy(fn, {
                        apply: (target, thisArg, args) => {
                            if (args.length === 0 && thisArg === target) return `function ${name}() { [native code] }`;
                            return originalToString.apply(target, args);
                        },
                        get: (target, prop) => {
                            if (prop === 'toString') return () => `function ${name}() { [native code] }`;
                            return target[prop];
                        }
                    });
                };

                // 1. WEBDRIVER HIDING
                try {
                    const newProto = Object.getPrototypeOf(navigator);
                    delete newProto.webdriver;
                    Object.defineProperty(newProto, 'webdriver', {
                        get: () => false,
                        enumerable: true,
                        configurable: true
                    });
                } catch (e) {}

                // 2. NAVIGATOR PROPERTIES CONSISTENCY
                const navOverrides = {
                    languages: STEALTH_CONFIG.languages,
                    language: STEALTH_CONFIG.language,
                    platform: STEALTH_CONFIG.platform,
                    vendor: STEALTH_CONFIG.vendor,
                    userAgent: STEALTH_CONFIG.userAgent,
                    appVersion: STEALTH_CONFIG.appVersion,
                    hardwareConcurrency: STEALTH_CONFIG.hardwareConcurrency,
                    deviceMemory: STEALTH_CONFIG.deviceMemory,
                    maxTouchPoints: STEALTH_CONFIG.maxTouchPoints
                };

                for (const [prop, value] of Object.entries(navOverrides)) {
                    try {
                        Object.defineProperty(Navigator.prototype, prop, {
                            get: () => value,
                            enumerable: true,
                            configurable: true
                        });
                    } catch (e) {}
                }

                // 3. WINDOW.CHROME EMULATION
                const mockChrome = () => {
                    if (window.chrome) return;
                    window.chrome = {
                        app: { 
                            isInstalled: false,
                            InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                            RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' }
                        },
                        runtime: { 
                            OnInstalledReason: { CHROME_UPDATE: 'chrome_update', INSTALL: 'install', SHARED_MODULE_UPDATE: 'shared_module_update', UPDATE: 'update' },
                            OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                            PlatformArch: { ARM: 'arm', ARM64: 'arm64', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                            PlatformNaclArch: { ARM: 'arm', MIPS: 'mips', MIPS64: 'mips64', X86_32: 'x86-32', X86_64: 'x86-64' },
                            PlatformOs: { ANDROID: 'android', CROS: 'cros', LINUX: 'linux', MAC: 'mac', OPENBSD: 'openbsd', WIN: 'win' },
                            RequestUpdateCheckStatus: { NO_UPDATE: 'no_update', THROTTLED: 'throttled', UPDATE_AVAILABLE: 'update_available' }
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
                        csi: nativeToStringProxy(() => ({ onloadT: Date.now(), pageT: Date.now(), startE: Date.now(), tran: 15 }), 'csi')
                    };
                };
                mockChrome();

                // 4. PERMISSIONS API
                if (navigator.permissions && navigator.permissions.query) {
                    const originalQuery = navigator.permissions.query;
                    navigator.permissions.query = nativeToStringProxy(function(descriptor) {
                        if (descriptor.name === 'notifications') {
                            return Promise.resolve({ state: 'prompt', onchange: null });
                        }
                        return originalQuery.apply(this, arguments);
                    }, 'query');
                }

                // 5. WEB WORKER STEALTH (FIXED)
                const injectWorkerStealth = () => {
                    const OriginalWorker = window.Worker;
                    const workerStealthCode = `
                        (function() {
                            try {
                                console.log('[STEALTH WORKER] Starting injection');
                                const config = ${JSON.stringify(navOverrides)};
                                const nav = self.navigator;
                                console.log('[STEALTH WORKER] Config:', JSON.stringify(config));
                                
                                const override = (obj, prop, value) => {
                                    try {
                                        Object.defineProperty(obj, prop, { get: () => value, configurable: true, enumerable: true });
                                    } catch(e) {
                                        console.error('[STEALTH WORKER] Override failed for ' + prop, e);
                                    }
                                    try {
                                        Object.defineProperty(Object.getPrototypeOf(obj), prop, { get: () => value, configurable: true, enumerable: true });
                                    } catch(e) {
                                        // console.error('[STEALTH WORKER] Proto override failed for ' + prop, e);
                                    }
                                };
                                
                                for (const [prop, val] of Object.entries(config)) {
                                    override(nav, prop, val);
                                }
                                override(nav, 'webdriver', false);
                                
                                // Clean CDP
                                ['__webdriver_evaluate', '__selenium_evaluate', '__driver_evaluate'].forEach(p => { try { delete self[p]; } catch(e) {} });
                                console.log('[STEALTH WORKER] Injection complete');
                            } catch (e) {
                                console.error('[STEALTH WORKER] Fatal error:', e);
                            }
                        })();
                    `;

                    window.Worker = nativeToStringProxy(function Worker(scriptURL, options) {
                        console.log('[STEALTH MAIN] Worker creation intercepted:', scriptURL);
                        if (scriptURL instanceof Blob) {
                            return new OriginalWorker(new Blob([workerStealthCode + '\n;', scriptURL], { type: 'application/javascript' }), options);
                        }
                        const wrappedCode = `${workerStealthCode}\nimportScripts('${scriptURL}');`;
                        const blob = new Blob([wrappedCode], { type: 'application/javascript' });
                        const newURL = URL.createObjectURL(blob);
                        return new OriginalWorker(newURL, options);
                    }, 'Worker');
                    window.Worker.prototype = OriginalWorker.prototype;
                    console.log('[STEALTH DEBUG] Worker overridden. Current Worker:', window.Worker.toString());
                };
                injectWorkerStealth();

                // 6. CDP CLEANUP
                const cleanupCDP = () => {
                    const traces = ['cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 'cdc_adoQpoasnfa76pfcZLmcfl_Symbol', '__webdriver_evaluate', 'webdriver'];
                    [window, document, Navigator.prototype, Object.prototype].forEach(t => {
                        traces.forEach(p => { try { delete t[p]; } catch(e) {} });
                    });
                };
                cleanupCDP();

                } catch (e) {
                    console.error('[STEALTH DEBUG] Error:', e);
                }
            })();
        


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
        


            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL
                if (parameter === 37445) {
                    return 'Google Inc.';
                }
                // UNMASKED_RENDERER_WEBGL
                if (parameter === 37446) {
                    return 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics (0x000046A6) Direct3D11, vs_5_0, ps_5_0)';
                }
                return getParameter.apply(this, arguments);
            };
        


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
        


            // AudioContext Noise implementation
            const originalGetChannelData = AudioBuffer.prototype.getChannelData;
            AudioBuffer.prototype.getChannelData = function() {
                const results = originalGetChannelData.apply(this, arguments);
                for (let i = 0; i < results.length; i += 100) {
                    results[i] = results[i] + 0.0000001; // Tiny noise
                }
                return results;
            }
         


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
        