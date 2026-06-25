#!/usr/bin/env python3
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None


# 入力プロンプトを表示し、数値として解釈して返す関数です。
# 空入力時はデフォルト値を返し、不正な値なら再入力を促します。
def ask_num(prompt, cast=float, default=None):
    while True:
        s = input(prompt).strip()
        if s == "" and default is not None:
            return default
        try:
            return cast(s)
        except ValueError:
            print("数値で入力してください。")

# y/n 形式の入力を受け取り、True/False に変換して返します。
# 全角文字や日本語の「はい/いいえ」にも対応します。
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

# 睡眠関連の各指標から診断スコアを算出する関数です。
# 入力値に応じて加点・減点を行い、最終的なスコアを返します。
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

# スコアに応じた診断カテゴリと改善アドバイスを生成します。
# スコアが高いほど睡眠改善の必要性が高いと判定します。
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


# 診断結果を画面表示用のテキストに整形します。
# 日時やスコア、アドバイスを改行付きでまとめた文字列を返します。
def format_results(score, category, tips):
    lines = [
        f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"スコア: {score} ({category})",
        "",
        "アドバイス:"
    ]
    lines += ["- " + tip for tip in tips]
    return "\n".join(lines)


# 診断結果をテキストファイルとして保存します。
# 保存先ファイル名を生成し、アドバイス付きのレポートを書き出します。
def save_report(score, category, tips):
    fname = f"sleep_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("簡易 睡眠改善診断\n")
        f.write(f"日時: {datetime.now().isoformat()}\n")
        f.write(f"スコア: {score} ({category})\n\n")
        f.write("アドバイス:\n")
        for tip in tips:
            f.write("- " + tip + "\n")
    return fname


