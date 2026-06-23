# Regression QA Notes

Status: PASS

- Deterministic seed supports rebuild comparison.
- Pre-upgrade PBIX/script/layout backups are stored under `archive/old_versions/project20_upgrade_before_*`.
- Final package readback confirms Project 15 SaaS CFO pages only: Executive Overview, Revenue & Retention, Efficiency & Forecast.
- Final package readback confirms `contains_esg_layout_text=false`, guarding against the unrelated Project 18 `dashboard_final.pbix` window collision found during Desktop validation.
- Final SHA256: `80F3678A5BF741101913CFF02AE471504185AC4C5D5AE91AD7C0806531A95B45`.
