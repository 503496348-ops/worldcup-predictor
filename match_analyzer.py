"""
Match Analyzer — 比赛数据分析器
实时分析比赛统计数据
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MatchStats:
    """单场比赛统计"""
    match_id: str
    home_team: str
    away_team: str
    home_goals: int = 0
    away_goals: int = 0
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_possession: float = 0.5
    away_possession: float = 0.5
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    
    @property
    def total_goals(self) -> int:
        return self.home_goals + self.away_goals
    
    @property
    def is_draw(self) -> bool:
        return self.home_goals == self.away_goals
    
    @property
    def winner(self) -> Optional[str]:
        if self.home_goals > self.away_goals:
            return self.home_team
        elif self.away_goals > self.home_goals:
            return self.away_team
        return None


class MatchAnalyzer:
    """
    比赛分析器 — 从原始数据提取洞察
    
    分析维度:
    - 进攻效率: 射门→射正→进球转化率
    - 控球价值: 控球率与进球的相关性
    - 防守强度: 对手射门/射正限制
    - 定位球威胁: 角球/任意球得分率
    """
    
    def analyze_efficiency(self, stats: MatchStats) -> Dict:
        """进攻效率分析"""
        home_conv = (stats.home_goals / max(stats.home_shots_on_target, 1)) * 100
        away_conv = (stats.away_goals / max(stats.away_shots_on_target, 1)) * 100
        
        return {
            'home': {
                'shot_accuracy': (stats.home_shots_on_target / max(stats.home_shots, 1)) * 100,
                'conversion_rate': home_conv,
                'shots_per_goal': stats.home_shots / max(stats.home_goals, 1),
            },
            'away': {
                'shot_accuracy': (stats.away_shots_on_target / max(stats.away_shots, 1)) * 100,
                'conversion_rate': away_conv,
                'shots_per_goal': stats.away_shots / max(stats.away_goals, 1),
            }
        }
    
    def predict_xg(self, stats: MatchStats) -> Dict:
        """基于统计数据估算xG"""
        # 简化模型: 射正数 × 平均射正xG
        AVG_XG_PER_SOT = 0.32
        return {
            'home_xg': stats.home_shots_on_target * AVG_XG_PER_SOT,
            'away_xg': stats.away_shots_on_target * AVG_XG_PER_SOT,
        }

    def statsbomb_match_stats(
        self, match_id: str, home_team: str, away_team: str, events: List[Dict]
    ) -> MatchStats:
        """Aggregate StatsBomb Open Data shot events for tournament analysis."""
        stats = MatchStats(match_id=match_id, home_team=home_team, away_team=away_team)
        for event in events:
            if str((event.get("type") or {}).get("name") or "").lower() != "shot":
                continue
            team = str((event.get("team") or {}).get("name") or "")
            outcome = str(((event.get("shot") or {}).get("outcome") or {}).get("name") or "").lower()
            on_target = outcome in {"goal", "saved", "saved to post"}
            if team == home_team:
                stats.home_shots += 1
                stats.home_shots_on_target += int(on_target)
                stats.home_goals += int(outcome == "goal")
            elif team == away_team:
                stats.away_shots += 1
                stats.away_shots_on_target += int(on_target)
                stats.away_goals += int(outcome == "goal")
        return stats
