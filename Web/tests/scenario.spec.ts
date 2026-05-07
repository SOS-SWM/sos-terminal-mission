// 验证 buildScenario + GameEngine 关键路径
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { buildScenario } from "../src/core/scene-loader";
import { GameEngine } from "../src/core/engine";
import { SCENE_META } from "../src/core/scene-meta";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BOOKS_DIR = join(__dirname, "..", "..", "Engine", "books");

function loadBooks(): string[] {
  return ["Chapter1.md", "Chapter2.md", "Chapter3.md", "Chapter4.md"].map((f) =>
    readFileSync(join(BOOKS_DIR, f), "utf8"),
  );
}

describe("buildScenario", () => {
  const scenes = buildScenario(loadBooks());

  it("loads every SCENE_META entry", () => {
    for (const id of SCENE_META.keys()) {
      expect(scenes.has(id)).toBe(true);
    }
  });

  it("has non-empty entries for book-driven scenes", () => {
    const skipMeta = ["c2a_map_return", "c2b_map_return"]; // synthetic only
    for (const [id, scene] of scenes) {
      if (skipMeta.includes(id)) continue;
      expect(scene.entries.length).toBeGreaterThan(0);
    }
  });
});

describe("GameEngine — black path (loop1 → reboot → loop2 missing items)", () => {
  it("survives 1A → 1B/cafe loop and triggers loop reset on c4a_final", () => {
    const scenes = buildScenario(loadBooks());
    const engine = new GameEngine(scenes);
    expect(engine.state.current_scene_id).toBe("c1a_morning_call");

    engine.process_input("2"); // c1a_leave_home → c2a_cafe
    expect(engine.state.current_scene_id).toBe("c2a_cafe");

    engine.process_input("1"); // c2a_paid，初始化 4 AP
    expect(engine.state.action_points_max).toBe(4);

    // _check_ap_exhausted 仅在进入 MAP_HUB 时触发，所以"消耗最后一点 AP 后必须再回一次 hub"
    engine.process_input("1"); // street (AP=3)
    engine.process_input("1"); // 返回 c2a_map_return
    engine.process_input("2"); // store (AP=2)
    engine.process_input("1");
    engine.process_input("3"); // nagato (AP=1)
    engine.process_input("1");
    engine.process_input("4"); // rooftop (AP=0)
    engine.process_input("1"); // 返回 c2a_map_return → 触发 c4a_final
    expect(engine.state.current_scene_id).toBe("c4a_final");
    expect(engine.state.pending_scene).toBe("c1b_morning_reboot");
    expect(engine.state.status.loop_count).toBe(1);
  });
});

describe("GameEngine — true ending path", () => {
  it("collects all 3 key items and reaches c4b_true_end", () => {
    const scenes = buildScenario(loadBooks());
    const engine = new GameEngine(scenes);

    // 第一轮：拿满 3 个普通物品 + 把 4 AP 耗尽再回 hub
    engine.process_input("2"); // c1a_leave_home → c2a_cafe
    engine.process_input("1"); // c2a_paid (4 AP)
    engine.process_input("2"); // store → 怪兽贴纸 (AP=3)
    engine.process_input("1"); // 返回
    engine.process_input("3"); // nagato → 灯带 (AP=2)
    engine.process_input("1");
    engine.process_input("4"); // rooftop → 风筝线 (AP=1)
    expect(engine.state.has_all_normal_items()).toBe(true); // 入 c4a_final 前确认收齐
    engine.process_input("1");
    engine.process_input("1"); // street (AP=0)
    engine.process_input("1"); // 返回 hub → c4a_final（loop_reset 会清空 NORMAL_ITEMS）
    expect(engine.state.current_scene_id).toBe("c4a_final");

    // 模拟 main.py 的 pending_scene 处理（手动跳到下个 reboot）
    const pending = engine.state.pending_scene!;
    engine.state.pending_scene = null;
    engine._enter_scene(pending);
    expect(engine.state.current_scene_id).toBe("c1b_morning_reboot");
    expect(engine.state.inventory.size).toBe(0);

    // 第二轮：7 AP，按 street → store 首访 → store 重访(玩偶服) →
    //  nagato 首访 → nagato 重访(按钮) → rooftop 首访 → rooftop 重访(装置) → 回 hub
    engine.process_input("2"); // c1b_leave_home → c2b_cafe
    engine.process_input("1"); // c2b_paid (7 AP)
    expect(engine.state.action_points_max).toBe(7);

    engine.process_input("1"); // street (AP=6)
    engine.process_input("1");
    engine.process_input("2"); // store 首访 → 怪兽贴纸 (AP=5)
    engine.process_input("1");
    engine.process_input("2"); // store 重访 → 玩偶服 (AP=4)
    engine.process_input("1"); // 接过玩偶服
    engine.process_input("3"); // nagato 首访 → 灯带 (AP=3)
    engine.process_input("1");
    engine.process_input("3"); // nagato 重访 → 大红按钮 (AP=2)
    engine.process_input("1");
    engine.process_input("4"); // rooftop 首访 → 风筝线 (AP=1)
    engine.process_input("1");
    engine.process_input("4"); // rooftop 重访 → 飞行装置 (AP=0)
    engine.process_input("1"); // 返回 hub → c4b_final
    expect(engine.state.current_scene_id).toBe("c4b_final");
    expect(engine.state.has_all_key_items()).toBe(true);
    expect(engine.state.flags["has_all_key_items"]).toBe(true);

    engine.process_input("2"); // 选 UFO 演出 → c4b_true_end
    expect(engine.state.current_scene_id).toBe("c4b_true_end");
    expect(engine.state.game_over).toBe(true);
  });
});

describe("GameEngine — commands", () => {
  it("HELP returns at least 8 system entries", () => {
    const scenes = buildScenario(loadBooks());
    const engine = new GameEngine(scenes);
    const [entries, isCommand] = engine.process_input("help");
    expect(isCommand).toBe(true);
    // 第一个是 player echo，后续是 sys 回复
    expect(entries.length).toBeGreaterThanOrEqual(9);
    expect(entries[1].text).toContain("HELP");
  });

  it("MAP shows glitch effect on second loop", () => {
    const scenes = buildScenario(loadBooks());
    const engine = new GameEngine(scenes);
    engine.state.status.loop_count = 1;
    const [entries] = engine.process_input("map");
    const last = entries[entries.length - 1];
    expect(last.effect).toBe("glitch");
  });
});
