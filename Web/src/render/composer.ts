// composer.ts — Stage 布局 + monitor.png 外框 + Screen/Terminal 层级
// main.tscn: Screen 锚点为 (0.14, 0.13, 0.87, 0.8)
// screen.tscn: Terminal 在 Control 内再次内缩 (0.02, 0.02, 0.98, 0.98)
// xterm 挂到 terminalViewport，最终视觉由覆盖在屏幕区上的 CrtRenderer (WebGL) 输出。
//
// CRT 视觉处理：原本是 CSS filter (SVG feDisplacementMap + 扫描线 ::before + 暗角 ::after
// + 色偏 drop-shadow)，改为 WebGL pincushion + RGB shift + 扫描线 + 荫罩 + 闪烁 + 暗角。
// 参数挂在 (window as any).crt.params 可在 DevTools 实时调整。

import { CrtRenderer } from "./crt-webgl";

const monitorUrl = "/monitor.png";

const VIEWPORT_REF_W = 1536;
const VIEWPORT_REF_H = 1293;
// 实测 monitor.png 黑色屏幕"孔"在图像 ratio (0.1485, 0.1405, 0.8585, 0.7920)。
// Godot main.tscn 的 anchor 是 (0.14, 0.13, 0.87, 0.8) —— Godot Shader 的 warp
// 把孔外区域采样到 transparent，所以肉眼看不出锚点比孔大那点。
// Web 把 anchor 设到 .sos-screen 上，CSS 的内边白线 (::after box-shadow) 直接
// 画在 .sos-screen 实际边界上；如果边界比 monitor 孔位还宽，白线会被 monitor.png
// 的米黄外框盖住。这里把 anchor 紧贴 monitor 孔位，让白边正好落在孔的内沿。
const SCREEN_ANCHOR_LEFT = 0.1485;
const SCREEN_ANCHOR_TOP = 0.1405;
const SCREEN_ANCHOR_RIGHT = 0.8585;
const SCREEN_ANCHOR_BOTTOM = 0.792;

// 对齐 screen.tscn Terminal 锚点 (0.02, 0.02, 0.98, 0.98)，让四周边距一致，
// 内容居中。row 0 status bar 在视觉上靠近 bezel 内边的问题由 CSS bloom +
// 屏幕内边白线 (.sos-screen::after box-shadow) 弥补，不再用不对称 anchor 解决。
const TERMINAL_ANCHOR_LEFT = 0.02;
const TERMINAL_ANCHOR_TOP = 0.02;
const TERMINAL_ANCHOR_RIGHT = 0.98;
const TERMINAL_ANCHOR_BOTTOM = 0.98;

export interface ComposerFit {
    screenW: number;
    screenH: number;
    terminalW: number;
    terminalH: number;
}

export class Composer {
    readonly root: HTMLDivElement;
    readonly stage: HTMLDivElement;
    readonly screen: HTMLDivElement; // Godot TextureRect / CRT shader 对应层
    readonly subviewport: HTMLDivElement; // Godot SubViewport 固定 1024×800 内容层
    readonly terminal: HTMLDivElement; // xterm / mikuru canvas 挂载点

    readonly powerButton: HTMLDivElement;
    readonly mainMenuOverlay: HTMLDivElement;
    readonly crt: CrtRenderer;

    private monitor: HTMLImageElement;
    private sourceCanvas: HTMLCanvasElement;
    private sourceCtx: CanvasRenderingContext2D;

    // 让 xterm canvas 等比缩放（保持字符宽高比）后在 terminal viewport 内居中。
    // 用单一 scale 而不是 (sx, sy)，否则窗口比例变化会把字符压扁/拉长。
    applyTerminalScale(scale: number, padX: number, padY: number): void {
        const xt = this.terminal.querySelector<HTMLElement>(".xterm");
        if (!xt) return;
        xt.style.transformOrigin = "top left";
        xt.style.transform = `translate(${padX.toFixed(2)}px, ${padY.toFixed(2)}px) scale(${scale.toFixed(4)})`;
    }

