"""
Player Model — 球员数据模型与评估
基于世界杯表现的球员价值评估
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Position(Enum):
    GK = "goalkeeper"
    CB = "center_back"
    LB = "left_back"
    RB = "right_back"
    CDM = "defensive_midfielder"
    CM = "central_midfielder"
    CAM = "attacking_midfielder"
    LW = "left_winger"
    RW = "right_winger"
    ST = "striker"
    CF = "center_forward"


@dataclass
class PlayerStats:
    """球员世界杯统计数据"""
    player_id: str
    name: str
    team: str
    position: Position
    minutes_played: int = 0
    goals: int = 0
    assists: int = 0
    shots: int = 0
    shots_on_target: int = 0
    passes_completed: int = 0
    passes_attempted: int = 0
    tackles: int = 0
    interceptions: int = 0
    clearances: int = 0
    saves: int = 0  # GK only
    yellow_cards: int = 0
    red_cards: int = 0
    motm_awards: int = 0  # Man of the Match
    
    @property
    def pass_accuracy(self) -> float:
        return self.passes_completed / max(self.passes_attempted, 1)
    
    @property
    def shot_accuracy(self) -> float:
        return self.shots_on_target / max(self.shots, 1)
    
    @property
    def goal_contributions(self) -> int:
        return self.goals + self.assists
    
    @property
    def minutes_per_goal(self) -> float:
        return self.minutes_played / max(self.goals, 1)


class PlayerEvaluator:
    """
    球员评估器 — 基于位置的多维度评分
    
    评估维度（按位置加权）:
    - 进攻: 进球/助攻/射门（前锋权重高）
    - 组织: 传球/关键传球/控球（中场权重高）
    - 防守: 铲断/拦截/解围（后卫权重高）
    - 门将: 扑救/零封/出击（门将专用）
    - 影响力: MOTM/出场时间/纪律
    """
    
    POSITION_WEIGHTS = {
        Position.ST: {"attack": 0.5, "organization": 0.15, "defense": 0.05, "influence": 0.3},
        Position.CF: {"attack": 0.45, "organization": 0.2, "defense": 0.05, "influence": 0.3},
        Position.LW: {"attack": 0.4, "organization": 0.25, "defense": 0.1, "influence": 0.25},
        Position.RW: {"attack": 0.4, "organization": 0.25, "defense": 0.1, "influence": 0.25},
        Position.CAM: {"attack": 0.3, "organization": 0.4, "defense": 0.05, "influence": 0.25},
        Position.CM: {"attack": 0.2, "organization": 0.35, "defense": 0.2, "influence": 0.25},
        Position.CDM: {"attack": 0.05, "organization": 0.3, "defense": 0.4, "influence": 0.25},
        Position.CB: {"attack": 0.05, "organization": 0.15, "defense": 0.5, "influence": 0.3},
        Position.LB: {"attack": 0.1, "organization": 0.2, "defense": 0.4, "influence": 0.3},
        Position.RB: {"attack": 0.1, "organization": 0.2, "defense": 0.4, "influence": 0.3},
        Position.GK: {"attack": 0.0, "organization": 0.1, "defense": 0.6, "influence": 0.3},
    }
    
    def evaluate(self, player: PlayerStats) -> Dict:
        """综合评估球员"""
        weights = self.POSITION_WEIGHTS.get(player.position, self.POSITION_WEIGHTS[Position.CM])
        
        attack = self._score_attack(player)
        org = self._score_organization(player)
        defense = self._score_defense(player)
        influence = self._score_influence(player)
        
        total = (attack * weights["attack"] + org * weights["organization"] +
                defense * weights["defense"] + influence * weights["influence"])
        
        return {
            "player": player.name,
            "position": player.position.value,
            "overall": round(total, 2),
            "attack": round(attack, 2),
            "organization": round(org, 2),
            "defense": round(defense, 2),
            "influence": round(influence, 2),
        }
    
    def _score_attack(self, p: PlayerStats) -> float:
        if p.minutes_played == 0: return 0
        goals_90 = p.goals * 90 / p.minutes_played
        assists_90 = p.assists * 90 / p.minutes_played
        return min(10, goals_90 * 4 + assists_90 * 2 + p.shot_accuracy * 3)
    
    def _score_organization(self, p: PlayerStats) -> float:
        return min(10, p.pass_accuracy * 8 + (p.passes_completed / max(p.minutes_played, 1)) * 10)
    
    def _score_defense(self, p: PlayerStats) -> float:
        if p.minutes_played == 0: return 0
        tackles_90 = p.tackles * 90 / p.minutes_played
        ints_90 = p.interceptions * 90 / p.minutes_played
        return min(10, tackles_90 * 2 + ints_90 * 2 + p.clearances * 0.1)
    
    def _score_influence(self, p: PlayerStats) -> float:
        mins_score = min(5, p.minutes_played / 540)  # 6场=满分
        motm_score = min(3, p.motm_awards * 1.5)
        discipline = max(0, 2 - p.yellow_cards * 0.3 - p.red_cards * 1)
        return mins_score + motm_score + discipline
