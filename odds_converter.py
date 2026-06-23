"""
Odds Converter — 赔率格式转换与隐含概率计算
支持欧赔/英赔/美赔/亚盘互转
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Odds:
    """赔率数据"""
    home: float
    draw: float
    away: float
    
    @property
    def implied_prob(self) -> Tuple[float, float, float]:
        """隐含概率（含overround）"""
        total = 1/self.home + 1/self.draw + 1/self.away
        return (1/self.home/total, 1/self.draw/total, 1/self.away/total)
    
    @property
    def overround(self) -> float:
        """庄家利润率"""
        return 1/self.home + 1/self.draw + 1/self.away - 1
    
    @property
    def fair_odds(self) -> Tuple[float, float, float]:
        """公平赔率（去除overround）"""
        p_home, p_draw, p_away = self.implied_prob
        return (1/p_home, 1/p_draw, 1/p_away)


class OddsConverter:
    """
    赔率转换器 — 多格式互转
    
    支持格式:
    - 欧洲盘 (Decimal): 2.50
    - 英国盘 (Fractional): 3/2
    - 美国盘 (Moneyline): +150 / -200
    - 隐含概率: 40%
    """
    
    @staticmethod
    def decimal_to_implied(decimal_odds: float) -> float:
        """欧赔→隐含概率"""
        return 1 / decimal_odds
    
    @staticmethod
    def implied_to_decimal(prob: float) -> float:
        """隐含概率→欧赔"""
        return 1 / prob if prob > 0 else float('inf')
    
    @staticmethod
    def decimal_to_fractional(decimal: float) -> str:
        """欧赔→英赔"""
        numerator = decimal - 1
        # 简化分数
        from math import gcd
        n = int(numerator * 100)
        d = 100
        g = gcd(n, d)
        return f"{n//g}/{d//g}"
    
    @staticmethod
    def decimal_to_american(decimal: float) -> int:
        """欧赔→美赔"""
        if decimal >= 2.0:
            return int((decimal - 1) * 100)
        else:
            return int(-100 / (decimal - 1))
    
    @staticmethod
    def american_to_decimal(american: int) -> float:
        """美赔→欧赔"""
        if american > 0:
            return 1 + american / 100
        else:
            return 1 + 100 / abs(american)
    
    @staticmethod
    def kelly_criterion(prob: float, odds: float) -> float:
        """凯利公式计算最优投注比例"""
        b = odds - 1  # 净赔率
        q = 1 - prob
        return max(0, (b * prob - q) / b)
