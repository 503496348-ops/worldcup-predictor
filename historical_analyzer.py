"""
Historical Data Analyzer — 世界杯历史数据分析
历届世界杯数据统计与趋势分析
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


@dataclass
class TournamentResult:
    """单届世界杯结果"""
    year: int
    host: str
    champion: str
    runner_up: str
    third: str
    fourth: str
    total_goals: int = 0
    total_matches: int = 0
    avg_goals_per_match: float = 0.0
    
    def __post_init__(self):
        if self.total_matches > 0 and self.avg_goals_per_match == 0:
            self.avg_goals_per_match = self.total_goals / self.total_matches


# 历届世界杯数据 (1930-2022)
WORLD_CUP_HISTORY = [
    TournamentResult(1930, "Uruguay", "Uruguay", "Argentina", "USA", "Yugoslavia", 70, 18, 3.89),
    TournamentResult(1934, "Italy", "Italy", "Czechoslovakia", "Germany", "Austria", 70, 17, 4.12),
    TournamentResult(1938, "France", "Italy", "Hungary", "Brazil", "Sweden", 84, 18, 4.67),
    TournamentResult(1950, "Brazil", "Uruguay", "Brazil", "Sweden", "Spain", 88, 22, 4.00),
    TournamentResult(1954, "Switzerland", "Germany", "Hungary", "Austria", "Uruguay", 140, 26, 5.38),
    TournamentResult(1958, "Sweden", "Brazil", "Sweden", "France", "Germany", 126, 35, 3.60),
    TournamentResult(1962, "Chile", "Brazil", "Czechoslovakia", "Chile", "Yugoslavia", 89, 32, 2.78),
    TournamentResult(1966, "England", "England", "Germany", "Portugal", "Soviet Union", 89, 32, 2.78),
    TournamentResult(1970, "Mexico", "Brazil", "Italy", "Germany", "Uruguay", 95, 32, 2.97),
    TournamentResult(1974, "Germany", "Germany", "Netherlands", "Poland", "Brazil", 97, 38, 2.55),
    TournamentResult(1978, "Argentina", "Argentina", "Netherlands", "Brazil", "Italy", 102, 38, 2.68),
    TournamentResult(1982, "Spain", "Italy", "Germany", "Poland", "France", 146, 52, 2.81),
    TournamentResult(1986, "Mexico", "Argentina", "Germany", "France", "Belgium", 132, 52, 2.54),
    TournamentResult(1990, "Italy", "Germany", "Argentina", "Italy", "England", 115, 52, 2.21),
    TournamentResult(1994, "USA", "Brazil", "Italy", "Sweden", "Bulgaria", 141, 52, 2.71),
    TournamentResult(1998, "France", "France", "Brazil", "Croatia", "Netherlands", 171, 64, 2.67),
    TournamentResult(2002, "S.Korea/Japan", "Brazil", "Germany", "Turkey", "S.Korea", 161, 64, 2.52),
    TournamentResult(2006, "Germany", "Italy", "France", "Germany", "Portugal", 147, 64, 2.30),
    TournamentResult(2010, "South Africa", "Spain", "Netherlands", "Germany", "Uruguay", 145, 64, 2.27),
    TournamentResult(2014, "Brazil", "Germany", "Argentina", "Netherlands", "Brazil", 171, 64, 2.67),
    TournamentResult(2018, "Russia", "France", "Croatia", "Belgium", "England", 169, 64, 2.64),
    TournamentResult(2022, "Qatar", "Argentina", "France", "Croatia", "Morocco", 172, 64, 2.69),
]


@dataclass
class TeamHistory:
    """球队历史表现"""
    team: str
    titles: int = 0
    finals: int = 0
    semi_finals: int = 0
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    tournaments_played: int = 0
    
    @property
    def win_rate(self) -> float:
        return self.wins / max(self.total_matches, 1)
    
    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
    
    @property
    def points_per_match(self) -> float:
        return (self.wins * 3 + self.draws) / max(self.total_matches, 1)


class HistoricalAnalyzer:
    """
    历史数据分析器 — 从历届世界杯提取规律
    
    分析维度:
    - 冠军规律: 哪些因素最能预测冠军
    - 进球趋势: 历届世界杯场均进球变化
    - 主场优势: 东道主平均表现
    - 大洲轮换: 不同大洲夺冠分布
    """
    
    def __init__(self, history: List[TournamentResult] = None):
        self.history = history or WORLD_CUP_HISTORY
    
    def get_champion_frequency(self) -> Dict[str, int]:
        """冠军频率统计"""
        freq = defaultdict(int)
        for t in self.history:
            freq[t.champion] += 1
        return dict(sorted(freq.items(), key=lambda x: -x[1]))
    
    def get_goals_trend(self) -> List[Tuple[int, float]]:
        """进球趋势 (年份, 场均进球)"""
        return [(t.year, t.avg_goals_per_match) for t in self.history]
    
    def get_host_performance(self) -> List[Tuple[str, str, int]]:
        """东道主表现 (年份, 东道主, 最终名次)"""
        results = []
        for t in self.history:
            if t.champion == t.host:
                results.append((t.year, t.host, 1))
            elif t.runner_up == t.host:
                results.append((t.year, t.host, 2))
            elif t.third == t.host:
                results.append((t.year, t.host, 3))
            elif t.fourth == t.host:
                results.append((t.year, t.host, 4))
            else:
                results.append((t.year, t.host, 5))
        return results
    
    def get_continent_dominance(self) -> Dict[str, Dict[str, int]]:
        """大洲夺冠分布"""
        continent_map = {
            "Brazil": "SA", "Argentina": "SA", "Uruguay": "SA",
            "Germany": "EU", "Italy": "EU", "France": "EU", "Spain": "EU",
            "England": "EU", "Netherlands": "EU",
        }
        dominance = defaultdict(lambda: {"titles": 0, "finals": 0})
        for t in self.history:
            champ_cont = continent_map.get(t.champion, "Other")
            dominance[champ_cont]["titles"] += 1
            runner_cont = continent_map.get(t.runner_up, "Other")
            dominance[runner_cont]["finals"] += 1
        return dict(dominance)
    
    def predict_2026_favorites(self) -> List[Tuple[str, float]]:
        """基于历史数据预测2026热门"""
        freq = self.get_champion_frequency()
        favorites = []
        for team, titles in freq.items():
            score = titles * 0.4 + (1 if titles >= 2 else 0) * 0.3
            favorites.append((team, score))
        
        # 加入近年强队
        recent_strong = ["France", "Argentina", "England", "Spain", "Brazil"]
        for team in recent_strong:
            if team not in [f[0] for f in favorites]:
                favorites.append((team, 0.5))
        
        return sorted(favorites, key=lambda x: -x[1])[:10]
