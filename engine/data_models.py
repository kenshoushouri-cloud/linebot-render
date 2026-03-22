class Boat:
    def __init__(
        self,
        number,
        player_id,
        player_name,
        avg_st,
        win_rate,
        local_win_rate,
        course_stats,
        f_count,
        accident_rate,
        motor_score,
        comment,
        pair_stats
    ):
        self.number = number
        self.player_id = player_id
        self.player_name = player_name
        self.avg_st = avg_st
        self.win_rate = win_rate
        self.local_win_rate = local_win_rate
        self.course_stats = course_stats
        self.f_count = f_count
        self.accident_rate = accident_rate
        self.motor_score = motor_score
        self.comment = comment
        self.pair_stats = pair_stats


class Race:
    def __init__(
        self,
        place,
        number,
        boats,
        wind_dir,
        wind_power,
        water_condition,
        trend,
        is_4kado_attack
    ):
        self.place = place
        self.number = number
        self.boats = boats
        self.wind_dir = wind_dir
        self.wind_power = wind_power
        self.water_condition = water_condition
        self.trend = trend
        self.is_4kado_attack = is_4kado_attack
