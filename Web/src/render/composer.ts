// composer.ts — Stage 布局 + monitor.png 外框 + Screen/Terminal 层级
// main.tscn: Screen 锚点为 (0.14, 0.13, 0.87, 0.8)
// screen.tscn: Terminal 在 Control 内再次内缩 (0.02, 0.02, 0.98, 0.98)
// xterm 挂到 terminalViewport，外层 .sos-screen 负责 CRT shader 视觉处理
//
// 注意：原 Godot 用 SubViewport 1024×800 渲染再缩放到屏幕（pixelate）；
// 这里曾用 `transform: scale()` 模拟 SubViewport，但 WebGL renderer 在
// CSS-transform 容器内会把 cell 用 DPR=1 计算导致行数被裁切，所以改为
// 直接按目标显示尺寸布局，由 xterm 自行处理 DPR。

// monitor.webp 是体积优化版 (~22KB vs ~300KB)；monitor.png 仍保留在 public/ 作为 fallback。
const monitorUrl = "/monitor.webp";

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

    private monitor: HTMLImageElement;
    private warpDisplacement!: SVGFEDisplacementMapElement;

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
        this.root.appendChild(
            createCrtFilter((el) => {
                this.warpDisplacement = el;
            }),
        );

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
        setTimeout(() => {
            this.mainMenuOverlay.style.display = "none";
            this.terminal.style.opacity = "1";
        }, 500);
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
        // GLSL warp(uv) 在角点把采样偏移 0.0156 倍 UV。对应 X 像素偏移
        // = 0.0156 × element_width，Y 偏移 = 0.0156 × element_height。
        // feDisplacementMap 只能用单个 scale；用 width 让 X 精确匹配。
        // 实测 Godot 视觉曲率比纯 GLSL 计算更明显（GPU 双线性插值 +
        // 抗锯齿放大了视感），用 1.5× 让 SVG 视觉强度对齐。
        // GLSL warp(uv): 角点采样偏移 0.0156 倍 UV → X 像素 ≈ 0.0156 × sw。
        // SVG feDisplacementMap 用 (channel/255 - 0.5) × scale，角点 channel=1
        // → -0.5 × scale 像素偏移。GLSL 等价 scale = sw × 0.0312。但 GPU bilinear
        // 让 Godot 视觉曲率比纯算式更明显，scale 调到 sw × 0.05 才在视觉上接近，
        // 同时不会让 terminal 内容（在 0.02 inset 内）被采样到画布外。
        // 角点位移 0.5×scale 像素。scale 太大会把 status bar / 左侧文字采样到画布外。
        // 0.025 ≈ GLSL warp(uv) 在角点的 UV 位移 0.0156 × element_w，向下取整保证
        // status bar (canvas 第 0 行) 不被采样到 canvas 上方的空区域。
        this.warpDisplacement.setAttribute(
            "scale",
            `${Math.max(2, sw * 0.025)}`,
        );

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

function createCrtFilter(
    onDisplacement: (el: SVGFEDisplacementMapElement) => void,
): SVGSVGElement {
    const svgNs = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNs, "svg");
    svg.setAttribute("class", "sos-crt-svg");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");

    const filter = document.createElementNS(svgNs, "filter");
    filter.setAttribute("id", "sos-crt-warp");
    filter.setAttribute("x", "-8%");
    filter.setAttribute("y", "-8%");
    filter.setAttribute("width", "116%");
    filter.setAttribute("height", "116%");
    filter.setAttribute("color-interpolation-filters", "sRGB");

    const image = document.createElementNS(svgNs, "feImage");
    image.setAttribute("x", "0");
    image.setAttribute("y", "0");
    image.setAttribute("width", "100%");
    image.setAttribute("height", "100%");
    image.setAttribute("preserveAspectRatio", "none");
    image.setAttribute("result", "warp-map");
    image.setAttribute("href", createWarpMapDataUrl(192, 192));

    const displacement = document.createElementNS(svgNs, "feDisplacementMap");
    displacement.setAttribute("in", "SourceGraphic");
    displacement.setAttribute("in2", "warp-map");
    displacement.setAttribute("xChannelSelector", "R");
    displacement.setAttribute("yChannelSelector", "G");
    displacement.setAttribute("scale", "6");
    displacement.setAttribute("result", "warped");

    filter.appendChild(image);
    filter.appendChild(displacement);
    svg.appendChild(filter);
    onDisplacement(displacement);
    return svg;
}

function createWarpMapDataUrl(width: number, height: number): string {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    const image = ctx.createImageData(width, height);
    const data = image.data;
    const warpAmount = 0.125;
    const maxDelta = 0.5 * 0.25 * warpAmount;
    for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
            const u = x / Math.max(1, width - 1);
            const v = y / Math.max(1, height - 1);
            const dx0 = u - 0.5;
            const dy0 = v - 0.5;
            const delta2 = dx0 * dx0 + dy0 * dy0;
            const delta4 = delta2 * delta2;
            const dx = dx0 * delta4 * warpAmount;
            const dy = dy0 * delta4 * warpAmount;
            const i = (y * width + x) * 4;
            data[i] = clampByte(128 + (dx / maxDelta) * 127);
            data[i + 1] = clampByte(128 + (dy / maxDelta) * 127);
            data[i + 2] = 128;
            data[i + 3] = 255;
        }
    }
    ctx.putImageData(image, 0, 0);
    return canvas.toDataURL("image/png");
}

function clampByte(value: number): number {
    return Math.max(0, Math.min(255, Math.round(value)));
}
