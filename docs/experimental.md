# Experimental Features

This page documents CLI commands and features that are currently experimental. Their API may change or be removed in future releases.

!!! warning "Experimental"
    These features depend on the Venturalitica SaaS platform, which is not yet publicly available. They are included in the SDK for early adopters and internal testing.

---

## CLI: `login`

Authenticate with the Venturalitica SaaS platform.

```bash
venturalitica login
```

Stores credentials locally for use by `pull` and `push` commands. Authentication is required before using any SaaS-connected features.

---

## CLI: `pull`

Pull OSCAL policies and system configuration from the SaaS platform to your local project.

```bash
venturalitica pull
```

### What It Downloads

| File | Description |
| :--- | :--- |
| `model_policy.oscal.yaml` | Model fairness and performance policy |
| `data_policy.oscal.yaml` | Data quality and privacy policy |
| `system_description.yaml` | Annex IV.1 system identity fields |

### Behavior

- Authenticates using stored credentials from `login`
- Fetches policies from `/api/pull?format=oscal`
- Writes files to the current working directory
- Reports bound and unbound risks from the SaaS platform

!!! note "Format Difference"
    The `pull` command currently downloads policies in `system-security-plan` OSCAL format, while the Dashboard Policy Editor generates `assessment-plan` format. Both formats are supported by the SDK loader, but the difference may cause confusion when editing pulled policies in the Dashboard. This will be unified in a future release.

---

## CLI: `push`

Push local compliance evidence to the Venturalitica SaaS platform.

```bash
venturalitica push
```

Uploads enforcement results and trace files from `.venturalitica/` to the cloud for team visibility and audit trails.

---

## CLI: `ui` (Stable)

Launch the local Glass Box Dashboard. This command is **stable** and fully documented.

```bash
venturalitica ui
```

See [Dashboard Guide](dashboard.md) for full documentation.

---

## Feature Status Matrix

| Feature | Status | Depends On |
| :--- | :--- | :--- |
| `venturalitica ui` | Stable | Local only |
| `venturalitica login` | Experimental | SaaS platform |
| `venturalitica pull` | Experimental | SaaS platform |
| `venturalitica push` | Experimental | SaaS platform |
| `vl.enforce()` | Stable | Local only |
| `vl.monitor()` | Stable | Local only |
| `vl.quickstart()` | Stable | Local only |
| `vl.wrap()` | Experimental | Local only |

---

## Providing Feedback

If you are testing experimental features, report issues at [GitHub Issues](https://github.com/venturalitica/venturalitica-sdk/issues/new).
