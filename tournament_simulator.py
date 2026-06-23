"""
Tournament Simulator — 世界杯赛制模拟器
模拟小组赛→淘汰赛全流程
"""
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


class Stage(Enum):
    GROUP = "group_stage"
    R16 = "round_of_16"
    QF = "quarter_finals"
    SF = "semi_finals"
    FINAL = "final"


@dataclass
class Team:
    name: str
    elo: int = 1500
    group: str = ""
    attack_strength: float = 1.0
    defense_strength: float = 1.0
    
    @property
    def overall(self) -> float:
        return (self.attack_strength + self.defense_strength) / 2


@dataclass
class GroupStanding:
    team: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    
    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws
    
    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against


@dataclass 
class MatchResult:
    home: str
    away: str
    home_goals: int
    away_goals: int
    stage: Stage = Stage.GROUP
    extra_time: bool = False
    penalties: Optional[Tuple[int, int]] = None


class TournamentSimulator:
    """
    世界杯赛制模拟器
    
    模拟流程:
    1. 小组赛 (每组4队, 单循环, 前2名出线)
    2. 1/8决赛 (16强, 单场淘汰)
    3. 1/4决赛 (8强)
    4. 半决赛
    5. 决赛/三四名决赛
    
    预测模型: 基于Elo评分的Poisson分布模拟
    """
    
    HOME_ADVANTAGE = 75  # 主场优势Elo分（世界杯中性场地减半）
    NEUTRAL_MODIFIER = 0.5
    
    def __init__(self, teams: List[Team], seed: int = 42):
        self.teams = {t.name: t for t in teams}
        self.rng = random.Random(seed)
        self.results: List[MatchResult] = []
    
    def expected_goals(self, home: Team, away: Team) -> Tuple[float, float]:
        """基于Elo差计算预期进球"""
        elo_diff = home.elo - away.elo
        neutral = self.NEUTRAL_MODIFIER
        
        # Poisson参数
        base_lambda = 1.35  # 历届世界杯场均进球
        home_adv = self.HOME_ADVANTAGE * neutral
        
        lambda_home = base_lambda * (1 + (elo_diff + home_adv) / 2000)
        lambda_away = base_lambda * (1 - (elo_diff + home_adv) / 2000)
        
        # 应用攻防强度
        lambda_home *= home.attack_strength * (2 - away.defense_strength)
        lambda_away *= away.attack_strength * (2 - home.defense_strength)
        
        return (max(0.2, lambda_home), max(0.2, lambda_away))
    
    def simulate_match(self, home: Team, away: Team, stage: Stage = Stage.GROUP) -> MatchResult:
        """模拟单场比赛"""
        lambda_h, lambda_a = self.expected_goals(home, away)
        
        home_goals = self.rng.poisson(lambda_h) if hasattr(self.rng, 'poisson') else int(self.rng.expovariate(1/max(lambda_h, 0.1)))
        away_goals = self.rng.poisson(lambda_a) if hasattr(self.rng, 'poisson') else int(self.rng.expovariate(1/max(lambda_a, 0.1)))
        
        extra_time = False
        penalties = None
        
        # 淘汰赛需要分出胜负
        if stage != Stage.GROUP and home_goals == away_goals:
            extra_time = True
            # 加时赛期望进球减半
            et_home = self.rng.expovariate(1/max(lambda_h * 0.5, 0.1))
            et_away = self.rng.expovariate(1/max(lambda_a * 0.5, 0.1))
            home_goals += int(et_home)
            away_goals += int(et_away)
            
            if home_goals == away_goals:
                # 点球大战
                ph, pa = 0, 0
                for i in range(10):
                    if self.rng.random() < 0.75:
                        if i % 2 == 0:
                            ph += 1
                        else:
                            pa += 1
                    if i >= 6 and ph != pa:
                        break
                penalties = (ph, pa)
        
        result = MatchResult(
            home=home.name, away=away.name,
            home_goals=home_goals, away_goals=away_goals,
            stage=stage, extra_time=extra_time, penalties=penalties
        )
        self.results.append(result)
        return result
    
    def simulate_group(self, teams: List[Team]) -> List[GroupStanding]:
        """模拟小组赛"""
        standings = {t.name: GroupStanding(team=t.name) for t in teams}
        
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                result = self.simulate_match(teams[i], teams[j], Stage.GROUP)
                h, a = standings[result.home], standings[result.away]
                
                h.played += 1
                a.played += 1
                h.goals_for += result.home_goals
                h.goals_against += result.away_goals
                a.goals_for += result.away_goals
                a.goals_against += result.home_goals
                
                if result.home_goals > result.away_goals:
                    h.wins += 1
                    a.losses += 1
                elif result.home_goals < result.away_goals:
                    a.wins += 1
                    h.losses += 1
                else:
                    h.draws += 1
                    a.draws += 1
        
        return sorted(standings.values(), key=lambda s: (-s.points, -s.goal_difference, -s.goals_for))
    
    def simulate_knockout(self, teams: List[Team]) -> Team:
        """模拟淘汰赛阶段"""
        round_teams = teams[:]
        stage_map = {16: Stage.R16, 8: Stage.QF, 4: Stage.SF, 2: Stage.FINAL}
        
        while len(round_teams) > 1:
            stage = stage_map.get(len(round_teams), Stage.R16)
            winners = []
            for i in range(0, len(round_teams), 2):
                result = self.simulate_match(round_teams[i], round_teams[i+1], stage)
                if result.penalties:
                    winner = result.home if result.penalties[0] > result.penalties[1] else result.away
                else:
                    winner = result.home if result.home_goals > result.away_goals else result.away
                winners.append(self.teams[winner])
            round_teams = winners
        
        return round_teams[0]
    
    def simulate_tournament(self, groups: Dict[str, List[Team]]) -> Dict:
        """模拟完整世界杯"""
        qualified = []
        group_results = {}
        
        for group_name, teams in groups.items():
            standings = self.simulate_group(teams)
            group_results[group_name] = standings
            qualified.extend([self.teams[s.team] for s in standings[:2]])
        
        # 随机配对淘汰赛（实际赛制有固定对阵表）
        self.rng.shuffle(qualified)
        champion = self.simulate_knockout(qualified)
        
        return {
            'champion': champion.name,
            'groups': group_results,
            'total_matches': len(self.results),
        }
