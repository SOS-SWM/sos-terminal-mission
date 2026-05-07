import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";

// SOS Terminal Mission — Web 版构建配置
// - alias 直接指向 ../Engine/ 下的 books / assets，避免重复拷贝
// - assetsInclude: 让 Markdown 与 GLSL 进入打包（配合 ?raw 后缀使用）
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@books": fileURLToPath(new URL("../Engine/books", import.meta.url)),
      "@assets": fileURLToPath(new URL("../Engine/assets", import.meta.url)),
    },
  },
  assetsInclude: ["**/*.md", "**/*.glsl"],
  server: {
    // 默认 5173 与许多其他工具撞车，固定到 dynamic port range 里一个不常用的高端口
    port: 52389,
    strictPort: true,
    fs: {
      // 允许 Vite 读取项目根目录之外的 ../Engine/{books,assets}
      allow: [fileURLToPath(new URL("..", import.meta.url))],
    },
  },
  build: {
    target: "es2022",
    sourcemap: true,
  },
});
