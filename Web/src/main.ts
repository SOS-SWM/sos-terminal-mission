// main.ts — 顶层 Orchestrator（xterm.js 版）
// 渲染管线：xterm.js 终端渲染于 stage 内的 Screen 区域，外侧 monitor.png 边框
// 状态机对应 main.py:347-364 的 while True：
//   boot → terminal → mikuru → terminal(c3b_store_revisit) → ... → credit → end

import "./styles.css";
import { Terminal } from "@xterm/xterm";
import { CanvasAddon } from "@xterm/addon-canvas";

import { GameEngine } from "./core/engine";
import { buildScenario } from "./core/scene-loader";
import { BOOK_TEXTS } from "./core/books";
import { XtermApp } from "./tui/XtermApp";
import { AudioManager } from "./audio/manager";
import {
    BOOT_BGM,
    HARUHI_BGM,
    SCENE_BGM_MAP,
    SF1096_BGM,
} from "./audio/tracks";
import { Composer } from "./render/composer";

// xterm 主题：Godot 版的 Terminal 使用 xterm 默认 ANSI 调色板，
// Textual 的 ansi-dark 再通过 truecolor 覆盖项目专用绿/边框色。
const TERMINAL_THEME = {
    background: "#050505",
    foreground: "#d3d7cf",
    cursor: "#d3d7cf",
    black: "#2e3436",
    red: "#cc0000",
    green: "#4e9a06",
    yellow: "#c4a000",
    blue: "#3465a4",
    magenta: "#75507b",
    cyan: "#06989a",
    white: "#d3d7cf",
    brightBlack: "#555753",
    brightRed: "#ef2929",
    brightGreen: "#8ae234",
    brightYellow: "#fce94f",
    brightBlue: "#729fcf",
    brightMagenta: "#ad7fa8",
    brightCyan: "#34e2e2",
    brightWhite: "#eeeeec",
} as const;

const root = document.getElementById("app")!;

const audio = new AudioManager();
window.addEventListener("pointerdown", () => audio.unlock(), { once: true });
window.addEventListener("keydown", () => audio.unlock(), { once: true });
// 浏览器 autoplay policy 要求用户手势后才能播声音，但我们可以在 user 还没点
// 之前就把 buffer 拉过来 + decode 好——等手势一到就立刻能放，不用再等下载/解码。
void audio.preload(BOOT_BGM.key, BOOT_BGM.url);
void audio.preload(SF1096_BGM.key, SF1096_BGM.url);
void audio.preload(HARUHI_BGM.key, HARUHI_BGM.url);
for (const track of SCENE_BGM_MAP.values()) {
    void audio.preload(track.key, track.url);
}

const composer = new Composer();
root.appendChild(composer.root);

// 创建 xterm 终端 — 与 Godot screen.tscn 中 PTY 一致：cols=121, rows=36
// 由于不再用 SubViewport+CSS scale 的方案（与 WebGL renderer 冲突），fontSize
// 改为按 terminal 实际像素尺寸动态计算，让 121×36 cells 正好铺满区域。
const TERM_COLS = 121;
const TERM_ROWS = 36;
const TERM_FONT_PX = 13; // 初始占位，挂载后由 fitFontToScreen 重算
const TERM_LINE_HEIGHT = 1.36;
// SarasaTermSC 在 xterm.js 中实测 cell 大小 vs fontSize 比例：
// cellWidth ≈ 0.5 × fontSize（偶数字号取整后通常正好是 fontSize/2），
// cellHeight ≈ 1.7 × fontSize（含字体自带上下空白）。
const CELL_WIDTH_RATIO = 0.5;
const CELL_HEIGHT_RATIO = 1.7;

