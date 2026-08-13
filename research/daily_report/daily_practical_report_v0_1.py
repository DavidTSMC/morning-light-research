from pathlib import Path
from datetime import datetime

OUT = Path(
    "reports/daily_report/daily_practical_report_v0_1.txt"
)

# ============================================================
# MORNING LIGHT DAILY PRACTICAL REPORT v0.1
#
# FRONT-END SEMANTICS
#
# GREEN  = new bullish trigger
# YELLOW = continuation / observation
# RED    = new bearish trigger
#
# Arrow  = direction
#
# Severity is NOT encoded by traffic-light color.
# Severity belongs to cross-family / thesis state.
#
# Prototype only:
# NO production signal
# NO live API
# NO email
# ============================================================


def build_report():

    lines = []

    lines.append("=" * 64)
    lines.append("MORNING LIGHT — 每日實戰報告 v0.1")
    lines.append("=" * 64)

    lines.append("")
    lines.append(
        f"產生時間｜{datetime.now():%Y-%m-%d %H:%M}"
    )

    lines.append(
        "資料狀態｜介面 Prototype / 尚未連接即時市場"
    )

    lines.append("")
    lines.append("-" * 64)

    # ========================================================
    # MARKET SUMMARY — PLACEHOLDER
    # ========================================================

    lines.append("【市場總覽】")
    lines.append("")
    lines.append("市場狀態｜🟡 → 觀察中")
    lines.append("風險環境｜尚未連接 Market Pulse")
    lines.append("主題輪動｜尚未連接 Theme Engine")

    lines.append("")
    lines.append("-" * 64)

    # ========================================================
    # STOCK CARD — SEMANTIC PROTOTYPE ONLY
    #
    # IMPORTANT:
    # These are SAMPLE states to test readability.
    # They are NOT current 2330 signals.
    # ========================================================

    lines.append("【個股實戰卡】")
    lines.append("")
    lines.append("2330 台積電")
    lines.append("資料｜示範資料，非目前市場訊號")

    lines.append("")
    lines.append("🔴 ↘ 新轉弱｜J 出現 A 型轉折")
    lines.append("🟡 ↘ 持續轉弱｜Bias5 弱化中")
    lines.append("🔴 ↘ 新轉弱｜Bias10 下穿 0 軸")
    lines.append("🔴 ↘ 跨系確認｜D−M 下穿 0 軸")

    lines.append("")
    lines.append("狀態｜惡化中")
    lines.append("跨系｜2 個獨立家族確認")
    lines.append("部位｜檢視／考慮減碼")

    lines.append("")
    lines.append("-" * 64)

    # ========================================================
    # EVIDENCE — BACK-END TRACE
    # ========================================================

    lines.append("【查證區｜Evidence】")
    lines.append("")
    lines.append("J       ｜A-turn")
    lines.append("Bias5   ｜持續弱化")
    lines.append("Bias10  ｜Bearish zero-cross")
    lines.append("D−M     ｜Bearish zero-cross")

    lines.append("")
    lines.append(
        "Cross-family｜Bias family + D−M family"
    )

    lines.append("")
    lines.append("-" * 64)

    # ========================================================
    # CONSTITUTION
    # ========================================================

    lines.append("【前台判讀原則】")
    lines.append("")
    lines.append("🟢 = 新的正向 Trigger")
    lines.append("🟡 = 延續／觀察，沒有新的 Trigger")
    lines.append("🔴 = 新的負向 Trigger")
    lines.append("↗ / → / ↘ = 方向")
    lines.append("")
    lines.append(
        "燈號不代表嚴重程度；"
        "嚴重程度由跨系確認與狀態判斷。"
    )

    lines.append("")
    lines.append("=" * 64)
    lines.append("前台講人話，後台留證據。")
    lines.append("新・速・實・簡")
    lines.append("=" * 64)

    return "\n".join(lines)


report = build_report()

OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUT.write_text(
    report,
    encoding="utf-8"
)

print(report)

print()
print("Saved:")
print(" ", OUT)
