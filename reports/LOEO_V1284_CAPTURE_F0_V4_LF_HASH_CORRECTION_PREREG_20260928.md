# V1284 fold0 capture v4 — predictor LF hash correction

Written 2026-09-28 before correcting the v4 source contract and rebuilding
its manifest. This addendum preserves the earlier preregistration
`LOEO_V1284_CAPTURE_F0_V4_LF_WATCHER_PREREG_20260928.md` unchanged.

The earlier preregistration and initial v4 contract copied a truncated,
63-character predictor LF SHA (`330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e`).
The direct Windows local execution of the v4 cell4 generated 55,227 bytes,
1,235 LF newlines, zero CR bytes, and full SHA256
`330b7407fbf8d0f89af22f8821dffc9bc17332d37179fd87f04dca9819b6c4e5`.
The generated module is 3,423 bytes, 79 LF, zero CR, SHA256
`940e6d18c4a2f93d5df43912b36d4dec308a3b551686285f25a351b1da354894`.

Use the full 64-character predictor SHA in the v4 contract and plan. Pin this
addendum's hash alongside the original preregistration and prove both LF/CRLF
input variants yield the same exact bytes and hashes. All other controls,
local-only boundary, and independent review requirements remain as written.