const term = new Terminal({
    theme: TERMINAL_THEME,
    fontFamily:
        '"SarasaTermSC","Sarasa Term SC","Sarasa Mono SC","Menlo","Consolas",monospace',
    fontSize: TERM_FONT_PX,
    lineHeight: TERM_LINE_HEIGHT,
    letterSpacing: 0,
    cols: TERM_COLS,
    rows: TERM_ROWS,
    cursorBlink: false,
    cursorStyle: "block",
    scrollback: 0,
    disableStdin: false,
    allowProposedApi: true,
    convertEol: false,
    macOptionIsMeta: true,
} as ConstructorParameters<typeof Terminal>[0]);
term.open(composer.terminal);
// 进入页面就把焦点给 xterm 隐藏的 textarea，用户不用先点屏幕。
// 任何点击页面其它地方时再抢回 focus，避免不小心丢失输入。
term.focus();
window.addEventListener("pointerdown", () => term.focus());
// Canvas renderer + 字号在 fontReady 后一次性设置好。
// 用 Canvas（不是 WebGL）原因：父级 .sos-screen 上挂着 CSS filter（CRT
// shader），WebGL renderer 的 devicePixelContentBoxSize 在 filter 合成
// 层里会以 DPR=1 上报，导致 canvas 内部像素只有期望的一半，渲染只显示
// 屏幕左上 1/4。Canvas renderer 不依赖 ResizeObserver、按 cell 网格
// 定位字符，能在 CSS filter 下稳定工作；同时也保留按 cell 对齐的右边框
// 渲染，避免 DOM renderer 下空格/中文字宽飘移导致"边框碎了"。
// 显式 load SarasaTermSC——document.fonts.ready 不一定等到自定义字体完成测量，
// CanvasAddon 在初次创建时如果用 fallback (Menlo) 测的 advance，之后字体一加载
// xterm 内部又重新测一次，cellW 就跳变 (8 → 7)，整体布局缩水。
void Promise.all([
    document.fonts.load("13px SarasaTermSC"),
    document.fonts.load("bold 13px SarasaTermSC"),
    document.fonts.ready,
]).then(() => {
    try {
        term.loadAddon(new CanvasAddon());
    } catch (err) {
        console.warn(
            "[xterm] Canvas renderer 不可用，回退到 DOM renderer：",
            err,
        );
    }
    fitFontToScreen();
});

const scenes = buildScenario(BOOK_TEXTS);
let engine: GameEngine | null = null;
let isEnteredMikuru = false;
let initialSceneId: string | null = null;
let activeApp: { unmount?: () => void } | null = null;

function fitFontToScreen(): void {
    const fit = composer.fit(window.innerWidth, window.innerHeight);
    // Sarasa cell 自然 aspect (cellW/cellH) ≈ 0.29，但 terminal 区域 aspect
    // (terminalW/121) / (terminalH/36) 通常 ≈ 0.38。直接 fit 会留大量横向空白。
    // 思路：用 height 算 fontSize，再用 letterSpacing 把 cellW 拉到匹配 terminal
    // aspect → 等比 CSS scale 时刚好两边都铺满。
    const fontSize = Math.max(
        8,
        Math.floor(fit.terminalH / (TERM_ROWS * CELL_HEIGHT_RATIO)),
    );
    // 同值不会触发 CharSizeService 重新测量；先给一个非目标值再设回，强制
    // xterm 用当前激活字体（SarasaTermSC）重测 cell advance。没这一步，初次
    // fit 的 cellW 是用 Menlo 测的，等 resize 才用 SarasaTerm 重测，布局缩水。
    if (term.options.fontSize === fontSize) {
        term.options.fontSize = fontSize === 8 ? 9 : 8;
    }
    term.options.fontSize = fontSize;
    term.options.lineHeight = TERM_LINE_HEIGHT;
    term.options.letterSpacing = 0;
    term.resize(TERM_COLS, TERM_ROWS);
    // canvas 自然尺寸用 xterm 自己的 dimension service（同步更新），不用 DOM
    // offsetWidth — 后者在快速 resize 时常拿到旧值，导致 scale 算错累积。
    // 等两帧让样式 + 渲染都 settle，再用 cellW × cols 当 canvas natural 宽。
    requestAnimationFrame(() =>
        requestAnimationFrame(() => {
            const xt = composer.terminal.querySelector<HTMLElement>(".xterm");
            if (!xt) return;
            // 从 xterm 内部拿"权威"的 cell css 尺寸（带 letterSpacing/lineHeight 折算）
            type RendererInternals = {
                _core?: {
                    _renderService?: {
                        dimensions?: {
                            css?: {
                                canvas?: { width: number; height: number };
                                cell?: { width: number; height: number };
                            };
                        };
                    };
                };
            };
            const renderer = (term as unknown as RendererInternals)._core
                ?._renderService;
            const cellH = renderer?.dimensions?.css?.cell?.height ?? 0;
            let canvasW = renderer?.dimensions?.css?.canvas?.width ?? 0;
            const canvasH = renderer?.dimensions?.css?.canvas?.height ?? 0;
            if (canvasW <= 0 || canvasH <= 0 || cellH <= 0) return;
            // 已知 cellH（高度方向已 fit），用 letterSpacing 把 cellW 拉到让 canvas
            // aspect 等于 terminal aspect → uniform scale 两边都不留 padding。
            // 等比 scale = terminalH / canvasH；目标 canvas_w = scale_target × terminalW。
            // 实际 scale 用 height 算后等比应用，所以需要 canvas_w / canvas_h = terminal_w / terminal_h。
            const targetCellW =
                (fit.terminalW / fit.terminalH) *
                cellH *
                (TERM_ROWS / TERM_COLS);
            const currentCellW = canvasW / TERM_COLS;
            const ls = Math.max(0, targetCellW - currentCellW);
            if (ls > 0.1) {
                // letterSpacing 改变会触发重测，要把 ls 应用后再读一遍 dim
                term.options.letterSpacing = ls;
                const newCanvasW =
                    renderer?.dimensions?.css?.canvas?.width ?? canvasW;
                canvasW = newCanvasW;
            }
            const sx = fit.terminalW / canvasW;
            const sy = fit.terminalH / canvasH;
            const scale = Math.min(sx, sy);
            const padX = (fit.terminalW - canvasW * scale) / 2;
            const padY = (fit.terminalH - canvasH * scale) / 2;
            composer.applyTerminalScale(scale, padX, padY);
        }),
    );
}
// 拖拽 resize 期间会触发 N 次 resize 事件，debounce 让 fitFontToScreen 等
// 用户停手再算一次，避免中间状态相互覆盖留下歪 scale。
let fitTimer: ReturnType<typeof setTimeout> | null = null;
function fitAll(): void {
    if (fitTimer !== null) clearTimeout(fitTimer);
    fitTimer = setTimeout(() => {
        fitTimer = null;
        fitFontToScreen();
    }, 80);
}
window.addEventListener("resize", fitAll);
fitFontToScreen();

