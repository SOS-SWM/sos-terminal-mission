// books.ts — 通过 Vite 的 ?raw 加载四章 Markdown 剧本

import ch1 from "@books/Chapter1.md?raw";
import ch2 from "@books/Chapter2.md?raw";
import ch3 from "@books/Chapter3.md?raw";
import ch4 from "@books/Chapter4.md?raw";

export const BOOK_TEXTS: ReadonlyArray<string> = [ch1, ch2, ch3, ch4];
