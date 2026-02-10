# EU AI Act Annex IV Alignment Table

| Annex IV Requirement | Description | Venturalítica SDK Implementation | Completeness |
| :--- | :--- | :--- | :--- |
| **2(a) Development Methods** | Methods/steps, pre-trained systems, third-party tools integration. | `TraceProbe` captures AST (logic) + Call Stack. `BOMProbe` captures exact `pip freeze` of all 3rd party tools. | ✅ High |
| **2(b) Design Specifications** | Logic, algorithms, optimization goals, target groups, trade-offs. | `SystemPolicy` (OSCAL) defines objectives. `Dashboard` Transparency View visualizes logic alignment. | ✅ High |
| **2(c) System Architecture** | Component integration, computational resources used. | `HardwareProbe` (CPU/RAM). `TraceProbe` (Duration/Success). `BOMProbe` (Component Graph). | ✅ High |
| **2(d) Data Requirements** | Training methodologies, datasets, provenance, scope, labeling, cleaning. | `ArtifactProbe` captures Rich Metadata for **Files, SQL Queries, and S3 Objects**. Includes Hashes + Timestamps. | ✅ High |
| **2(e) Human Oversight** | Measures for Article 14, output interpretation tools. | `HandshakeProbe` mandates `vl.enforce()`. Dashboard provides "Glass Box" interpretability. | ✅ High |
| **2(f) Change Management** | Pre-determined changes, continuous compliance technical solutions. | `IntegrityProbe` detects drift. `CI` Strict Mode prevents unapproved changes from deploying. | ✅ High |
| **2(g) Validation & Testing** | Testing data, metrics (accuracy/robustness/bias), test logs. | `vl.monitor()` captures execution metrics. `ComplianceResult` binds metrics to policy objectives. | ✅ High |
| **2(h) Cybersecurity** | Cybersecurity measures put in place. | **HMAC-SHA256 Signing** of evidence + `IntegrityProbe` (Environment Fingerprinting). | ✅ High (Pilot) |
