// crt-webgl.ts — CRT pincushion + post-processing (WebGL)
// 接管原 CSS filter (feDisplacementMap warp + 扫描线 ::before + 暗角 ::after + 色偏 drop-shadow)。
// 全部效果参数都暴露成 uniform，可以通过 (window as any).crt.params 实时修改。
//
// 数据流：xterm 多层 canvas → composer 合成到 source canvas → 这里 texImage2D 上传 → fragment shader 出图。
//
// 调参入口（DevTools）：
//   crt.params.curveX = 6.0;     // 上下边缘弯曲程度 (越小越弯)
//   crt.params.curveY = 5.0;     // 左右边缘弯曲程度
//   crt.params.zoom = 1.08;      // 整体放大 (>1 会显得更"凸")
//   crt.params.chromaShift = 0;  // 关掉色彩错位
//   crt.params.scanIntensity = 0.06;
//   crt.preset('mild' | 'default' | 'strong'); // 预设
//   crt.reset();                 // 回到默认

export interface CrtParams {
    // pincushion 弯曲
    curveX: number; // uv.x *= 1 + (|uv.y|/curveX)^curveExp  — 小=上下边更弯
    curveY: number; // uv.y *= 1 + (|uv.x|/curveY)^curveExp  — 小=左右边更弯
    curveExp: number; // 指数 (默认 2.0 = 参考实现，调大→只有角落弯)
    zoom: number; // 内容放大 (1.0=刚好填满；>1=画面被推向边缘形成"凸面"感)
    // RGB 错位 / 色差
    chromaShift: number; // 横向 R/B 错位基准量
    chromaWobble: number; // 错位的时间抖动
    chromaWobbleSpeed: number;
    // 扫描线
    scanFreq: number; // 频率 (uv.y * scanFreq)
    scanIntensity: number; // 强度 (从颜色中减去的最大值)
    scanSpeed: number; // 扫描线上下漂移速度
    // 荫罩 / 像素栅格
    gridFreq: number;
    gridIntensity: number;
    // 闪烁
    flickerIntensity: number;
    flickerSpeed: number;
    // 后期
    brightness: number; // 整体亮度倍率
    vignette: number; // 暗角强度 (0 = 关闭)
    bgColor: [number, number, number]; // 透明/黑底显示的 phosphor 基底色 (=最低亮度)
}

export const CRT_DEFAULT_PARAMS: CrtParams = {
    curveX: 6.0,
    curveY: 5.0,
    curveExp: 2.1,
    zoom: 1.02,
    chromaShift: 0.0005,
    chromaWobble: 0.0008,
    chromaWobbleSpeed: 3.0,
    scanFreq: 700.0,
    scanIntensity: 0.03,
    scanSpeed: 4.0,
    gridFreq: 1000.0,
    gridIntensity: 0.05,
    flickerIntensity: 0.05,
    flickerSpeed: 20.0,
    brightness: 1.25,
    vignette: 0.55,
    bgColor: [0.018, 0.03, 0.018],
};

export const CRT_PRESETS: Record<string, Partial<CrtParams>> = {
    default: CRT_DEFAULT_PARAMS,
    mild: {
        curveX: 7.0,
        curveY: 6.0,
        zoom: 1.03,
        chromaShift: 0.0012,
        scanIntensity: 0.05,
        gridIntensity: 0.03,
        flickerIntensity: 0.02,
        vignette: 0.35,
    },
    strong: {
        curveX: 3.5,
        curveY: 3.0,
        zoom: 1.12,
        chromaShift: 0.005,
        scanIntensity: 0.14,
        gridIntensity: 0.09,
        flickerIntensity: 0.1,
        vignette: 0.85,
    },
    flat: {
        // 完全关掉枕形 + 色差，只保留扫描线/荫罩 — 想对比时用
        curveX: 1e6,
        curveY: 1e6,
        zoom: 1.0,
        chromaShift: 0.0,
        chromaWobble: 0.0,
        vignette: 0.0,
    },
};

const VERT = `
attribute vec2 position;
varying vec2 vUv;
void main() {
  vUv = position * 0.5 + 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}`;

