// audio/manager.ts — 音频管理（Web Audio API）
// 按需懒加载 BGM、淡入淡出、循环、停止、单段播放
// 对应 main.py 的 _play_scene_bgm / play_boot_music

interface CachedBuffer {
  buffer: AudioBuffer;
}

export class AudioManager {
  private ctx: AudioContext | null = null;
  private cache = new Map<string, CachedBuffer>();
  private loading = new Map<string, Promise<CachedBuffer>>();

  private bgmSource: AudioBufferSourceNode | null = null;
  private bgmGain: GainNode | null = null;
  private currentBgmKey: string | null = null;

  // 用户手势之前发起的播放请求先 queue 起来，unlock 时一并执行。
  // 这样不会在 user gesture 之前就 new AudioContext()（避免 Chrome 警告）。
  private unlocked = false;
  private pending: Array<() => void> = [];

  // 解锁：浏览器要求用户手势后才能 resume AudioContext
  unlock(): void {
    if (!this.ctx) {
      this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.ctx.state === "suspended") {
      void this.ctx.resume();
    }
    if (!this.unlocked) {
      this.unlocked = true;
      const queued = this.pending.splice(0);
      for (const fn of queued) fn();
    }
  }

  // 预加载：在用户手势之前就拿到 audio buffer，等手势一到立刻能播。
  // 不依赖 AudioContext（用临时 OfflineAudioContext 解码，避免触发"AudioContext
  // was not allowed to start"警告）。
  async preload(key: string, url: string): Promise<CachedBuffer> {
    if (this.cache.has(key)) return this.cache.get(key)!;
    if (this.loading.has(key)) return this.loading.get(key)!;
    const promise = (async () => {
      const resp = await fetch(url);
      const arr = await resp.arrayBuffer();
      // 用 OfflineAudioContext 做离线 decode，不需要用户手势
      const tmpCtx = new OfflineAudioContext(2, 1, 44100);
      const buffer = await tmpCtx.decodeAudioData(arr);
      const cached = { buffer };
      this.cache.set(key, cached);
      this.loading.delete(key);
      return cached;
    })();
    this.loading.set(key, promise);
    return promise;
  }

  async load(key: string, url: string): Promise<CachedBuffer> {
    if (this.cache.has(key)) return this.cache.get(key)!;
    if (this.loading.has(key)) return this.loading.get(key)!;
    if (!this.ctx) this.unlock();
    const ctx = this.ctx!;
    const promise = (async () => {
      const resp = await fetch(url);
      const arr = await resp.arrayBuffer();
      const buffer = await ctx.decodeAudioData(arr);
      const cached = { buffer };
      this.cache.set(key, cached);
      this.loading.delete(key);
      return cached;
    })();
    this.loading.set(key, promise);
    return promise;
  }

  // 播放 BGM；若与当前 key 相同则不重新加载
  async playBgm(key: string, url: string, opts: { loop?: boolean; fadeMs?: number; volume?: number } = {}): Promise<void> {
    if (this.currentBgmKey === key && this.bgmSource) return;
    const fadeMs = opts.fadeMs ?? 1000;
    const volume = opts.volume ?? 0.3;
    const loop = opts.loop ?? true;

    // 用户没点过的话，buffer 提前 fetch 完，但 ctx 不创建；等手势到了再播。
    if (!this.unlocked) {
      this.pending.push(() => void this.playBgm(key, url, opts));
      return;
    }
    const ctx = this.ctx!;
    const cached = await this.load(key, url);

    // 旧 BGM 淡出
    this.stopBgm(fadeMs);

    const src = ctx.createBufferSource();
    src.buffer = cached.buffer;
    src.loop = loop;
    const gain = ctx.createGain();
    gain.gain.value = 0;
    src.connect(gain).connect(ctx.destination);
    src.start();
    gain.gain.linearRampToValueAtTime(volume, ctx.currentTime + fadeMs / 1000);

    this.bgmSource = src;
    this.bgmGain = gain;
    this.currentBgmKey = key;
  }

  stopBgm(fadeMs = 1000): void {
    if (!this.bgmSource || !this.bgmGain || !this.ctx) return;
    const src = this.bgmSource;
    const gain = this.bgmGain;
    const t = this.ctx.currentTime;
    gain.gain.cancelScheduledValues(t);
    gain.gain.setValueAtTime(gain.gain.value, t);
    gain.gain.linearRampToValueAtTime(0, t + fadeMs / 1000);
    setTimeout(() => {
      try { src.stop(); } catch {}
      try { src.disconnect(); } catch {}
      try { gain.disconnect(); } catch {}
    }, fadeMs + 50);
    this.bgmSource = null;
    this.bgmGain = null;
    this.currentBgmKey = null;
  }

  // 一次性播放（启动音）；不循环，不影响 BGM
  async playOneShot(key: string, url: string, opts: { volume?: number; durationMs?: number } = {}): Promise<void> {
    const volume = opts.volume ?? 0.6;
    if (!this.unlocked) {
      this.pending.push(() => void this.playOneShot(key, url, opts));
      return;
    }
    const ctx = this.ctx!;
    const cached = await this.load(key, url);
    const src = ctx.createBufferSource();
    src.buffer = cached.buffer;
    const gain = ctx.createGain();
    gain.gain.value = volume;
    src.connect(gain).connect(ctx.destination);
    src.start();
    if (opts.durationMs !== undefined) {
      setTimeout(() => {
        try { src.stop(); } catch {}
      }, opts.durationMs);
    }
  }
}
