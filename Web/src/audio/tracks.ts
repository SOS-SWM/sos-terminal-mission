// audio/tracks.ts — 对应 main.py:17 与 main.py:68-85 的 bgm_path/bgm_map
// URL 通过 Vite 的 ?url 后缀引用，构建期会被复制到 dist/

import boot from "@assets/fixed.wav?url";
import sf1096 from "@assets/1096.mp3?url";
import haruhi from "@assets/haruhi.mp3?url";
import itsumo from "@assets/itsumo_no_fuukei.mp3?url";
import nanika from "@assets/nanika_ga_okashii.mp3?url";
import kamadouma from "@assets/kamadouma.mp3?url";
import mikuru from "@assets/mikuru_henshin.mp3?url";

export const BOOT_BGM = { key: "boot", url: boot };
export const SF1096_BGM = { key: "1096", url: sf1096 };
export const HARUHI_BGM = { key: "haruhi", url: haruhi };

interface Track { key: string; url: string }

export const SCENE_BGM_MAP: ReadonlyMap<string, Track> = new Map([
  // 1. そして、いつもの風景
  ["c1a_leave_home", { key: "itsumo", url: itsumo }],
  ["c2a_cafe", { key: "itsumo", url: itsumo }],
  ["c2a_protest", { key: "itsumo", url: itsumo }],
  ["c2a_paid", { key: "itsumo", url: itsumo }],
  // 2. 何かがおかしい
  ["c1b_leave_home", { key: "nanika", url: nanika }],
  ["c2b_cafe", { key: "nanika", url: nanika }],
  ["c2b_status", { key: "nanika", url: nanika }],
  ["c2b_protest", { key: "nanika", url: nanika }],
  ["c2b_paid", { key: "nanika", url: nanika }],
  // 3. カマドウマ
  ["c4b_insufficient", { key: "kamadouma", url: kamadouma }],
  ["c4a_final", { key: "kamadouma", url: kamadouma }],
  // 4. ミクル変身! そして戦闘!
  ["c4b_true_end", { key: "mikuru_h", url: mikuru }],
]);
