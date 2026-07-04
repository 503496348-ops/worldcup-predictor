# Changelog

All notable changes to `worldcup-predictor` should be documented in this file.

This repository follows a lightweight Keep-a-Changelog style and semantic versioning where applicable.

## [2.0.0] — 2026-07-04

### Added — Pi-Rating + Conformal Prediction Fusion
- **Pi-Rating system** (`scripts/pi-rating.mjs`): Constantinou & Fenton (2012) goal-difference-sensitive rating. Responds to score margin, not just W/D/L. Zero-centered, diminishing-returns multiplier for blowouts.
- **Weighted Conformal Prediction** (`scripts/conformal.mjs`): Split-conformal for 3-class H/D/A forecasts with exponential recency weighting (30-day halflife). Provides prediction sets with 90% coverage guarantees and confidence labels (high/medium/low).
- **predict.mjs v2**: Integrated 3-model fusion — Elo+DC (85%) + Pi-Rating (15%) + Conformal output. Shows component breakdown, fused probabilities, expected goals, and conformal prediction set with adjusted probabilities.
- Data files: `pi-ratings.json` (calibrated Pi-Ratings), `conformal-calibration.json` (historical calibration records).

### Changed
- predict.mjs output now includes component-level breakdown when Pi-Rating is available.

## Unreleased

- Governance baseline initialized.
