# BeeSky marketing prototypes

Three standalone Vietnamese landing page prototypes. Not connected to production routing.

From the repository root run `python -m http.server 8794 --bind 127.0.0.1`.

- Corporate: http://127.0.0.1:8794/marketing-preview/
- Mine: http://127.0.0.1:8794/marketing-preview/mine.html
- FlowDocker: http://127.0.0.1:8794/marketing-preview/flowdocker.html

Current approved content structure: BeeSky is the company providing enterprise technology solutions. FlowDocker and BeeSky Mine are separate products. AutoVideo is excluded. Company/FlowDocker pages use portal.js and portal.css; Mine uses story.js, miner-demo.js, mine-ecosystem.js and the bundled hardware renderer. Mine opens with the Scanner/Agent/Cloud ecosystem; hardware models are below the feature tour. AI/MCP explicitly states that the integration into the new cloud is pending. Contact drafts can be copied, but are not submitted. FlowDocker demo does not create real documents or signatures; a live FlowDocker application URL has not been configured.

Application buttons open the existing local backend at port 8793. All visual metrics and warehouse previews are explicitly illustrative. Company service positioning is proposed copy. Contact details need confirmation before publication.

Current direction: product presentation with large local 3D models, minimal copy and three scroll chapters (space, power, maintenance). On mobile and with reduced motion, use the chapter buttons. Motion can be disabled in the footer. Operational actions open the existing app.

The Three.js renderer uses the existing local GLB files and bundles the repository's pinned Three.js dependency. No external fonts, analytics or remote assets. Rebuild after editing hardware-source.js:

`node cloud-preview/rack3d/node_modules/esbuild/bin/esbuild marketing-preview/hardware-source.js --bundle --minify --format=esm --outfile=marketing-preview/hardware.js`

Active entry points use story.js, story.css and hardware.js; main.js, style.css and editorial.css preserve the earlier prototype directions.

## Current company presentation

The company entry loads portal.js, company-sections.js, ivory.js, product-scroll.js, page-depth.js and tech-background.js, with matching CSS overrides. Local generated artwork is stored in assets/. The four-panel hero has animated data paths; lower sections use pearl illustrations, scroll parallax and full-width technology scenery. A translucent bee hovers at the left edge. Footer motion controls and reduced-motion preferences pause or disable decorative movement.


## Public delivery

Approved public domain: https://beeskybase.com/ (company), /mine.html (Mine introduction), /flowdocker.html (FlowDocker introduction). Cloud application links use https://mine.beeskybase.com/. Build the static release with `python tools/build_marketing_site.py work/marketing-site.tar.gz`; it includes public fonts, logo, artwork and miner GLBs, with no backend configuration or credentials. The existing proxy serves the versioned static directory independently of the Mine backend.

