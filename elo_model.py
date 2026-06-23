"""
Team Strength Model — 球队实力评估模型
基于Elo评分系统 + FIFA排名加权
"""
from dataclasses import dataclass
from typing import Dict, Optional
import math


@dataclass
class TeamStrength:
    """球队综合实力评估"""
    team_id: str
    elo: int = 1500
    fifa_rank: int = 50
    attack_rating: float = 1.0
    defense_rating: float = 1.0
    form_rating: float = 0.5  # 近期状态 (0-1)
    
    @property
    def overall(self) -> float:
        """综合评分"""
        elo_norm = (self.elo - 1000) / 1000  # 归一化到0-1
        rank_norm = 1.0 - (self.fifa_rank / 200)
        return (elo_norm * 0.4 + rank_norm * 0.2 + 
                self.attack_rating * 0.15 + self.defense_rating * 0.15 + 
                self.form_rating * 0.1)


class EloSystem:
    """
    Elo评分系统 — 国际足球专用
    
    参数:
    - K=60: 国际比赛系数（FIFA标准）
    - 主场优势: +75分（中性场地减半）
    - 进球差修正: 最大+3分
    """
    
    K = 60
    HOME_ADVANTAGE = 75
    
    def expected_score(self, elo_a: int, elo_b: int) -> float:
        """A队的期望得分"""
        diff = (elo_b - elo_a) / 400
        return 1.0 / (1.0 + math.pow(10, diff))
    
    def update(self, elo_a: int, elo_b: int, score_a: float, 
               goal_diff: int = 0, is_neutral: bool = False) -> tuple:
        """
        更新Elo评分
        score_a: 1=胜, 0.5=平, 0=负
        goal_diff: 进球差（绝对值）
        """
        if not is_neutral:
            elo_a += self.HOME_ADVANTAGE
        
        expected = self.expected_score(elo_a, elo_b)
        
        # 进球差修正 (GD=1: ×1, GD=2: ×1.5, GD=3+: ×(11+GD)/8)
        if goal_diff <= 1:
            gd_mult = 1.0
        elif goal_diff == 2:
            gd_mult = 1.5
        else:
            gd_mult = (11 + goal_diff) / 8
        
        delta = self.K * gd_mult * (score_a - expected)
        
        new_elo_a = elo_a + delta
        new_elo_b = elo_b - delta
        
        return (round(new_elo_a), round(new_elo_b))


# FIFA排名数据（Top 30, 2026年6月）
FIFA_RANKINGS = {
    'argentina': 1, 'france': 2, 'spain': 3, 'england': 4, 'brazil': 5,
    'germany': 6, 'portugal': 7, 'netherlands': 8, 'belgium': 9, 'italy': 10,
    'croatia': 11, 'uruguay': 12, 'japan': 13, 'colombia': 14, 'usa': 15,
    'mexico': 16, 'morocco': 17, 'switzerland': 18, 'denmark': 19, 'south-korea': 20,
    'australia': 21, 'iran': 22, 'senegal': 23, 'ukraine': 24, 'poland': 25,
    'wales': 26, 'serbia': 27, 'chile': 28, 'tunisia': 29, 'peru': 30,
}
