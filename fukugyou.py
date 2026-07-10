#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

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
    fullwidth_map = str.maketrans({'ｙ': 'y', 'ｎ': 'n', 'Ｙ': 'y', 'Ｎ': 'n'})
    while True:
        s = input(prompt + " (y/n): ").strip()
        s_norm = s.translate(fullwidth_map).lower()
        if s_norm in ("y", "yes", "はい"):
            return True
        if s_norm in ("n", "no", "いいえ"):
            return False
        print("y または n で答えてください。")

def score_sidegig(monthly_income, time_hours, skill_level, risk_tolerance, 
                   workplace_allows, family_support, job_security):
    """
    副業適性スコア計算
    monthly_income: 月収（万円）
    time_hours: 週に確保できる副業時間（時間）
    skill_level: スキルレベル (1-5)
    risk_tolerance: リスク許容度 (1-5, 5が高い)
    workplace_allows: 職場が副業を認めている (bool)
    family_support: 家族の理解と支持がある (bool)
    job_security: 現職の安定性 (1-5, 5が安定)
    """
    score = 0
    
    # 月収: 低いほど副業ニーズが高い
    if monthly_income < 25:
        score += 3
    elif monthly_income < 40:
        score += 2
    elif monthly_income > 80:
        score -= 1
    
    # 時間確保: 週10時間以上あると理想的
    if time_hours >= 15:
        score += 3
    elif time_hours >= 10:
        score += 2
    elif time_hours >= 5:
        score += 1
    elif time_hours == 0:
        score -= 2
    
    # スキルレベル: 高いほど良い
    score += max(0, skill_level - 1)
    
    # リスク許容度
    if risk_tolerance >= 4:
        score += 2
    elif risk_tolerance >= 3:
        score += 1
    
    # 職場の許可
    if workplace_allows:
        score += 2
    else:
        score -= 1
    
    # 家族の支持
    if family_support:
        score += 1
    else:
        score -= 1
    
    # 現職の安定性: 不安定なら副業ニーズが高い
    if job_security <= 2:
        score += 2
    elif job_security >= 5:
        score -= 1
    
    return max(0, score)

def get_sidegig_recommendations(score, risk_tolerance, skill_level, time_hours):
    """副業タイプと推奨事項を返す"""
    tips = []
    
    if score <= 3:
        category = "副業は不要"
        tips.append("現在の収入と時間から、副業の優先度は低いと考えられます。")
        tips.append("ただし将来のキャリア構築を考えるなら、低リスク副業の検討も良いでしょう。")
    elif score <= 7:
        category = "副業検討中"
        tips.append("時間と能力があれば副業を始めても良い段階です。")
    else:
        category = "副業推奨"
        tips.append("副業開始を積極的に検討することをお勧めします。")
    
    # 副業タイプの提案
    tips.append("\n--- 推奨される副業タイプ ---")
    
    if risk_tolerance <= 2:
        tips.append("★ 低リスク型：データ入力、メール対応代行、簡単な記事作成（週5-10時間）")
    elif risk_tolerance <= 3:
        tips.append("★ 中リスク型：ブログ、Webライター、オンライン家庭教師（週10-15時間）")
    else:
        tips.append("★ 中～高リスク型：コンサル、プログラミング案件、自分のサービス販売（週15時間以上）")
    
    if skill_level >= 4:
        tips.append("高スキルを活かして：Web制作、アプリ開発、データ分析コンサル")
    elif skill_level >= 2:
        tips.append("適度なスキルで：オンライン講師、翻訳、デザイン案件")
    else:
        tips.append("スキル習得型：プログラミング学習しながら、初心者向け案件で実践")
    
    if time_hours >= 15:
        tips.append("豊富な時間を活かして：複数の小さな案件、または深く掘り下げた副業")
    elif time_hours < 5:
        tips.append("限られた時間を活かして：自動化収入（ブログ、note）、単価の高い案件に集中")
    
    tips.append("\n--- 実行前の注意点 ---")
    tips.append("① 必ず職場に副業の可否を確認してください")
    tips.append("② 確定申告が必要になることを認識してください（年20万円以上の所得）")
    tips.append("③ 本業とのバランスを第一に、無理のないペースで。")
    tips.append("④ 最初の3ヶ月は試行錯誤期間。焦らず続けることが重要です")
    
    return category, tips

