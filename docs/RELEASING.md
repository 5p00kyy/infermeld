# Release checklist

Infermeld is experimental and source-only. This checklist prepares a release; running source checks or pushing a private candidate does not publish it.

## Candidate gates

- [ ] Review the complete candidate diff, including new assets, tests and workflow permissions.
- [ ] Run `make test` and `make package`.
- [ ] Extract the bundle into a separate directory, verify `SOURCE-MANIFEST.json`, and run `make test` there.
- [ ] Confirm that `infermeld.py` still matches the retained CLI-acceptance digest. A changed launcher needs fresh hardware acceptance before reusing that claim.
- [ ] Review mobile and desktop rendering, keyboard disclosure/navigation, code scrolling, evidence downloads and chart controls.
- [ ] Preview the site under `/infermeld/`, not just `/`; all local site URLs must remain relative.
- [ ] Scan the source bundle and every commit intended for public visibility for private paths, addresses, identities and credentials. Review author metadata too. A clean tip does not erase previous Git blobs. Resolve historical disclosure or approve a separate clean-history export before changing visibility; do not rewrite shared history implicitly.
- [ ] Push the reviewed candidate privately and require successful source checks on that exact SHA. CI tests source and bundle contracts, not GPUs.

## Approved publication only

1. Obtain explicit approval to publish the repository, site and release. Do not infer this from private-candidate approval.
2. Resolve the history/privacy gate above. Keep the original private repository until any approved export is verified.
3. Replace the neutral **Source checks · CPU-only** badge with the native live workflow image documented in the README. Keep the hardware/CI distinction visible. Verify the public image actually loads; do not substitute a static passing badge.
4. Push any release-copy change and repeat exact-head checks before tagging. Add a version badge only when the real tag exists.
5. Make the approved source public and review it without authentication. Check README images, license/attribution, documentation links and downloadable evidence.
6. Configure GitHub Pages to use **GitHub Actions**, with the `github-pages` environment restricted to `main`. The prepared workflow cannot run on push, pull request, private repositories or non-main refs. It defaults to `publish=false` and does not enable Pages itself.
7. Manually dispatch **Publish Pages (manual)** on `main` with `publish=true`. Confirm that the deployed commit is the approved candidate. Verify the live `/infermeld/` site, mobile layout, JSON downloads, historical chart and return navigation.
8. Publish a source-only tag/release from the checked commit, with experimental status, requirements, exact tested scope and known limitations. Verify archive contents, manifest and public downloads. Do not distribute weights, engine binaries, toolkits or private receipts.

## Claims to preserve

- Mixed-vendor execution is llama.cpp's capability, not an Infermeld invention.
- The fresh-build launcher acceptance is MoE Q4 at an 8K reservation, with and without MTP4: short checks and owned teardown only.
- Q4 allocation up to 128K does not prove filled-context ingestion, recall or an optimum. Retain the failed dense 3:2 attempt beside the separate 2:1 retry.
- The IQ3-named measurements use different artifacts and a historical engine cohort. They are not Q4 speeds or a universal mixed-GPU speedup.
- Neither sustained Q4 throughput nor maximum useful context is qualified. No aborted run supplies a performance number.

The deployment workflow uses immutable action revisions. Updating those pins, adding automatic deployment or expanding hardware support requires review rather than a release-copy edit.
