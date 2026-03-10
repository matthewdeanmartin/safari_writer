 1. Syntax highlighting — Color keywords (PRINT, FOR, GOTO) in the input line and LIST output. Cyan for keywords, green for strings, yellow for numbers. Keeps the 8-bit feel but uses ANSI
   colors.
  2. PROFILE command — Run a program and show which lines executed most often and how long each took. Like a mini profiler: PROFILE RUN → shows a heat map of line execution counts.
  3. DIFF — Show what changed since the last SAVE or LOAD. Like git diff for your BASIC program. Useful after a batch of edits.
  4. WATCH <var> — Set a watchpoint: break execution whenever a variable changes value. Complementary to TRON VARS but more targeted.
  5. BREAK <line> / BREAKS — Set breakpoints on specific lines. BREAKS lists them. UNBREAK <line> removes them. When hit, drops to immediate mode with CONT to resume.
  6. CROSSREF — Cross-reference table showing where each variable and line number is used/referenced. Great for understanding unfamiliar programs.
  7. PRETTY — Auto-indent FOR/NEXT, GOSUB/RETURN blocks when listing. Makes structure visible at a glance.
  8. SNIPPET library — Built-in named code templates: SNIPPET SORT inserts a bubble sort subroutine, SNIPPET MENU inserts a menu loop pattern. Teach by example.
  9. BENCHMARK <n> — Run the program N times and report min/avg/max time. Perfect for optimization challenges.
  10. EXPORT HTML — Export the current program as a syntax-highlighted HTML file. Share your creations on the web.
  11. Multi-line paste detection — Detect when multiple lines are pasted at once and process them all, showing a count ("12 LINES ENTERED") rather than echoing each one.
  12. ! shell escape — !ls, !date, etc. Execute a shell command without leaving the REPL. Classic Unix REPL convention.