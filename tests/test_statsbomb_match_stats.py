from match_analyzer import MatchAnalyzer


def test_statsbomb_events_produce_match_stats_with_goal_and_shot_counts():
    events = [
        {"team": {"name": "Home"}, "type": {"name": "Shot"}, "shot": {"outcome": {"name": "Goal"}}},
        {"team": {"name": "Away"}, "type": {"name": "Shot"}, "shot": {"outcome": {"name": "Saved"}}},
    ]
    stats = MatchAnalyzer().statsbomb_match_stats("m1", "Home", "Away", events)
    assert (stats.home_goals, stats.away_goals) == (1, 0)
    assert (stats.home_shots, stats.away_shots) == (1, 1)
    assert stats.away_shots_on_target == 1
