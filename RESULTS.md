
## v0.15.1 — main-window layout fix (post-screenshot review)
The v0.15 live screenshot showed the results Treeview (default 10 rows) consuming the whole
1080x680 window and squeezing the "Chi tiết máy đã chọn" detail card out of view. Fix: Treeview
height=7 visible rows, window 1120x730 (minsize 940x620). Verified by re-running the GUI smoke +
theme suite (green) and a fresh live screenshot with a scanned miner selected — detail card
(dead-chip positions, fan speeds) now visible under the table.

## v0.15.2 — main-window balance fix (supersedes v0.15.1)
v0.15.1's screenshot still showed the detail card crushed (root request 943px vs 730px window;
pack starves the last widgets). v0.15.2 converts the main window's section layout from pack to
grid with the table row weighted (minsize 150): the table now absorbs any shortfall and the
detail pane always keeps full height. Card padding trimmed (16->12), detail text 5 lines,
default window 1120x880. Measured on the live window: header 67 / toolbar 153 / stats 110 /
table 253 (of 270) / detail 191 full / footer 24 — everything visible, GUI + theme suites green.
