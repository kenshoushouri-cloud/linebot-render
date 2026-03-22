from engine.data_models import Boat, Race
from engine.predict_engine import predict, predict_all, format_summary

# ============================================
#  サンプルデータ（丸亀5R）
# ============================================

boat1 = Boat(
    1,101,"A選手",0.13,7.2,7.5,{1:85},0,0.2,78,"出足が良い",
    {102:{"together":12,"hit":7,"score":58}}
)
boat2 = Boat(
    2,102,"B選手",0.14,6.5,6.8,{2:60},0,0.3,72,"悪くない",
    {101:{"together":12,"hit":7,"score":58}}
)
boat3 = Boat(
    3,103,"C選手",0.16,5.8,5.9,{3:55},1,0.5,65,"普通",
    {}
)
boat4 = Boat(4,104,"D選手",0.15,6.0,6.2,{4:60},0,0.4,70,"悪くない",{})
boat5 = Boat(
    5,105,"E選手",0.15,5.5,5.7,{5:55},0,0.3,75,"伸びが良い",
    {101:{"together":5,"hit":3,"score":60}}
)
boat6 = Boat(6,106,"F選手",0.17,4.8,4.9,{6:40},0,0.6,60,"普通",{})

race = Race(
    "丸亀",5,
    [boat1,boat2,boat3,boat4,boat5,boat6],
    "向かい風",4,"普通","まくりデー",True
)

# ============================================
#  実行テスト
# ============================================

result = predict(race)
print("▼ レース単体予想")
print(result)

results, summary = predict_all([race])
print("\n▼ まとめ表示")
print(format_summary(summary))