# tkinter GUI を構築し、入力検証と診断表示の画面操作を制御します。
# GUI が利用できない場合はコンソール実行に切り替えます。
def run_gui():
    if tk is None:
        print("tkinter が利用できないため、コンソール実行にフォールバックします。")
        return main_console()

    root = tk.Tk()
    root.title("簡易 睡眠改善診断")
    root.geometry("600x520")
    root.resizable(False, False)

    entries = {}
    normal_labels = {}
    values = {}

    def mark_widget_valid(widget, valid):
        widget.configure(bg="white" if valid else "#ffcccc")

    # すべての正常値表示ラベルをクリアします。
    def clear_field_labels():
        for label in normal_labels.values():
            label.config(text="")

    # 入力元から文字列を取得し、数値検証で使用します。
    # 入力元から文字列を取得し、数値検証で使用します。
    def get_widget_text(source):
        if isinstance(source, tk.StringVar):
            return source.get()
        if hasattr(source, 'get'):
            return source.get()
        return ''

    # 浮動小数点入力の検証を行います。範囲外や不正な入力時は False を返します。
    def validate_float(source, widget, min_val=None, max_val=None):
        try:
            value = float(get_widget_text(source))
        except ValueError:
            mark_widget_valid(widget, False)
            return None, False
        valid = True
        if min_val is not None and value < min_val:
            valid = False
        if max_val is not None and value > max_val:
            valid = False
        mark_widget_valid(widget, valid)
        return value, valid

    # 整数入力の妥当性を検証し、範囲外や不正値の場合は False を返します。
    def validate_int(source, widget, min_val=None, max_val=None):
        try:
            value = int(get_widget_text(source))
        except ValueError:
            mark_widget_valid(widget, False)
            return None, False
        valid = True
        if min_val is not None and value < min_val:
            valid = False
        if max_val is not None and value > max_val:
            valid = False
        mark_widget_valid(widget, valid)
        return value, valid

    # ラベルと入力欄、正常値表示欄を横並びで配置する補助関数です。
    def add_row(label_text, default, row, width=12):
        label = tk.Label(root, text=label_text)
        label.grid(row=row, column=0, sticky="w", padx=10, pady=6)
        entry = tk.Entry(root, width=width)
        entry.insert(0, str(default))
        entry.grid(row=row, column=1, sticky="w", padx=10)
        normal_label = tk.Label(root, text="", fg="#555555")
        normal_label.grid(row=row, column=2, sticky="w", padx=(0, 0))
        return entry, normal_label

    entries['h'], normal_labels['h'] = add_row("平均睡眠時間（時間）:", 7.5, 0)
    entries['latency'], normal_labels['latency'] = add_row("寝つきまでの時間（分）:", 15, 1)

    awakenings_var = tk.StringVar(value="0")
    awakenings_label = tk.Label(root, text="夜中に目が覚める回数（平均）:")
    awakenings_label.grid(row=2, column=0, sticky="w", padx=10, pady=6)
    awakenings_menu = tk.OptionMenu(root, awakenings_var, *[str(i) for i in range(0, 11)])
    awakenings_menu.config(width=10)
    awakenings_menu.grid(row=2, column=1, sticky="w", padx=10)
    normal_labels['awakenings'] = tk.Label(root, text="", fg="#555555")
    normal_labels['awakenings'].grid(row=2, column=2, sticky="w", padx=(0, 0))
    entries['awakenings'] = awakenings_menu
    values['awakenings'] = awakenings_var

    daytime_var = tk.StringVar(value="1")
    daytime_label = tk.Label(root, text="日中の眠気（1=なし,5=強い）:")
    daytime_label.grid(row=3, column=0, sticky="w", padx=10, pady=6)
    daytime_menu = tk.OptionMenu(root, daytime_var, *[str(i) for i in range(1, 6)])
    daytime_menu.config(width=10)
    daytime_menu.grid(row=3, column=1, sticky="w", padx=10)
    normal_labels['daytime'] = tk.Label(root, text="", fg="#555555")
    normal_labels['daytime'].grid(row=3, column=2, sticky="w", padx=(0, 0))
    entries['daytime'] = daytime_menu
    values['daytime'] = daytime_var

    caffeine_var = tk.BooleanVar(value=False)
    caffeine_check = tk.Checkbutton(root, text="夕方以降にカフェインを摂りますか？", variable=caffeine_var)
    caffeine_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=6)
    entries['screen'], normal_labels['screen'] = add_row("就寝1時間前の画面使用時間（分）:", 10, 5)

    exercise_var = tk.StringVar(value="2")
    exercise_label = tk.Label(root, text="週あたりの運動回数:")
    exercise_label.grid(row=6, column=0, sticky="w", padx=10, pady=6)
    exercise_menu = tk.OptionMenu(root, exercise_var, *[str(i) for i in range(0, 8)])
    exercise_menu.config(width=10)
    exercise_menu.grid(row=6, column=1, sticky="w", padx=10)
    normal_labels['exercise'] = tk.Label(root, text="", fg="#555555")
    normal_labels['exercise'].grid(row=6, column=2, sticky="w", padx=(0, 0))
    entries['exercise'] = exercise_menu
    values['exercise'] = exercise_var

    result_text = tk.Text(root, width=60, height=14, wrap="word", state="disabled")
    result_text.grid(row=8, column=0, columnspan=2, padx=10, pady=(8, 0))

    error_label = tk.Label(root, text="", fg="red", anchor="w")
    error_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))

    last_result = {'score': None, 'category': None, 'tips': None}

    # 画面項目の値をチェックし、診断結果を算出して表示します。
    # 未入力や不正値は赤背景で示し、エラー文を表示します。
    def compute_result():
        clear_field_labels()
        error_label.config(text="")

        normal_labels['h'].config(text="正常値: 5.5〜9.5")
        normal_labels['latency'].config(text="正常値: 0〜60")
        normal_labels['awakenings'].config(text="正常値: 0〜2")
        normal_labels['daytime'].config(text="正常値: 1〜3")
        normal_labels['screen'].config(text="正常値: 0〜60")
        normal_labels['exercise'].config(text="正常値: 0〜3")

        valid = True
        h, ok = validate_float(entries['h'], entries['h'], min_val=5.5, max_val=9.5)
        valid &= ok
        latency, ok = validate_int(entries['latency'], entries['latency'], min_val=0, max_val=60)
        valid &= ok
        awakenings, ok = validate_int(values['awakenings'], entries['awakenings'], min_val=0, max_val=2)
        valid &= ok
        daytime, ok = validate_int(values['daytime'], entries['daytime'], min_val=1, max_val=3)
        valid &= ok
        screen, ok = validate_int(entries['screen'], entries['screen'], min_val=0, max_val=60)
        valid &= ok
        exercise, ok = validate_int(values['exercise'], entries['exercise'], min_val=0, max_val=3)
        valid &= ok

        if h is None or latency is None or awakenings is None or daytime is None or screen is None or exercise is None:
            error_label.config(text="未入力または数値として無効な項目があります。赤い入力欄を修正してください。")
            return

        score = score_sleep(h, latency, awakenings, daytime, caffeine_var.get(), screen, exercise)
        category, tips = recommendations(score)
        last_result['score'] = score
        last_result['category'] = category
        last_result['tips'] = tips

        output = format_results(score, category, tips)
        result_text.configure(state="normal")
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, output)
        result_text.configure(state="disabled")
        error_label.config(text="")

    def save_result():
        if last_result['score'] is None:
            messagebox.showinfo("保存できません", "まず「診断する」で結果を表示してください。")
            return
        fname = save_report(last_result['score'], last_result['category'], last_result['tips'])
        messagebox.showinfo("保存完了", f"診断結果を保存しました: {fname}")

    button_frame = tk.Frame(root)
    button_frame.grid(row=9, column=0, columnspan=2, pady=10)

    diagnose_button = tk.Button(button_frame, text="診断する", command=compute_result, width=14)
    diagnose_button.pack(side="left", padx=8)
    save_button = tk.Button(button_frame, text="結果を保存", command=save_result, width=14)
    save_button.pack(side="left", padx=8)
    close_button = tk.Button(button_frame, text="終了", command=root.destroy, width=14)
    close_button.pack(side="left", padx=8)

    root.mainloop()


# コンソール版の診断フローを実行します。
# 入力プロンプトから値を受け取り、スコア計算と結果表示を行います。
def main_console():
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
        fname = save_report(s, cat, tips)
        print(f"保存しました: {fname}")


# アプリケーションのエントリポイントです。
# ここでは GUI 実行を起動します。
def main():
    run_gui()

if __name__ == '__main__':
    main()