    constructor() {
        this.root = document.createElement("div");
        this.root.style.cssText = `
      position:relative;width:100%;height:100%;
      display:flex;align-items:center;justify-content:center;
      background:#000;`;

        this.stage = document.createElement("div");
        this.stage.className = "sos-stage";
        this.root.appendChild(this.stage);

        this.monitor = document.createElement("img");
        this.monitor.src = monitorUrl;
        this.monitor.className = "sos-monitor";
        this.stage.appendChild(this.monitor);

        this.screen = document.createElement("div");
        this.screen.className = "sos-screen";
        this.stage.appendChild(this.screen);

        this.subviewport = document.createElement("div");
        this.subviewport.className = "sos-subviewport";
        this.screen.appendChild(this.subviewport);

        this.terminal = document.createElement("div");
        this.terminal.className = "sos-terminal-viewport";

        // 初始时候 terminal 不显示
        this.terminal.style.opacity = "0";
        this.terminal.style.transition = "opacity 0.2s ease";
        this.subviewport.appendChild(this.terminal);

        // 添加 主菜单提示界面
        this.mainMenuOverlay = document.createElement("div");
        this.mainMenuOverlay.className = "sos-main-menu";
        this.mainMenuOverlay.style.cssText = `
			position: absolute;
			inset: 0;
			display: flex;
			align-items: center;
			justify-content: center;
			font-family: "SarasaTermSC", "Sarasa Term SC", "Sarasa Mono SC", "Menlo", "Consolas", monospace;
			text-align: center;
			z-index: 10;
			pointer-events: none;
			transition: opacity 0.5s ease;
			`;

        this.mainMenuOverlay.innerHTML = `
			<div style="
				background-color: #0a0a0a;
				color: #8ae234;
				width: 18em;
				height: 11em;
				display: flex;
				flex-direction: column;
				justify-content: center;
				align-items: center;
				border: none;
				position: relative;
				overflow: hidden;
			">
				<!-- CRT 扫描线叠层 -->
				<div style="
					position: absolute;
					top: 0; left: 0; width: 100%; height: 100%;
					background: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.25) 50%),
								linear-gradient(90deg, rgba(255,0,0,0.06), rgba(0,255,0,0.02), rgba(0,0,255,0.06));
					background-size: 100% 4px, 3px 100%;
					pointer-events: none;
				"></div>

				<!-- 状态标题 -->
				<div style="
					font-size: 1.1em;
					font-weight: bold;
					margin-bottom: 0.8em;
					letter-spacing: 0.15em;
					text-shadow: 0 0 0.5em #8ae234;
					text-transform: uppercase;
				">
					SYSTEM OFFLINE
				</div>

				<!-- 操作提示 -->
				<div style="
					font-size: 0.55em;
					opacity: 0.8;
					text-align: left;
					line-height: 1.8;
					text-shadow: 0 0 0.3em #8ae234;
				">
					<div>&gt; Click the Power Button</div>
					<div>&gt; on the monitor to start</div>
				</div>
			</div>`;
        this.screen.appendChild(this.mainMenuOverlay);

        // WebGL CRT 渲染：把 xterm 多层 canvas 合成到 source canvas，再走 shader 出图。
        // sourceCanvas 是临时合成画布，尺寸跟 xterm 的 cell 网格走，每帧动态调整。
        this.sourceCanvas = document.createElement("canvas");
        this.sourceCanvas.width = 1024;
        this.sourceCanvas.height = 800;
        const sctx = this.sourceCanvas.getContext("2d", {
            willReadFrequently: false,
            alpha: false,
        });
        if (!sctx) throw new Error("2D context unavailable for CRT source");
        this.sourceCtx = sctx;

        this.crt = new CrtRenderer(() => this.compositeSource());
        this.crt.canvas.className = "sos-crt-webgl";
        // 覆盖在 xterm 之上 (z-index 2)，但在主菜单覆盖层 (z-index 10) 之下。
        // border-radius: inherit 让 WebGL 输出和 .sos-screen 的圆角一致 (8% / 6%)。
        this.crt.canvas.style.cssText = `
      position: absolute;
      left: 0; top: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 2;
      opacity: 0;
      transition: opacity 0.5s ease;
      border-radius: inherit;
      display: block;
    `;
        this.screen.appendChild(this.crt.canvas);
        this.crt.start();

        // 暴露到 window 方便 DevTools 调参：
        //   crt.params.curveX = 6
        //   crt.preset('mild' | 'default' | 'strong' | 'flat')
        //   crt.reset()
        (window as unknown as { crt: CrtRenderer }).crt = this.crt;

        const noise = document.createElement("div");
        noise.className = "sos-crt-noise";
        this.screen.appendChild(noise);

        // 新增：开机电源键，精确定位于 monitor.png 中的右下角物理按钮位置
        // 左 77.38%、上 84.99%、宽 4.87%、高 5.79% 是按照测算的准确相对位置给出的 bounding box
        this.powerButton = document.createElement("div");
        this.powerButton.className = "sos-power-button";
        this.powerButton.style.cssText = `
      position: absolute;
      left: 77.38%;
      top: 84.99%;
      width: 4.87%;
      height: 5.79%;
      cursor: pointer;
      border-radius: 50%;
      z-index: 20;
      transition: box-shadow 0.2s ease;
    `;
        // 给按钮增加细微的 hover 交互光晕，引导用户点击
        this.powerButton.onmouseenter = () => {
            this.powerButton.style.boxShadow =
                "inset 0 0 10px rgba(255, 255, 255, 0.3), 0 0 15px rgba(138, 226, 52, 0.4)";
        };
        this.powerButton.onmouseleave = () => {
            this.powerButton.style.boxShadow = "none";
        };
        this.stage.appendChild(this.powerButton);
    }

