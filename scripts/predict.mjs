#!/usr/bin/env node
// Predict any head-to-head from the calibrated ratings.
//   node predict.mjs brazil argentina            (neutral venue)
//   node predict.mjs usa mexico usa               (3rd arg = home team)
//
// V2.0 — Integrated: Elo+DC + Pi-Rating + Conformal Prediction
import { readFileSync, existsSync } from "node:fs";
import { matchProb } from "./elo.mjs";
import { PiRatingSystem, fusePiProbs } from "./pi-rating.mjs";
import { conformalPredict } from "./conformal.mjs";
import { monteCarloSimulate, scoreProbabilityGrid } from "./monte-carlo.mjs";

const D = (f) => new URL(`../data/${f}`, import.meta.url);

// ── Load Elo ratings ───────────────────────────────────────────────────────
const { ratings } = JSON.parse(readFileSync(D("elo-calibrated.json"), "utf8"));

// ── Load Pi-Ratings (if available) ─────────────────────────────────────────
let piSystem = null;
const piDataPath = D("pi-ratings.json");
if (existsSync(piDataPath)) {
  try {
    const piData = JSON.parse(readFileSync(piDataPath, "utf8"));
    piSystem = new PiRatingSystem(piData.k || 0.1);
    for (const [team, r] of Object.entries(piData.ratings || {})) {
      const t = piSystem.getTeam(team);
      t.home = r.home || 0;
      t.away = r.away || 0;
    }
    piSystem.matchCount = piData.matchCount || 0;
  } catch { piSystem = null; }
}

// ── Load calibration records (if available) ────────────────────────────────
let calibRecords = [];
const calibPath = D("conformal-calibration.json");
if (existsSync(calibPath)) {
  try {
    const cData = JSON.parse(readFileSync(calibPath, "utf8"));
    calibRecords = cData.records || [];
  } catch { calibRecords = []; }
}

// ── Parse CLI args ─────────────────────────────────────────────────────────
const [a, b, home] = process.argv.slice(2);

if (!a || !b) {
  console.log("Usage: node predict.mjs <teamA> <teamB> [homeTeam]\n");
  console.log("Teams:\n  " + Object.keys(ratings).sort().join(", "));
  process.exit(0);
}

const ra = ratings[a], rb = ratings[b];
if (ra == null || rb == null) {
  console.error(`Unknown team: ${ra == null ? a : b}\nAvailable: ${Object.keys(ratings).sort().join(", ")}`);
  process.exit(1);
}

// ── Elo+DC base prediction ─────────────────────────────────────────────────
const hb = home === a ? 75 : home === b ? -75 : 0;
const eloPred = matchProb(ra, rb, hb);
const bar = (x) => "█".repeat(Math.round(x * 30));

// ── Pi-Rating prediction (if available) ────────────────────────────────────
let piPred = null;
if (piSystem) {
  piPred = piSystem.predict(a, b, !home);
}

// ── Fuse models ────────────────────────────────────────────────────────────
let fused;
if (piPred) {
  // Weighted fusion: Elo+DC 85%, Pi-Rating 15%
  fused = {
    homeWin: eloPred.winA * 0.85 + piPred.homeWin * 0.15,
    draw: eloPred.draw * 0.85 + piPred.draw * 0.15,
    awayWin: eloPred.winB * 0.85 + piPred.awayWin * 0.15,
  };
  const total = fused.homeWin + fused.draw + fused.awayWin;
  fused.homeWin /= total;
  fused.draw /= total;
  fused.awayWin /= total;
} else {
  fused = { homeWin: eloPred.winA, draw: eloPred.draw, awayWin: eloPred.winB };
}

// ── Conformal prediction (if calibration available) ────────────────────────
let cpResult = null;
if (calibRecords.length >= 10) {
  cpResult = conformalPredict(
    [fused.homeWin, fused.draw, fused.awayWin],
    calibRecords
  );
}

// ── Monte Carlo simulation (Poisson + lambda uncertainty) ──────────────────
const mc = monteCarloSimulate(
  eloPred.expectedGoalsA,
  eloPred.expectedGoalsB,
  -0.13,  // DC rho
  10000,  // nSim
  0.15    // lambda uncertainty CV
);

