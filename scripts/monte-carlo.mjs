#!/usr/bin/env node
// Monte Carlo match simulation — Poisson-based scoreline sampling
// Fixes probability fixation by injecting lambda uncertainty.
// Reference: penaltyblog FootballProbabilityGrid + Dixon-Coles tau adjustment.
// Pure JS, zero dependencies, deterministic with optional seed.

// ── Poisson sampler (Knuth's algorithm) ────────────────────────────────────
function poissonSample(lambda, rng = Math.random) {
  if (lambda <= 0) return 0;
  if (lambda > 30) {
    // Normal approximation for large lambda
    const std = Math.sqrt(lambda);
    return Math.max(0, Math.round(lambda + std * normalSample(rng)));
  }
  let L = Math.exp(-lambda);
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rng();
  } while (p > L);
  return k - 1;
}

// Box-Muller normal sample
function normalSample(rng = Math.random) {
  const u1 = rng();
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(Math.max(u1, 1e-10))) * Math.cos(2 * Math.PI * u2);
}

// ── Dixon-Coles tau adjustment ─────────────────────────────────────────────
function dixonColesTau(h, a, lambdaH, lambdaA, rho) {
  if (h === 0 && a === 0) return 1 - rho * lambdaH * lambdaA;
  if (h === 1 && a === 0) return 1 + rho * lambdaH;
  if (h === 0 && a === 1) return 1 + rho * lambdaA;
  if (h === 1 && a === 1) return 1 - rho;
  return 1;
}

// ── Analytic probability grid (from penaltyblog) ───────────────────────────
function poissonPmf(k, lambda) {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  return Math.exp(-lambda) * Math.pow(lambda, k) / factorial(k);
}

function factorial(n) {
  if (n <= 1) return 1;
  let r = 1;
  for (let i = 2; i <= n; i++) r *= i;
  return r;
}

/**
 * Compute analytic score probability grid with Dixon-Coles adjustment.
 * @param {number} lambdaH - Home expected goals
 * @param {number} lambdaA - Away expected goals
 * @param {number} rho - Dixon-Coles correlation (-0.13 typical)
 * @param {number} maxGoals - Grid size
 * @returns {Object} { grid, homeWin, draw, awayWin, mostLikelyScore }
 */
export function scoreProbabilityGrid(lambdaH, lambdaA, rho = -0.13, maxGoals = 8) {
  const grid = [];
  let homeWin = 0, draw = 0, awayWin = 0;
  let bestScore = [0, 0], bestProb = 0;

  for (let h = 0; h <= maxGoals; h++) {
    grid[h] = [];
    for (let a = 0; a <= maxGoals; a++) {
      let prob = poissonPmf(h, lambdaH) * poissonPmf(a, lambdaA);
      prob *= dixonColesTau(h, a, lambdaH, lambdaA, rho);
      grid[h][a] = prob;

      if (h > a) homeWin += prob;
      else if (h === a) draw += prob;
      else awayWin += prob;

      if (prob > bestProb) {
        bestProb = prob;
        bestScore = [h, a];
      }
    }
  }

  // Normalize
  const total = homeWin + draw + awayWin;
  return {
    homeWin: homeWin / total,
    draw: draw / total,
    awayWin: awayWin / total,
    mostLikelyScore: `${bestScore[0]}-${bestScore[1]}`,
    grid,
  };
}

// ── Monte Carlo simulation ─────────────────────────────────────────────────
/**
 * Run Monte Carlo match simulation with lambda uncertainty.
 *
 * Instead of a single (λH, λA) → fixed probability, we:
 * 1. Sample λH' ~ Gamma(λH, λH/shapeK) and λA' ~ Gamma(λA, λA/shapeK)
 * 2. Sample goals from Poisson(λH') and Poisson(λA')
 * 3. Repeat N times, aggregate outcomes
 *
 * This naturally produces different distributions each run because
 * the Poisson sampling introduces genuine randomness.
 *
 * @param {number} lambdaH - Base home expected goals
 * @param {number} lambdaA - Base away expected goals
 * @param {number} rho - Dixon-Coles rho (default -0.13)
 * @param {number} nSim - Number of simulations (default 10000)
 * @param {number} lambdaUncertainty - CV of lambda uncertainty (default 0.15)
 * @param {Function} rng - Random number generator (default Math.random)
 * @returns {Object} { homeWin, draw, awayWin, scoreDistribution, confidence95 }
 */
