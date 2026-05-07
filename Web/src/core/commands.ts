// commands.ts — 终端指令的响应，对应 scene.py:589-683 get_command_response

import { LogEntry, type EffectTag } from "./models";
import { KEY_ITEMS, WORLDLINE_STABLE, WORLDLINE_UNSTABLE } from "./constants";

function sys(text: string, effect: EffectTag = "typewriter_fast"): LogEntry {
  return new LogEntry({
    kind: "system",
    speaker: null,
    text,
    effect,
    speed: 0.6,
  });
}

function err(text: string): LogEntry {
  return new LogEntry({
    kind: "error",
    speaker: null,
    text,
    effect: "typewriter_fast",
    speed: 0.6,
  });
}

export function getCommandResponse(
  cmd: string,
  _scene_id: string,
  inventory: ReadonlySet<string>,
  loop_count: number,
  _flags: Readonly<Record<string, boolean>>,
): LogEntry[] {
  const c = cmd.trim().toLowerCase();
  if (c === "help") {
    return [
      sys(">> HELP"),
      sys("  STATUS    - 查看当前精神状态"),
      sys("  INVENTORY - 查看背包物品"),
      sys("  MAP       - 查看地图"),
      sys("  DATE      - 查看世界线信息"),
      sys("  HELP      - 显示此帮助"),
      sys("  SKIP      - 跳过当前场景"),
      sys("  请使用键盘上下或者 Page Up/Down 滚动场景"),
      sys("  剧情移动请使用当前场景的数字选项。"),
    ];
  }
  if (c === "status" || c === "st") {
    const deja_vu = loop_count === 0 ? "NONE" : "INCREASING";
    return [
      sys(">> STATUS", "cursor_fast"),
      sys("STATUS_CHECK_RUNNING...", "typewriter_slow"),
      sys("KYON.STATUS = {", "instant"),
      sys(`  LOOP_COUNT: ${loop_count},`),
      sys("  WALLET: ENDANGERED,"),
      sys("  SANITY: SUSPICIOUS,"),
      sys(`  DEJA_VU: ${deja_vu},`),
      sys(`  ITEMS_HELD: ${inventory.size},`),
      sys("}", "instant"),
    ];
  }
  if (c === "inventory" || c === "inv" || c === "i") {
    if (inventory.size === 0) {
      return [sys(">> INVENTORY"), sys("  [空] 背包里什么都没有。")];
    }
    const lines: LogEntry[] = [sys(">> INVENTORY")];
    const sorted = Array.from(inventory).sort();
    for (const item of sorted) {
      const type = KEY_ITEMS.has(item) ? "关键物品" : "普通物品";
      lines.push(sys(`  [${type}] ${item}`));
    }
    lines.push(sys(`  共 ${inventory.size} 件物品。`));
    return lines;
  }
  if (c === "map") {
    return [
      sys(">> MAP"),
      sys("  HOME       - 阿虚的家"),
      sys("  CAFE       - 站前咖啡厅"),
      sys("  STREET     - 商业街"),
      sys("  STORE      - 便利店"),
      sys("  NAGATO_APT - 长门公寓"),
      sys("  ROOFTOP    - 北高天台"),
      sys(
        "  路线提示: 时间与地点决定道具。",
        loop_count > 0 ? "glitch" : "typewriter_fast",
      ),
    ];
  }
  if (c === "date") {
    const worldline = loop_count === 0 ? WORLDLINE_UNSTABLE : WORLDLINE_STABLE;
    return [
      sys(">> DATE"),
      sys("  DATE: 2006-05-02"),
      sys(`  WORLDLINE: ${worldline}`),
      sys(`  LOOP_COUNT: ${loop_count}`),
    ];
  }
  if (c === "ls") {
    return [sys(" >> LS"), sys("loop.log")];
  }
  if (c === "cat") {
    return [sys(" >> CAT"), sys("用法: CAT <文件名>")];
  }
  if (c === "cat loop.log") {
    return [
      sys(" >> CAT LOOP.LOG"),
      sys(`LOOP COUNT: ${loop_count + 15498}`),
    ];
  }
  if (c === "skip") {
    return [
      sys(">> SKIP"),
      sys("  仅在播放文本的过程中跳过当前场景..."),
    ];
  }
  if (c.startsWith("go")) {
    return [
      err(">> GO 命令在此版本中仅作为剧本文档提示。"),
      err("   请使用当前场景的数字选项移动，以便场景校验保持可追踪。"),
    ];
  }
  return [
    err(`>> 未知指令: '${cmd}'`),
    err("   输入 HELP 查看可用指令列表。"),
  ];
}
