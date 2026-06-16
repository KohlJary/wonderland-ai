# Vendored: ophanic layout core

Vendored from https://github.com/KohlJary/ophanic (MIT, same author) at
the layout-toolchain layer: parser → IR → React forward/reverse adapters.
Pure-stdlib, no third-party deps. CLI, tests, and Figma-network pieces of
the upstream package are intentionally omitted.

Wonderland extends this with durable node identity + ticket linkage in the
parent `wonderland.diagrams` package (P21) — kept separate so the vendored
core stays a clean drop-in we can refresh from upstream.
