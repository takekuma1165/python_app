import random

def omikuji():
    results = ["大吉", "中吉", "小吉", "吉", "末吉", "凶"]
    weights = [2, 1, 1, 1, 1, 0.5]  # 大吉の確率を 4 倍、凶の確率を 1/3 に調整
    result = random.choices(results, weights=weights, k=1)[0]
    print("あなたの運勢は・・・")
    print(result)

def forecast_weather():
    weathers = ["晴れ", "曇り", "雨", "雪", "雷", "霧"]
    forecast = random.choice(weathers)
    print("明日の天気予報は・・・")
    print(forecast)
    return forecast

# 実行
omikuji()
forecast_weather()