const FRAG = `
precision highp float;
varying vec2 vUv;
uniform sampler2D uTexture;
uniform float uTime;

uniform float uCurveX;
uniform float uCurveY;
uniform float uCurveExp;
uniform float uZoom;
uniform float uChromaShift;
uniform float uChromaWobble;
uniform float uChromaWobbleSpeed;
uniform float uScanFreq;
uniform float uScanIntensity;
uniform float uScanSpeed;
uniform float uGridFreq;
uniform float uGridIntensity;
uniform float uFlickerIntensity;
uniform float uFlickerSpeed;
uniform float uBrightness;
uniform float uVignette;
uniform vec3 uBgColor;

vec2 curve(vec2 uv) {
    uv = (uv - 0.5) * 2.0;
    uv *= uZoom;
    uv.x *= 1.0 + pow(abs(uv.y) / uCurveX, uCurveExp);
    uv.y *= 1.0 + pow(abs(uv.x) / uCurveY, uCurveExp);
    return uv * 0.5 + 0.5;
}

void main() {
    vec2 uv = curve(vUv);

    // Canvas 2D 坐标系(左上原点) vs WebGL 纹理坐标系(左下原点) 需翻转 Y。
    uv.y = 1.0 - uv.y;

    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    float shift = uChromaShift + uChromaWobble * sin(uTime * uChromaWobbleSpeed);
    float r  = texture2D(uTexture, uv + vec2(shift, 0.0)).r;
    float g  = texture2D(uTexture, uv).g;
    float b  = texture2D(uTexture, uv - vec2(shift, 0.0)).b;
    float b2 = texture2D(uTexture, uv + vec2(0.0, shift * 0.5)).b;
    vec3 color = vec3(r, g, mix(b, b2, 0.5));

    // phosphor 基底色 — 让纯黑也有一点幽灵般的绿色基底
    color = max(color, uBgColor);

    // 横向扫描线
    float scan = sin(uv.y * uScanFreq + uTime * uScanSpeed) * uScanIntensity;
    color -= scan;

    // 像素栅格 / 荫罩
    color *= 1.0 - uGridIntensity * cos(uv.x * uGridFreq);

    // 整屏微闪烁
    color *= (1.0 - uFlickerIntensity * 0.5) + uFlickerIntensity * 0.5 * sin(uTime * uFlickerSpeed);

    // 暗角
    vec2 d = vUv - 0.5;
    float vig = 1.0 - dot(d, d) * uVignette;
    color *= vig;

    gl_FragColor = vec4(color * uBrightness, 1.0);
}`;

type UniformMap = Record<string, WebGLUniformLocation | null>;

export class CrtRenderer {
    readonly canvas: HTMLCanvasElement;
    params: CrtParams;
    private readonly gl: WebGLRenderingContext;
    private readonly program: WebGLProgram;
    private readonly texture: WebGLTexture;
    private readonly uniforms: UniformMap;
    private readonly source: () => HTMLCanvasElement | null;
    private rafId: number | null = null;
    private startTime = 0;

