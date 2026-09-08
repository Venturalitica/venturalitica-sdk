# Security Policy

## Scope

This policy covers **`venturalitica`**, the Python package published to PyPI from this
repository. That is the product name in the market; `venturalitica-sdk` is only the name of
the repository.

This file exists so that you do not have to guess where the policy lives. The contact below
is the same one Venturalítica publishes for its other components — you are in the right place.

## Reporting a vulnerability (coordinated disclosure)

Email **security@venturalitica.ai** with a description, reproduction steps, and impact.

- Acknowledgement of receipt: **within 72 hours**.
- Initial assessment: **within 7 days**.
- Please do not disclose publicly until we confirm a fix (coordinated disclosure).
- If your report contains sensitive data, we prefer PGP; ask for the key in your first mail.

Please report privately by email rather than opening a public issue.

## Supported period

| Product | Supported until |
|---|---|
| `venturalitica` (PyPI package) | **2028-08-30** |

Two things this does and does not mean, stated because the difference matters:

- **The period covers the product, not each release.** Security fixes are delivered
  **forward**, as a new version — not as backports to earlier ones. The supported version is
  the current one.
- The period is declared **below** the five-year default of Article 13(8) of the Cyber
  Resilience Act (Regulation (EU) 2024/2847) deliberately, not by omission. The Article sets
  the period to the expected time in use where that is shorter than five years. This is a 0.x
  package in a moving regulatory domain, published continuously, where any given deployment is
  superseded within months.

Independently of that period, the Apache-2.0 licence means you can maintain the package
yourself. The continuity of your use rests on the licence, not on our support window.

## Third-party dependencies

Dependencies are pinned in `uv.lock` and inventoried in the CycloneDX SBOM published with the
repository. Vulnerabilities in a third-party dependency should be reported upstream first; tell
us as well if the SDK's use of it makes the impact worse.
