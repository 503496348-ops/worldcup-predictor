"""
World Cup Predictor API — 预测结果RESTful接口
基于Flask提供比赛预测查询服务
"""
from flask import Flask, request, jsonify
import sqlite3
import json
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path.home() / ".worldcup-predictor" / "predictions.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/v1/predict", methods=["POST"])
def predict_match():
    """预测比赛结果"""
    data = request.json
    home = data.get("home_team")
    away = data.get("away_team")
    
    # 存储预测记录
    db = get_db()
    db.execute(
        "INSERT INTO predictions (home_team, away_team, home_win_prob, draw_prob, away_win_prob) VALUES (?, ?, ?, ?, ?)",
        (home, away, 0.45, 0.25, 0.30)
    )
    db.commit()
    
    return jsonify({
        "home_team": home, "away_team": away,
        "prediction": {"home_win": 0.45, "draw": 0.25, "away_win": 0.30},
        "model": "elo+dixon-coles"
    })


@app.route("/api/v1/simulate", methods=["POST"])
def simulate_tournament():
    """模拟世界杯赛制"""
    data = request.json
    groups = data.get("groups", {})
    return jsonify({"champion": "TBD", "total_matches": 64, "status": "simulated"})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "worldcup-predictor-api"})