    constructor(
        source: () => HTMLCanvasElement | null,
        params: Partial<CrtParams> = {},
    ) {
        this.source = source;
        this.params = { ...CRT_DEFAULT_PARAMS, ...params };

        this.canvas = document.createElement("canvas");
        const gl = this.canvas.getContext("webgl", {
            alpha: false,
            antialias: false,
            premultipliedAlpha: false,
            preserveDrawingBuffer: false,
        }) as WebGLRenderingContext | null;
        if (!gl) throw new Error("WebGL not supported");
        this.gl = gl;

        this.program = this.createProgram();
        gl.useProgram(this.program);

        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(
            gl.ARRAY_BUFFER,
            new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]),
            gl.STATIC_DRAW,
        );
        const posLoc = gl.getAttribLocation(this.program, "position");
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

        this.texture = gl.createTexture()!;
        gl.bindTexture(gl.TEXTURE_2D, this.texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);

        this.uniforms = {
            uTexture: gl.getUniformLocation(this.program, "uTexture"),
            uTime: gl.getUniformLocation(this.program, "uTime"),
            uCurveX: gl.getUniformLocation(this.program, "uCurveX"),
            uCurveY: gl.getUniformLocation(this.program, "uCurveY"),
            uCurveExp: gl.getUniformLocation(this.program, "uCurveExp"),
            uZoom: gl.getUniformLocation(this.program, "uZoom"),
            uChromaShift: gl.getUniformLocation(this.program, "uChromaShift"),
            uChromaWobble: gl.getUniformLocation(this.program, "uChromaWobble"),
            uChromaWobbleSpeed: gl.getUniformLocation(
                this.program,
                "uChromaWobbleSpeed",
            ),
            uScanFreq: gl.getUniformLocation(this.program, "uScanFreq"),
            uScanIntensity: gl.getUniformLocation(
                this.program,
                "uScanIntensity",
            ),
            uScanSpeed: gl.getUniformLocation(this.program, "uScanSpeed"),
            uGridFreq: gl.getUniformLocation(this.program, "uGridFreq"),
            uGridIntensity: gl.getUniformLocation(
                this.program,
                "uGridIntensity",
            ),
            uFlickerIntensity: gl.getUniformLocation(
                this.program,
                "uFlickerIntensity",
            ),
            uFlickerSpeed: gl.getUniformLocation(this.program, "uFlickerSpeed"),
            uBrightness: gl.getUniformLocation(this.program, "uBrightness"),
            uVignette: gl.getUniformLocation(this.program, "uVignette"),
            uBgColor: gl.getUniformLocation(this.program, "uBgColor"),
        };
    }

    start(): void {
        if (this.rafId !== null) return;
        this.startTime = performance.now();
        const tick = (): void => {
            this.render();
            this.rafId = requestAnimationFrame(tick);
        };
        this.rafId = requestAnimationFrame(tick);
    }

    stop(): void {
        if (this.rafId !== null) cancelAnimationFrame(this.rafId);
        this.rafId = null;
    }

    resize(cssW: number, cssH: number): void {
        // DPR 限到 2，避免 4K 屏上 viewport 过大白白浪费 GPU。
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const w = Math.max(1, Math.round(cssW * dpr));
        const h = Math.max(1, Math.round(cssH * dpr));
        if (this.canvas.width !== w || this.canvas.height !== h) {
            this.canvas.width = w;
            this.canvas.height = h;
            this.gl.viewport(0, 0, w, h);
        }
    }

    setParams(partial: Partial<CrtParams>): void {
        Object.assign(this.params, partial);
    }

    reset(): void {
        Object.assign(this.params, CRT_DEFAULT_PARAMS);
    }

    preset(name: keyof typeof CRT_PRESETS): void {
        const p = CRT_PRESETS[name];
        if (!p) return;
        // 先回默认再叠预设 — 这样 'flat' 关项目时干净不残留
        Object.assign(this.params, CRT_DEFAULT_PARAMS, p);
    }

    private render(): void {
        const gl = this.gl;
        const src = this.source();
        if (!src || src.width === 0 || src.height === 0) return;

        gl.useProgram(this.program);

        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, this.texture);
        try {
            gl.texImage2D(
                gl.TEXTURE_2D,
                0,
                gl.RGBA,
                gl.RGBA,
                gl.UNSIGNED_BYTE,
                src,
            );
        } catch {
            // 偶尔 source canvas 在切换 size 的瞬间被另一处写 — 跳过这一帧。
            return;
        }

        const p = this.params;
        const t = (performance.now() - this.startTime) * 0.001;
        gl.uniform1i(this.uniforms.uTexture, 0);
        gl.uniform1f(this.uniforms.uTime, t);
        gl.uniform1f(this.uniforms.uCurveX, p.curveX);
        gl.uniform1f(this.uniforms.uCurveY, p.curveY);
        gl.uniform1f(this.uniforms.uCurveExp, p.curveExp);
        gl.uniform1f(this.uniforms.uZoom, p.zoom);
        gl.uniform1f(this.uniforms.uChromaShift, p.chromaShift);
        gl.uniform1f(this.uniforms.uChromaWobble, p.chromaWobble);
        gl.uniform1f(this.uniforms.uChromaWobbleSpeed, p.chromaWobbleSpeed);
        gl.uniform1f(this.uniforms.uScanFreq, p.scanFreq);
        gl.uniform1f(this.uniforms.uScanIntensity, p.scanIntensity);
        gl.uniform1f(this.uniforms.uScanSpeed, p.scanSpeed);
        gl.uniform1f(this.uniforms.uGridFreq, p.gridFreq);
        gl.uniform1f(this.uniforms.uGridIntensity, p.gridIntensity);
        gl.uniform1f(this.uniforms.uFlickerIntensity, p.flickerIntensity);
        gl.uniform1f(this.uniforms.uFlickerSpeed, p.flickerSpeed);
        gl.uniform1f(this.uniforms.uBrightness, p.brightness);
        gl.uniform1f(this.uniforms.uVignette, p.vignette);
        gl.uniform3f(
            this.uniforms.uBgColor,
            p.bgColor[0],
            p.bgColor[1],
            p.bgColor[2],
        );

        gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    private createProgram(): WebGLProgram {
        const gl = this.gl;
        const vs = this.compileShader(gl.VERTEX_SHADER, VERT);
        const fs = this.compileShader(gl.FRAGMENT_SHADER, FRAG);
        const program = gl.createProgram()!;
        gl.attachShader(program, vs);
        gl.attachShader(program, fs);
        gl.linkProgram(program);
        if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
            const log = gl.getProgramInfoLog(program) ?? "";
            throw new Error("CRT shader link failed: " + log);
        }
        return program;
    }

    private compileShader(type: number, src: string): WebGLShader {
        const gl = this.gl;
        const shader = gl.createShader(type)!;
        gl.shaderSource(shader, src);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            const log = gl.getShaderInfoLog(shader) ?? "";
            throw new Error("CRT shader compile failed: " + log);
        }
        return shader;
    }
}