    // 开机动画方法
    powerOn(): void {
        this.mainMenuOverlay.style.opacity = "0";
        // WebGL 输出和 terminal 一起渐入，确保 CRT 效果跟内容同步显示。
        this.crt.canvas.style.opacity = "1";
        setTimeout(() => {
            this.mainMenuOverlay.style.display = "none";
            this.terminal.style.opacity = "1";
        }, 500);
    }

    // 每帧把 xterm 内部多层 canvas 合成到 sourceCanvas，供 WebGL 当纹理上传。
    // CanvasAddon 通常会创建几层 canvas (text / selection / link / cursor)，
    // 全部按它们的自然像素尺寸叠加。空内容时返回 null，shader 这一帧跳过。
    private compositeSource(): HTMLCanvasElement | null {
        const xtermScreen = this.terminal.querySelector(".xterm-screen");
        if (!xtermScreen) return null;
        const canvases = Array.from(
            xtermScreen.querySelectorAll<HTMLCanvasElement>("canvas"),
        );
        if (canvases.length === 0) return null;
        let w = 0;
        let h = 0;
        for (const c of canvases) {
            if (c.width > w) w = c.width;
            if (c.height > h) h = c.height;
        }
        if (w === 0 || h === 0) return null;
        if (
            this.sourceCanvas.width !== w ||
            this.sourceCanvas.height !== h
        ) {
            this.sourceCanvas.width = w;
            this.sourceCanvas.height = h;
        }
        const ctx = this.sourceCtx;
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = "#050505";
        ctx.fillRect(0, 0, w, h);
        for (const c of canvases) {
            if (c.width === 0 || c.height === 0) continue;
            try {
                // 各层 canvas 尺寸不一致时用 drawImage 拉伸到 source 尺寸 —
                // CanvasAddon 一般一致，这里只是防御。
                ctx.drawImage(c, 0, 0, w, h);
            } catch {
                // canvas tainted / 跨域罕见，忽略这一层
            }
        }
        return this.sourceCanvas;
    }

    // 适配视口：stage 按 1536:1293 contain；screen/terminal 分别使用 Godot 锚点定位
    fit(viewportW: number, viewportH: number): ComposerFit {
        const aspect = VIEWPORT_REF_W / VIEWPORT_REF_H;
        let stageW: number, stageH: number;
        if (viewportW / viewportH > aspect) {
            stageH = viewportH;
            stageW = stageH * aspect;
        } else {
            stageW = viewportW;
            stageH = stageW / aspect;
        }
        this.stage.style.width = `${stageW}px`;
        this.stage.style.height = `${stageH}px`;

        const sx = stageW * SCREEN_ANCHOR_LEFT;
        const sy = stageH * SCREEN_ANCHOR_TOP;
        const sw = stageW * (SCREEN_ANCHOR_RIGHT - SCREEN_ANCHOR_LEFT);
        const sh = stageH * (SCREEN_ANCHOR_BOTTOM - SCREEN_ANCHOR_TOP);
        this.screen.style.left = `${sx}px`;
        this.screen.style.top = `${sy}px`;
        this.screen.style.width = `${sw}px`;
        this.screen.style.height = `${sh}px`;

        // subviewport 直接铺满 .sos-screen，避免 CSS transform 干扰 WebGL renderer
        this.subviewport.style.width = `${sw}px`;
        this.subviewport.style.height = `${sh}px`;
        this.subviewport.style.transform = "";

        const tx = sw * TERMINAL_ANCHOR_LEFT;
        const ty = sh * TERMINAL_ANCHOR_TOP;
        const tw = sw * (TERMINAL_ANCHOR_RIGHT - TERMINAL_ANCHOR_LEFT);
        const th = sh * (TERMINAL_ANCHOR_BOTTOM - TERMINAL_ANCHOR_TOP);
        this.terminal.style.left = `${tx}px`;
        this.terminal.style.top = `${ty}px`;
        this.terminal.style.width = `${tw}px`;
        this.terminal.style.height = `${th}px`;

        // WebGL CRT canvas 跟 .sos-screen 一样大 (覆盖整个屏幕孔位)。
        this.crt.resize(sw, sh);

        // 调整字体大小
        this.mainMenuOverlay.style.fontSize = `${(sw * 0.07).toFixed(2)}px`;

        return {
            screenW: sw,
            screenH: sh,
            terminalW: sw * (TERMINAL_ANCHOR_RIGHT - TERMINAL_ANCHOR_LEFT),
            terminalH: sh * (TERMINAL_ANCHOR_BOTTOM - TERMINAL_ANCHOR_TOP),
        };
    }
}