function disposeActive(): void {
    if (activeApp?.unmount) activeApp.unmount();
    activeApp = null;
}

function startTerminal(): void {
    disposeActive();
    if (!engine) engine = new GameEngine(scenes, initialSceneId);
    const app = new XtermApp(term, engine, initialSceneId, isEnteredMikuru, {
        exit: (code) => onTerminalExit(code),
        playBootMusic: (sec) =>
            void audio.playOneShot(BOOT_BGM.key, BOOT_BGM.url, {
                volume: 0.5,
                durationMs: Math.round(sec * 1000),
            }),
        playSceneBgm: (sceneId) => {
            const track = SCENE_BGM_MAP.get(sceneId);
            if (track) {
                void audio.playBgm(track.key, track.url, {
                    loop: true,
                    fadeMs: 1000,
                    volume: 0.2,
                });
            } else {
                audio.stopBgm(1000);
            }
        },
    });
    activeApp = app;
    app.start();
}

function onTerminalExit(code: string): void {
    if (code === "GAME_CLEARED") {
        void startCredit();
        return;
    }
    initialSceneId = code;
    void startMikuru();
}

async function startMikuru(): Promise<void> {
    await audio.playBgm(SF1096_BGM.key, SF1096_BGM.url, {
        loop: true,
        fadeMs: 100,
        volume: 0.2,
    });
    const { MikuruXtermApp } = await import("./mikuru/XtermApp");
    disposeActive();
    const app = new MikuruXtermApp(term, () => {
        audio.stopBgm(1000);
        isEnteredMikuru = true;
        initialSceneId = "c3b_store_revisit";
        if (engine) engine._enter_scene("c3b_store_revisit");
        startTerminal();
    });
    activeApp = app;
    app.start();
}

async function startCredit(): Promise<void> {
    await audio.playBgm(HARUHI_BGM.key, HARUHI_BGM.url, {
        loop: true,
        fadeMs: 1000,
        volume: 0.2,
    });
    const { CreditXtermApp } = await import("./credit/XtermApp");
    disposeActive();
    const app = new CreditXtermApp(term);
    activeApp = app;
    app.start();
}

let isPoweredOn = false;

// 监听外置开机电源按键的点击触发游戏进入
composer.powerButton.addEventListener("click", () => {
    if (isPoweredOn) return;
    isPoweredOn = true;
    composer.powerOn();
    audio.unlock();
    term.focus();
    startTerminal();
});
