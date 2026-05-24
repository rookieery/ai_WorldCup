---
name: code-stats
description: 统计项目代码行数，区分前端和后端，排除依赖文件和生成文件。
allowed-tools: Bash
---

# Code Statistics Skill

## 上下文
- 项目根目录：`d:/code/ai_WorldCup`
- 前端项目：`football-web/`
- 后端项目：`football-server/`

## 执行步骤

1. **统计前端代码行数**：在前端目录中，排除 `node_modules`、`.next`、锁文件、生成文件等，按文件类型分类统计行数。

   ```bash
   cd "d:/code/ai_WorldCup/football-web" && find app components lib hooks styles -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.css" -o -name "*.json" \) ! -path "*/node_modules/*" ! -path "*/.next/*" ! -path "*/package-lock.json" | while read f; do ext="${f##*.}"; lines=$(wc -l < "$f"); printf "%s %d\n" "$ext" "$lines"; done | awk '{arr[$1]+=$2; total+=$2} END {for(k in arr) printf "  %-8s %6d 行\n", k, arr[k]; printf "  %-8s %6d 行\n", "TOTAL", total}'
   ```

2. **统计后端代码行数**（如有）：

   ```bash
   cd "d:/code/ai_WorldCup/football-server" && find src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.json" \) ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/package-lock.json" 2>/dev/null | while read f; do ext="${f##*.}"; lines=$(wc -l < "$f"); printf "%s %d\n" "$ext" "$lines"; done | awk '{arr[$1]+=$2; total+=$2} END {for(k in arr) printf "  %-8s %6d 行\n", k, arr[k]; if(total>0) printf "  %-8s %6d 行\n", "TOTAL", total}'
   ```

3. **汇总输出**：将上述结果整理为如下格式展示给用户：

   ```
   📊 项目代码统计

   ━━━ 前端 (football-web) ━━━
     .tsx       xxxx 行
     .ts        xxxx 行
     .css       xxxx 行
     ...
     TOTAL      xxxx 行

   ━━━ 后端 (football-server) ━━━
     .ts        xxxx 行
     ...
     TOTAL      xxxx 行

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   项目总计: xxxx 行
   ```

## 注意事项
- 必须排除：`node_modules`、`.next`、`dist`、`build`、`coverage`、`package-lock.json`、`*.log`、`*.min.*`
- 只统计源码文件，不统计配置文件（next.config.mjs、tsconfig.json 等）
- 如果用户只关心某一端，可以只运行对应步骤
