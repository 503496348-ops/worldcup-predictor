// Weighted Conformal Prediction — split-conformal for 3-class (H/D/A) football forecasts
// with exponential recency weighting.
// References: Stocker et al. (2025), Barber & Pananjady (2025), wc26-predict conformal_core.py
// Pure math — zero dependencies, deterministic.

// ── Config ─────────────────────────────────────────────────────────────────
const CONFORMAL_ALPHA = 0.1;                  // miscoverage → 90% nominal coverage
const RECENCY_HALFLIFE_DAYS = 30.0;           // exponential weight decay
const MIN_CALIBRATION_SIZE = 10;              // minimum records needed
const CLASSES = ['homeWin', 'draw', 'awayWin'];

// ── Nonconformity score: 1 − P(true class) ─────────────────────────────────
function nonconformityScore(probTrueClass) {
  return 1.0 - Math.max(0.0, Math.min(1.0, probTrueClass));
}

// ── Exponential recency weight ─────────────────────────────────────────────
function recencyWeight(predictionTime, calibrationTime, halflifeDays = RECENCY_HALFLIFE_DAYS) {
  const deltaDays = Math.max(0.0, (predictionTime - calibrationTime) / 86400.0);
  const lambda = Math.log(2) / Math.max(1e-9, halflifeDays);
  return Math.exp(-lambda * deltaDays);
}

// ── Weighted quantile ──────────────────────────────────────────────────────
function weightedQuantile(sortedScores, sortedWeights, q) {
  if (!sortedScores.length) return 1.0;
  const totalW = sortedWeights.reduce((s, w) => s + w, 0);
  if (totalW <= 0) return sortedScores[sortedScores.length - 1];

  let cumulative = 0.0;
  const target = q * totalW;
  for (let i = 0; i < sortedScores.length; i++) {
    cumulative += sortedWeights[i];
    if (cumulative >= target) return sortedScores[i];
  }
  return sortedScores[sortedScores.length - 1];
}

// ── Build calibration set from historical predictions ──────────────────────
// Each calibration record: { probs: [P(H), P(D), P(A)], outcome: 0|1|2, ts: unixSec }
function buildCalibrationSet(records, predictionTime) {
  return records.map(r => {
    const score = nonconformityScore(r.probs[r.outcome]);
    const weight = recencyWeight(predictionTime, r.ts);
    return { score, weight };
  }).sort((a, b) => a.score - b.score);
}

// ── Compute prediction set + adjusted probabilities ────────────────────────
export function conformalPredict(classProbs, calibrationRecords, predictionTime = Date.now() / 1000) {
  const n = calibrationRecords.length;

  // Not enough data — return all classes (uninformative)
  if (n < MIN_CALIBRATION_SIZE) {
    return {
      predictionSet: [0, 1, 2],
      adjustedProbs: [...classProbs],
      threshold: 1.0,
      coverage: 1.0 - CONFORMAL_ALPHA,
      setSize: 3,
      confidence: 'low',
    };
  }

  // Build sorted calibration set
  const cal = buildCalibrationSet(calibrationRecords, predictionTime);
  const sortedScores = cal.map(c => c.score);
  const sortedWeights = cal.map(c => c.weight);

  // Finite-sample correction: ⌈(n+1)(1−α)⌉ / n
  const qLevel = Math.min(1.0, Math.ceil((n + 1) * (1.0 - CONFORMAL_ALPHA)) / n);
  const threshold = weightedQuantile(sortedScores, sortedWeights, qLevel);

  // Build prediction set — classes whose nonconformity ≤ threshold
  const predictionSet = [];
  const adjustedProbs = [0.0, 0.0, 0.0];
  for (let idx = 0; idx < 3; idx++) {
    const score = nonconformityScore(classProbs[idx]);
    if (score <= threshold) {
      predictionSet.push(idx);
      adjustedProbs[idx] = classProbs[idx];
    }
  }

  // Renormalize adjusted probs within prediction set
  const total = adjustedProbs.reduce((s, p) => s + p, 0);
  if (total > 0) {
    for (let i = 0; i < 3; i++) adjustedProbs[i] /= total;
  }

  // Confidence label based on set size
  let confidence = 'high';
  if (predictionSet.length === 3) confidence = 'low';
  else if (predictionSet.length === 2) confidence = 'medium';

  return {
    predictionSet,
    adjustedProbs,
    threshold: +threshold.toFixed(4),
    coverage: 1.0 - CONFORMAL_ALPHA,
    setSize: predictionSet.length,
    confidence,
    calibrationSize: n,
  };
}

// ── Create a calibration record from a resolved prediction ─────────────────
export function createCalibrationRecord(probs, outcomeIndex, timestamp) {
  return {
    probs: Array.isArray(probs) ? probs : [probs.homeWin, probs.draw, probs.awayWin],
    outcome: outcomeIndex, // 0=H, 1=D, 2=A
    ts: timestamp || Date.now() / 1000,
    score: nonconformityScore(
      Array.isArray(probs) ? probs[outcomeIndex] : [probs.homeWin, probs.draw, probs.awayWin][outcomeIndex]
    ),
  };
}
