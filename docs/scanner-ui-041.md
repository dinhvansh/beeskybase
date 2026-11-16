# Mine Scanner 0.41.0 — native UI refresh

The scanner and embedded Agent use the same cool neutral palette as Mine Cloud.
Brand yellow highlights primary actions; navigation and secondary controls stay
neutral. Existing scan, credentials, groups, operations, persistence and Agent
contracts are retained.

- Shared 52px top bar, collapsible sidebar, automatic icon rail on smaller
  windows, tooltips and keyboard command search.
- Flatter network rows, compact scan header and status summaries.
- Search has an icon and clear action. Advanced columns/density/data modes live
  under **Hiển thị**; history and saved presets remain accessible from tooltips.
- Table columns fit more data before horizontal scrolling; an always-visible
  horizontal scrollbar makes hidden columns discoverable.
- Short windows scroll the controls separately while retaining table space;
  machine details remain scrollable when vertical space is limited.
- Agent uses two columns on wide screens and a single column on laptops. Start,
  Save and Test remain at the bottom of the window. The token has a visibility
  button; its destination remains readonly and controlled by the server.
- Installer shortcuts open the redesigned native UI by default. The old Tk UI is
  retained as **Compatibility**. Configuration paths and scheduled tasks are
  unchanged.

Validation on Windows: Scanner widget/model suite and Agent suite, plus laptop
layout tests at 1024×640. Headless rendered reviews at 1366×768 and 1024×640 cover
network groups, real-table layout against mock telemetry, display settings and
Agent. These UI checks use synthetic data; no live miner commands are sent.

Current Flutter stable reports Material facade deprecation information. CI keeps
warnings/errors fatal and uses `--no-fatal-infos`; no framework migration is part
of this change.
