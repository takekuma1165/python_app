#!/usr/bin/env python3
from datetime import datetime

def ask_num(prompt, cast=float, default=None):
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            return default
        try:
            return cast(s)
        except ValueError:
            print("数値で入力してください。")

def ask_yesno(prompt):
    fullwidth_map = str.maketrans({'ｙ':'y','ｎ':'n','Ｙ':'y','Ｎ':'n','Ｙ':'y','Ｙ':'y'})
    while True:
        s = input(prompt + " (y/n): ").strip()
        s_norm = s.translate(fullwidth_map).lower()
        if s_norm in ("y", "yes", "はい", "ya", "y\n"):
            return True
        if s_norm in ("n", "no", "いいえ", "iie", "n\n"):
            return False
        # 日本語の「はい/いいえ」を直接判定（全角スペース等を除去）
        if s_norm.replace(" ", "") in ("はい", "いいえ"):
            return s_norm.replace(" ", "") == "はい"
        print("y または n で答えてください。（例: y / n / はい / いいえ）")

def score_sleep(h, latency, awakenings, daytime_sleepiness, caffeine, screen_minutes, exercise_per_week):
    score = 0
    # 睡眠時間: 推奨 7-9h
    if h < 6:
        score += 3
    elif h < 7:
        score += 1
    elif h > 9:
        score += 1

    # 入眠時間
    if latency > 30:
        score += 2
    elif latency > 15:
        score += 1

    # 夜間覚醒
    if awakenings >= 3:
        score += 3
    elif awakenings >= 1:
        score += 1

    # 日中の眠気 (1-5) 高いほど悪化
    score += max(0, int(daytime_sleepiness) - 1)

    # カフェイン
    if caffeine:
        score += 2

    # 就寝前の画面時間
    if screen_minutes > 60:
        score += 2
    elif screen_minutes > 30:
        score += 1

    # 運動頻度
    if exercise_per_week >= 3:
        score -= 1
    elif exercise_per_week == 0:
        score += 1

    return max(score, 0)

def recommendations(score):
    tips = []
    if score <= 3:
        category = "良好"
        tips.append("現在の睡眠は概ね良好です。規則正しい生活を続けましょう。")
    elif score <= 7:
        category = "注意"
        tips.append("いくつか改善点があります。就寝ルーティンの見直しを検討してください。")
    else:
        category = "要改善"
        tips.append("睡眠の質が低下しています。以下の改善策を試し、必要なら専門医に相談してください。")

    tips += [
        "毎日ほぼ同じ時刻に就寝・起床する",
        "就寝90分前から強い光（画面含む）を避ける",
        "カフェインは午後は控える（可能なら昼以降は摂らない）",
        "寝る前の激しい運動は避けるが、日中の適度な運動は促進する",
        "寝室は暗く静かに、温度は快適に保つ"
    ]

    return category, tips

def main():
    print("=== 簡易 睡眠改善診断 ===")
    print("質問に答えてスコア化します。入力をスキップする場合は Enter を押してください（デフォルトは推定値）。\n")

    h = ask_num("平均睡眠時間（時間）: ", float, default=7.5)
    latency = ask_num("寝つきまでの時間（分）: ", int, default=15)
    awakenings = ask_num("夜中に目が覚める回数（平均）: ", int, default=0)
    daytime = ask_num("日中の眠気（1=なし,5=強い）: ", int, default=1)
    caffeine = ask_yesno("夕方以降にカフェインを摂りますか？")
    screen = ask_num("就寝1時間前の画面使用時間（分）: ", int, default=10)
    exercise = ask_num("週あたりの運動回数: ", int, default=2)

    s = score_sleep(h, latency, awakenings, daytime, caffeine, screen, exercise)
    cat, tips = recommendations(s)

    print("\n--- 診断結果 ---")
    print(f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"スコア: {s} ({cat})")
    print("\nアドバイス:")
    for t in tips:
        print("- ", t)

    if ask_yesno("診断結果をファイルに保存しますか？"):
        fname = f"sleep_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("簡易 睡眠改善診断\n")
            f.write(f"日時: {datetime.now().isoformat()}\n")
            f.write(f"スコア: {s} ({cat})\n\n")
            f.write("アドバイス:\n")
            for t in tips:
                f.write("- " + t + "\n")
        print(f"保存しました: {fname}")

if __name__ == '__main__':
    main()