// Analytic grid (penaltyblog-style Dixon-Coles)
const analyticGrid = scoreProbabilityGrid(
  eloPred.expectedGoalsA,
  eloPred.expectedGoalsB,
  -0.13
);

// ── Output ─────────────────────────────────────────────────────────────────
const label = (idx) => ["homeWin", "draw", "awayWin"][idx];

console.log(`\n  ${a} (Elo ${ra})  vs  ${b} (Elo ${rb})${hb ? `   [${home} at home]` : "   [neutral]"}`);
console.log(`  ─────────────────────────────────────────────`);
console.log(`  Model: Elo+DC${piPred ? " + Pi-Rating" : ""}${cpResult ? " + Conformal" : ""}\n`);

if (piPred) {
  console.log(`  Component      ${a.padEnd(12)} draw        ${b.padEnd(12)}`);
  console.log(`  Elo+DC         ${(eloPred.winA * 100).toFixed(1).padStart(5)}%     ${(eloPred.draw * 100).toFixed(1).padStart(5)}%     ${(eloPred.winB * 100).toFixed(1).padStart(5)}%`);
  console.log(`  Pi-Rating      ${(piPred.homeWin * 100).toFixed(1).padStart(5)}%     ${(piPred.draw * 100).toFixed(1).padStart(5)}%     ${(piPred.awayWin * 100).toFixed(1).padStart(5)}%`);
  console.log(`  ─────────────────────────────────────────`);
}

console.log(`  Fused          ${a.padEnd(12)}             ${b.padEnd(12)}`);
console.log(`  ${a.padEnd(16)} win  ${(fused.homeWin * 100).toFixed(1).padStart(5)}%  ${bar(fused.homeWin)}`);
console.log(`  ${"draw".padEnd(16)}      ${(fused.draw * 100).toFixed(1).padStart(5)}%  ${bar(fused.draw)}`);
console.log(`  ${b.padEnd(16)} win  ${(fused.awayWin * 100).toFixed(1).padStart(5)}%  ${bar(fused.awayWin)}`);

console.log(`\n  expected goals:  ${eloPred.expectedGoalsA.toFixed(2)} – ${eloPred.expectedGoalsB.toFixed(2)}`);

if (cpResult) {
  console.log(`\n  Conformal Prediction (90% coverage):`);
  console.log(`    prediction set: [${cpResult.predictionSet.map(label).join(", ")}]  (size=${cpResult.setSize})`);
  console.log(`    confidence: ${cpResult.confidence}  (calibration n=${cpResult.calibrationSize})`);
  console.log(`    adjusted probs:  ${a} ${(cpResult.adjustedProbs[0] * 100).toFixed(1)}%  draw ${(cpResult.adjustedProbs[1] * 100).toFixed(1)}%  ${b} ${(cpResult.adjustedProbs[2] * 100).toFixed(1)}%`);
}

console.log(`\n  Monte Carlo (10k sims, λ-uncertainty CV=15%):`);
console.log(`    ${a.padEnd(16)} win  ${(mc.homeWin * 100).toFixed(1).padStart(5)}%  ${bar(mc.homeWin)}`);
console.log(`    ${"draw".padEnd(16)}      ${(mc.draw * 100).toFixed(1).padStart(5)}%  ${bar(mc.draw)}`);
console.log(`    ${b.padEnd(16)} win  ${(mc.awayWin * 100).toFixed(1).padStart(5)}%  ${bar(mc.awayWin)}`);
console.log(`    most likely:  ${mc.topScores[0]?.score} (${(mc.topScores[0]?.prob * 100).toFixed(1)}%)`);
console.log(`    95% CI goal diff: [${mc.confidence95_goalDiff[0]}, ${mc.confidence95_goalDiff[1]}]`);

console.log(`\n  Analytic Grid (Dixon-Coles, penaltyblog-style):`);
console.log(`    ${a.padEnd(16)} win  ${(analyticGrid.homeWin * 100).toFixed(1).padStart(5)}%`);
console.log(`    ${"draw".padEnd(16)}      ${(analyticGrid.draw * 100).toFixed(1).padStart(5)}%`);
console.log(`    ${b.padEnd(16)} win  ${(analyticGrid.awayWin * 100).toFixed(1).padStart(5)}%`);
console.log(`    most likely score: ${analyticGrid.mostLikelyScore}`);

console.log("");
