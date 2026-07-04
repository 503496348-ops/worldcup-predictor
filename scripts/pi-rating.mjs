// Pi-Rating system — Constantinou & Fenton (2012)
// Responds to goal DIFFERENCE, not just win/loss — a 5-0 win generates a larger
// rating change than a 1-0 win, with diminishing returns to prevent blowouts
// from dominating.
// Zero-centered: positive = better than average, negative = worse.

// ── Config ─────────────────────────────────────────────────────────────────
const PI_K = 0.1;           // learning rate (sensitivity to new results)
const PROB_SCALE = 0.35;    // probability scaling factor
const HOME_ADJ = 0.3;       // home advantage adjustment

// ── Goal-difference multiplier with diminishing returns ─────────────────────
// Mirrors the wc26-predict penaltyblog approach:
//   gd=1 → 1.0, gd=2 → 1.5, gd=3+ → (11+gd)/8
function goalDiffMultiplier(gd) {
  const d = Math.abs(gd);
  if (d <= 1) return 1.0;
  if (d === 2) return 1.5;
  return (11 + d) / 8;
}

// ── Core rating update ─────────────────────────────────────────────────────
function updateRating(currentRating, homeGoals, awayGoals, isHome) {
  const gd = isHome ? homeGoals - awayGoals : awayGoals - homeGoals;
  // Expected goal diff from current rating advantage
  const expected = 1.0; // baseline expectation
  const mult = goalDiffMultiplier(gd);
  const surprise = gd > 0 ? mult : gd < 0 ? -mult : 0;
  return currentRating + PI_K * surprise;
}

// ── PiRatingSystem class ───────────────────────────────────────────────────
export class PiRatingSystem {
  constructor(k = PI_K) {
    this.k = k;
    this.ratings = new Map(); // team → { home: number, away: number }
    this.matchCount = 0;
  }

  getTeam(team) {
    if (!this.ratings.has(team)) {
      this.ratings.set(team, { home: 0.0, away: 0.0 });
    }
    return this.ratings.get(team);
  }

  // Update ratings from a single match result
  update(homeTeam, awayTeam, homeGoals, awayGoals) {
    const h = this.getTeam(homeTeam);
    const a = this.getTeam(awayTeam);

    const gd = homeGoals - awayGoals;
    const mult = goalDiffMultiplier(gd);
    const delta = this.k * (gd > 0 ? mult : gd < 0 ? -mult : 0);

    h.home += delta;
    a.away -= delta;
    this.matchCount++;
    return { homeDelta: delta, awayDelta: -delta };
  }

  // Get average rating for a team (mean of home + away)
  getRating(team) {
    const r = this.getTeam(team);
    return (r.home + r.away) / 2.0;
  }

  // Predict match outcome from Pi-Ratings
  predict(homeTeam, awayTeam, isNeutral = false) {
    const homeR = this.getRating(homeTeam);
    const awayR = this.getRating(awayTeam);
    const adj = isNeutral ? 0.0 : HOME_ADJ;

    const xgDiff = (homeR + adj - awayR) * PROB_SCALE * 2.0;

    const homeWinRaw = 1.0 / (1.0 + Math.exp(-xgDiff * 2.5));
    const awayWinRaw = 1.0 / (1.0 + Math.exp(xgDiff * 2.5));
    const drawRaw = 0.26 * Math.exp(-(xgDiff ** 2) / 2.0);

    const total = homeWinRaw + drawRaw + awayWinRaw;
    return {
      homeWin: homeWinRaw / total,
      draw: drawRaw / total,
      awayWin: awayWinRaw / total,
    };
  }

  // Fit from historical matches array: [{ home, away, hg, ag }, ...]
  fitFromMatches(matches) {
    const sorted = matches.slice().sort((a, b) => (a.ts || 0) - (b.ts || 0));
    for (const m of sorted) {
      if (m.hg == null || m.ag == null) continue;
      this.update(m.home, m.away, m.hg, m.ag);
    }
    return this;
  }

  // Export all ratings as plain object
  toJSON() {
    const obj = {};
    for (const [team, r] of this.ratings) {
      obj[team] = { home: +r.home.toFixed(4), away: +r.away.toFixed(4), avg: +this.getRating(team).toFixed(4) };
    }
    return { k: this.k, matchCount: this.matchCount, ratings: obj };
  }
}

// ── Fuse Pi-Rating probabilities into existing model output ─────────────────
export function fusePiProbs(baseProbs, piPred, piWeight = 0.10) {
  const keys = ['homeWin', 'draw', 'awayWin'];
  const fused = {};
  for (const k of keys) {
    fused[k] = baseProbs[k] * (1.0 - piWeight) + piPred[k] * piWeight;
  }
  // Renormalize
  const total = keys.reduce((s, k) => s + fused[k], 0);
  for (const k of keys) fused[k] /= total;
  return fused;
}
