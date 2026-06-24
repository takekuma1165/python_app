#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

def main():
    print("=== 副業診断アプリ ===")
    print("あなたの副業適性を診断します。\n")
    
    monthly_income = ask_num("月収（万円）: ", float, default=40.0)
    time_hours = ask_num("週に副業に使える時間（時間）: ", float, default=5.0)
    skill_level = ask_num("現在のスキルレベル（1=初心者, 5=エキスパート）: ", int, default=2)
    risk_tolerance = ask_num("リスク許容度（1=回避的, 5=積極的）: ", int, default=2)
    workplace_allows = ask_yesno("職場は副業を認めていますか？")
    family_support = ask_yesno("家族の理解と支持はありますか？")
    job_security = ask_num("現職の安定性（1=不安定, 5=非常に安定）: ", int, default=3)
    
    score = score_sidegig(monthly_income, time_hours, skill_level, risk_tolerance,
                          workplace_allows, family_support, job_security)
    category, tips = get_sidegig_recommendations(score, risk_tolerance, skill_level, time_hours)
    
    print("\n" + "="*50)
    print(f"診断日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"副業適性スコア: {score}")
    print(f"診断結果: 【{category}】")
    print("="*50)
    
    print("\nあなたへのアドバイス:")
    for tip in tips:
        print(tip)
    
    if ask_yesno("\n診断結果をファイルに保存しますか？"):
        fname = f"sidegig_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("副業診断レポート\n")
            f.write("="*50 + "\n")
            f.write(f"診断日時: {datetime.now().isoformat()}\n")
            f.write(f"\n入力内容:\n")
            f.write(f"  月収: {monthly_income}万円\n")
            f.write(f"  週の副業時間: {time_hours}時間\n")
            f.write(f"  スキルレベル: {skill_level}/5\n")
            f.write(f"  リスク許容度: {risk_tolerance}/5\n")
            f.write(f"  職場の副業許可: {'あり' if workplace_allows else 'なし'}\n")
            f.write(f"  家族の支持: {'あり' if family_support else 'なし'}\n")
            f.write(f"  現職の安定性: {job_security}/5\n")
            f.write(f"\n診断結果:\n")
            f.write(f"  適性スコア: {score}\n")
            f.write(f"  総合判定: {category}\n")
            f.write(f"\nアドバイス:\n")
            for tip in tips:
                f.write(tip + "\n")
        print(f"✓ 保存しました: {fname}")

if __name__ == '__main__':
    main()