def build_note_text(score, category, tips, monthly_income, time_hours, skill_level,
                    risk_tolerance, workplace_allows, family_support, job_security):
    """Note/SNSにそのまま貼り付けられる文章を作成する"""
    lines = []
    lines.append("副業診断結果")
    lines.append(f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"副業適性スコア: {score}")
    lines.append(f"診断結果: {category}")
    lines.append("")
    lines.append("あなたへのアドバイス")
    for tip in tips:
        tip_text = tip.replace("\n", " ").strip()
        if tip_text.startswith("---"):
            lines.append("")
            lines.append(tip_text.replace("---", "").strip())
        else:
            lines.append(f"・{tip_text}")
    lines.append("")
    lines.append("入力内容")
    lines.append(f"月収: {monthly_income}万円")
    lines.append(f"週の副業時間: {time_hours}時間")
    lines.append(f"スキルレベル: {skill_level}/5")
    lines.append(f"リスク許容度: {risk_tolerance}/5")
    lines.append(f"職場の副業許可: {'あり' if workplace_allows else 'なし'}")
    lines.append(f"家族の支持: {'あり' if family_support else 'なし'}")
    lines.append(f"現職の安定性: {job_security}/5")
    return "\n".join(lines)


def show_result_window(score, category, tips, monthly_income, time_hours, skill_level,
                       risk_tolerance, workplace_allows, family_support, job_security):
    """診断結果を見やすい別ウィンドウで表示する"""
    try:
        result_window = tk.Tk()
    except tk.TclError:
        return

    result_window.title("診断結果")
    result_window.geometry("740x800")
    result_window.resizable(False, False)
    result_window.configure(bg="#e9e0d1")

    style = ttk.Style(result_window)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Result.TFrame", background="#fdf8f0")
    style.configure("Main.TFrame", background="#e9e0d1")
    style.configure("Title.TLabel", background="#e9e0d1", foreground="#3a2f25", font=("Yu Gothic UI", 24, "bold"))
    style.configure("Score.TLabel", background="#fdf8f0", foreground="#875f2d", font=("Yu Gothic UI", 14, "bold"))
    style.configure("Body.TLabel", background="#ffffff", foreground="#4b4b4b", font=("Yu Gothic UI", 11))

    outer = ttk.Frame(result_window, style="Main.TFrame", padding=24)
    outer.pack(fill="both", expand=True)

    card = ttk.Frame(outer, style="Result.TFrame", padding=24)
    card.pack(fill="both", expand=True)

    ttk.Label(card, text="診断結果", style="Title.TLabel").pack(anchor="center", pady=(0, 10))
    ttk.Label(card, text=f"副業適性スコア: {score}", style="Score.TLabel").pack(anchor="center", pady=(0, 6))
    ttk.Label(card, text=f"総合判定: {category}", style="Score.TLabel").pack(anchor="center", pady=(0, 12))

    text_area = tk.Text(card, height=24, width=84, wrap="word", bg="#fcfaf6", fg="#333333", relief="solid", bd=1, padx=14, pady=14, font=("Yu Gothic UI", 11))
    text_area.pack(fill="both", expand=True)
    text_area.insert("end", f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    text_area.insert("end", "あなたへのアドバイス\n")
    for tip in tips:
        clean_tip = tip.replace("\n", " ").strip()
        if clean_tip.startswith("---"):
            text_area.insert("end", f"\n{clean_tip.replace('---', '').strip()}\n")
        else:
            text_area.insert("end", f"・{clean_tip}\n")
    text_area.insert("end", f"\n入力内容\n")
    text_area.insert("end", f"月収: {monthly_income}万円\n")
    text_area.insert("end", f"週の副業時間: {time_hours}時間\n")
    text_area.insert("end", f"スキルレベル: {skill_level}/5\n")
    text_area.insert("end", f"リスク許容度: {risk_tolerance}/5\n")
    text_area.insert("end", f"職場の副業許可: {'あり' if workplace_allows else 'なし'}\n")
    text_area.insert("end", f"家族の支持: {'あり' if family_support else 'なし'}\n")
    text_area.insert("end", f"現職の安定性: {job_security}/5\n")
    text_area.configure(state="disabled")

    close_button = ttk.Button(card, text="閉じる", command=result_window.destroy)
    close_button.pack(pady=(14, 0))
    close_button.configure(style="Accent.TButton")
    result_window.mainloop()


def ask_questions_gui():
    """別画面の入力フォームで質問に回答する"""
    try:
        root = tk.Tk()
    except tk.TclError:
        return None

    root.title("副業診断")
    root.geometry("520x540")
    root.resizable(False, False)
    root.configure(bg="#f4efe9")

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Card.TFrame", background="#ffffff")
    style.configure("Main.TFrame", background="#f4efe9")
    style.configure("Title.TLabel", background="#f4efe9", foreground="#2f2a24", font=("Yu Gothic UI", 20, "bold"))
    style.configure("Subtitle.TLabel", background="#f4efe9", foreground="#7b756f", font=("Yu Gothic UI", 10))
    style.configure("Field.TLabel", background="#ffffff", foreground="#544d46", font=("Yu Gothic UI", 10))
    style.configure("Accent.TButton", foreground="#ffffff", background="#8a6d3b", font=("Yu Gothic UI", 10, "bold"))
    style.configure("Secondary.TButton", foreground="#5f574f", background="#efe7dc", font=("Yu Gothic UI", 10))
    style.map("Accent.TButton", background=[("active", "#75562d"), ("!disabled", "#8a6d3b")])
    style.map("Secondary.TButton", background=[("active", "#e4d8ca"), ("!disabled", "#efe7dc")])
    style.configure("TEntry", padding=7, fieldbackground="#fcfbf8")
    style.configure("TCombobox", padding=7, fieldbackground="#fcfbf8")

    monthly_income_var = tk.StringVar(value="40.0")
    time_hours_var = tk.StringVar(value="5.0")
    skill_level_var = tk.StringVar(value="2")
    risk_tolerance_var = tk.StringVar(value="2")
    workplace_var = tk.StringVar(value="はい")
    family_var = tk.StringVar(value="はい")
    job_security_var = tk.StringVar(value="3")

    result = {}

    def validate_and_submit():
        nonlocal result
        try:
            monthly_income = float(monthly_income_var.get())
            time_hours = float(time_hours_var.get())
            skill_level = int(skill_level_var.get())
            risk_tolerance = int(risk_tolerance_var.get())
            job_security = int(job_security_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "数値は半角で入力してください。")
            return

        if monthly_income <= 0:
            messagebox.showerror("入力エラー", "月収は0より大きい値を入力してください。")
            return
        if time_hours <= 0:
            messagebox.showerror("入力エラー", "週に副業に使える時間は0より大きい値を入力してください。")
            return
        if not 1 <= skill_level <= 5:
            messagebox.showerror("入力エラー", "スキルレベルは1〜5で入力してください。")
            return
        if not 1 <= risk_tolerance <= 5:
            messagebox.showerror("入力エラー", "リスク許容度は1〜5で入力してください。")
            return
        if not 1 <= job_security <= 5:
            messagebox.showerror("入力エラー", "現職の安定性は1〜5で入力してください。")
            return

        workplace_allows = workplace_var.get() == "はい"
        family_support = family_var.get() == "はい"
        result = {
            "monthly_income": monthly_income,
            "time_hours": time_hours,
            "skill_level": skill_level,
            "risk_tolerance": risk_tolerance,
            "workplace_allows": workplace_allows,
            "family_support": family_support,
            "job_security": job_security,
        }
        root.quit()

    def cancel():
        if root.winfo_exists():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", cancel)

    outer = ttk.Frame(root, style="Main.TFrame", padding=20)
    outer.pack(fill="both", expand=True)

    card = ttk.Frame(outer, style="Card.TFrame", padding=20)
    card.pack(fill="both", expand=True)

    ttk.Label(card, text="副業診断", style="Title.TLabel").pack(anchor="center", pady=(0, 4))
    ttk.Label(card, text="あなたの状況を入力して、適性をチェックします。", style="Subtitle.TLabel").pack(anchor="center", pady=(0, 14))

    fields_frame = ttk.Frame(card, style="Card.TFrame")
    fields_frame.pack(fill="both", expand=True)

    fields = [
        ("月収（万円）", monthly_income_var, "entry"),
        ("週に副業に使える時間（時間）", time_hours_var, "entry"),
        ("スキルレベル（1=初心者, 5=エキスパート）", skill_level_var, "scale"),
        ("リスク許容度（1=回避的, 5=積極的）", risk_tolerance_var, "scale"),
        ("職場は副業を認めていますか？", workplace_var, "combo"),
        ("家族の理解と支持はありますか？", family_var, "combo"),
        ("現職の安定性（1=不安定, 5=非常に安定）", job_security_var, "scale"),
    ]

    for idx, (label_text, variable, widget_type) in enumerate(fields):
        ttk.Label(fields_frame, text=label_text, style="Field.TLabel").grid(row=idx, column=0, sticky="w", pady=4, padx=(0, 10))
        if widget_type == "combo":
            combo = ttk.Combobox(fields_frame, textvariable=variable, values=["はい", "いいえ"], state="readonly", width=22)
            combo.grid(row=idx, column=1, sticky="ew", pady=4)
        elif widget_type == "scale":
            combo = ttk.Combobox(fields_frame, textvariable=variable, values=["1", "2", "3", "4", "5"], state="readonly", width=22)
            combo.grid(row=idx, column=1, sticky="ew", pady=4)
        else:
            entry = ttk.Entry(fields_frame, textvariable=variable, width=24)
            entry.grid(row=idx, column=1, sticky="ew", pady=4)

    fields_frame.columnconfigure(1, weight=1)

    button_frame = ttk.Frame(card, style="Card.TFrame")
    button_frame.pack(fill="x", pady=(14, 0))
    ttk.Button(button_frame, text="診断する", style="Accent.TButton", command=validate_and_submit).pack(side="left", padx=(0, 8))
    ttk.Button(button_frame, text="キャンセル", style="Secondary.TButton", command=cancel).pack(side="left")

    root.mainloop()
    root.destroy()
    return result or None


def main():
    print("=== 副業診断アプリ ===")
    print("あなたの副業適性を診断します。\n")

    answers = ask_questions_gui()
    if answers is None:
        print("診断をキャンセルしました。")
        return

    monthly_income = answers["monthly_income"]
    time_hours = answers["time_hours"]
    skill_level = answers["skill_level"]
    risk_tolerance = answers["risk_tolerance"]
    workplace_allows = answers["workplace_allows"]
    family_support = answers["family_support"]
    job_security = answers["job_security"]
    
    score = score_sidegig(monthly_income, time_hours, skill_level, risk_tolerance,
                          workplace_allows, family_support, job_security)
    category, tips = get_sidegig_recommendations(score, risk_tolerance, skill_level, time_hours)
    note_text = build_note_text(score, category, tips, monthly_income, time_hours,
                                skill_level, risk_tolerance, workplace_allows,
                                family_support, job_security)
    
    print("\n" + "="*50)
    print(f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"副業適性スコア: {score}")
    print(f"診断結果: 【{category}】")
    print("="*50)
    
    print("\nあなたへのアドバイス:")
    for tip in tips:
        print(tip)

    show_result_window(score, category, tips, monthly_income, time_hours, skill_level,
                       risk_tolerance, workplace_allows, family_support, job_security)

    print("\n" + "="*50)
    print("Note/SNSに貼り付ける本文")
    print("="*50)
    print(note_text)
    print("="*50)
    
    if ask_yesno("\n診断結果をファイルに保存しますか？"):
        fname = f"sidegig_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(note_text + "\n")
        print(f"✓ 保存しました: {fname}")

if __name__ == '__main__':
    main()