export function monteCarloSimulate(
  lambdaH, lambdaA,
  rho = -0.13,
  nSim = 10000,
  lambdaUncertainty = 0.15,
  rng = Math.random
) {
  let homeWins = 0, draws = 0, awayWins = 0;
  const scoreCounts = {};
  const goalDiffs = [];

  // Gamma shape parameter — higher = less lambda uncertainty
  const shapeK = 1 / (lambdaUncertainty * lambdaUncertainty);

  for (let i = 0; i < nSim; i++) {
    // Sample uncertain lambdas from Gamma distribution
    const lh = gammaSample(shapeK, lambdaH / shapeK, rng);
    const la = gammaSample(shapeK, lambdaA / shapeK, rng);

    // Sample goals from Poisson
    const hg = poissonSample(Math.max(0.01, lh), rng);
    const ag = poissonSample(Math.max(0.01, la), rng);

    // Apply DC tau adjustment probabilistically for low scores
    if (hg <= 1 && ag <= 1 && rho !== 0) {
      const tau = dixonColesTau(hg, ag, lh, la, rho);
      if (rng() > Math.abs(tau)) continue; // reject sample
    }

    if (hg > ag) homeWins++;
    else if (hg === ag) draws++;
    else awayWins++;

    const key = `${hg}-${ag}`;
    scoreCounts[key] = (scoreCounts[key] || 0) + 1;
    goalDiffs.push(hg - ag);
  }

  const n = homeWins + draws + awayWins;
  goalDiffs.sort((a, b) => a - b);

  // Top 10 most likely scores
  const topScores = Object.entries(scoreCounts)
    .map(([score, count]) => ({ score, prob: count / n }))
    .sort((a, b) => b.prob - a.prob)
    .slice(0, 10);

  // 95% confidence interval on goal difference
  const ci95 = [
    goalDiffs[Math.floor(n * 0.025)],
    goalDiffs[Math.ceil(n * 0.975)],
  ];

  return {
    homeWin: homeWins / n,
    draw: draws / n,
    awayWin: awayWins / n,
    nSimulations: n,
    topScores,
    expectedGoalDiff: goalDiffs.reduce((s, v) => s + v, 0) / n,
    confidence95_goalDiff: ci95,
  };
}

// ── Gamma sampler (Marsaglia & Tsang) ──────────────────────────────────────
function gammaSample(shape, scale, rng = Math.random) {
  if (shape < 1) {
    return gammaSample(shape + 1, scale, rng) * Math.pow(rng(), 1 / shape);
  }
  const d = shape - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  while (true) {
    let x, v;
    do {
      x = normalSample(rng);
      v = 1 + c * x;
    } while (v <= 0);
    v = v * v * v;
    const u = rng();
    if (u < 1 - 0.0331 * x * x * x * x) return d * v * scale;
    if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v * scale;
  }
}

// ── Combined: analytic grid + Monte Carlo ───────────────────────────────────
/**
 * Full prediction: analytic probabilities + Monte Carlo with uncertainty.
 * @param {number} lambdaH - Home expected goals
 * @param {number} lambdaA - Away expected goals
 * @param {Object} opts - { rho, nSim, lambdaUncertainty, rng }
 * @returns {Object} analytic + monteCarlo results
 */
export function fullPrediction(lambdaH, lambdaA, opts = {}) {
  const {
    rho = -0.13,
    nSim = 10000,
    lambdaUncertainty = 0.15,
    rng = Math.random,
  } = opts;

  const analytic = scoreProbabilityGrid(lambdaH, lambdaA, rho);
  const mc = monteCarloSimulate(lambdaH, lambdaA, rho, nSim, lambdaUncertainty, rng);

  return {
    analytic: {
      homeWin: +analytic.homeWin.toFixed(4),
      draw: +analytic.draw.toFixed(4),
      awayWin: +analytic.awayWin.toFixed(4),
      mostLikelyScore: analytic.mostLikelyScore,
    },
    monteCarlo: {
      homeWin: +mc.homeWin.toFixed(4),
      draw: +mc.draw.toFixed(4),
      awayWin: +mc.awayWin.toFixed(4),
      nSimulations: mc.nSimulations,
      topScores: mc.topScores,
      expectedGoalDiff: +mc.expectedGoalDiff.toFixed(2),
      confidence95_goalDiff: mc.confidence95_goalDiff,
    },
    // Use MC probabilities as the "live" output (varies each run)
    live: {
      homeWin: +mc.homeWin.toFixed(4),
      draw: +mc.draw.toFixed(4),
      awayWin: +mc.awayWin.toFixed(4),
    },
  };
}
