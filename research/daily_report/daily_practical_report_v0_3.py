from pathlib import Path
from contextlib import redirect_stdout

OUT = Path(
    "reports/daily_report/daily_practical_report_v0_3.txt"
)

# ============================================================
# MORNING LIGHT DAILY PRACTICAL REPORT v0.3
# FREEZE-CANDIDATE UI PROTOTYPE
#
# IMPORTANT
# All values below are DISPLAY SAMPLES.
# NOT production signals.
# ============================================================


def position_card(name, short, mid, long, cross, state, amount, event="—"):
    print(f"【{name}】")
    print(f"短　{short}")
    print(f"中　{mid}")
    print(f"長　{long}")
    print(f"跨系　{cross}")
    print(f"狀態　{state}")
    print(f"部位　{amount}")
    print(f"事件　{event}")


def report():

    print("=" * 82)
    print("🌅 MORNING LIGHT ✦｜晨光每日實戰報告")
    print("See Early · Judge Wisely · Act Gracefully.")
    print("30秒實戰摘要｜DISPLAY PROTOTYPE ONLY")
    print("=" * 82)

    # ========================================================
    # GLOBAL
    # ========================================================

    print()
    print("🌎【全球環境】")
    print("-" * 82)

    print(
        "風險 🟢 微降 ↓ ｜ "
        "情緒 🟢 正向 ↑ ｜ "
        "利率 🟡 偏高 → ｜ "
        "美元 🟡 持平 →"
    )

    print(
        "證據　VIX ↓／US10Y →／DXY →／SOX ↑↑／Oil ↓／Gold ↑"
    )

    print(
        "全球判讀　風險略降、情緒正向；利率仍是主要壓力。"
    )

    print(
        "確認條件　殖利率若進一步下降，通常較有利估值；"
        "若續升，壓力增加。"
    )

    print("全球詳情 >")

    # ========================================================
    # TAIWAN
    # ========================================================

    print()
    print("🇹🇼【台灣市場】")
    print("-" * 82)

    print(
        "風險 🟡 持平 → ｜ "
        "情緒 🟢 偏多 ↑ ｜ "
        "資金 🟢 回流 ↑ ｜ "
        "量能 🟡 待確認 →"
    )

    print(
        "證據　TAIEX ↑／TXF ↑↑／USD-TWD →／"
        "外資現貨 ↑／期貨避險注意"
    )

    print(
        "台股判讀　偏多輪動；資金改善，但量能尚未確認全面攻擊。"
    )

    print(
        "確認條件　攻擊量參考 ≥ 20日均量 × 1.2～1.3；"
        "並觀察價格與市場廣度同步轉強。"
    )

    print("台股詳情 >")

    # ========================================================
    # SECTOR
    # ========================================================

    print()
    print("🏭【產業輪動】")
    print("-" * 82)

    print(
        "AI 🟢 強 ↑↑ ｜ "
        "CPO 🟢 強 ↑↑ ｜ "
        "PCB 🟢 偏強 ↑ ｜ "
        "記憶體 🟡 持平 → ｜ "
        "重電 🟢 轉強 ↑"
    )

    print(
        "主軸　AI基建／CPO ↑↑ ｜ "
        "輪動　PCB／重電／金融／…"
    )

    print("產業詳情 >")

    # ========================================================
    # POSITIONS
    # ========================================================

    print()
    print("💼【我的持股｜固定追蹤】")
    print("-" * 82)

    position_card(
        "台積電",
        "🔴 新轉弱 ↓↓",
        "🟡 持續偏多 ↑",
        "🟡 結構偏多 ↑↑",
        "2/3",
        "結構受壓",
        "檢視／考慮減碼",
        "3日內重要事件 >",
    )

    print()

    position_card(
        "長榮",
        "🟡 觀察 →",
        "🟡 持續偏多 ↑",
        "🟡 結構偏多 ↑",
        "0/3",
        "結構完整",
        "維持",
        "法說（3日內） >",
    )

    print()

    position_card(
        "台達電",
        "🟡 觀察 →",
        "🟡 持續偏多 ↑",
        "🟡 結構偏多 ↑↑",
        "0/3",
        "結構完整",
        "維持",
    )

    # ========================================================
    # OPPORTUNITIES
    # ========================================================

    print()
    print("✨【今日機會｜每日輪動】")
    print("-" * 82)

    print("聯發科　🟢 新轉強 ↑↑　｜ 詳細 >")
    print("候選A　 🟢 結構轉佳 ↑　｜ 詳細 >")
    print("候選B　 🟢 新進榜 ↑　　 ｜ 詳細 >")

    # ========================================================
    # WATCH
    # ========================================================

    print()
    print("👀【持續觀察】")
    print("-" * 82)

    print("觀察A　排名下降，但結構尚未失效　｜ 詳細 >")

    # ========================================================
    # EVENT RADAR
    # ========================================================

    print()
    print("📅【事件雷達】")
    print("-" * 82)

    print("今日　無重大事件")
    print("3日　 股東會（台積電）／法說（長榮）　詳細 >")
    print("7日　 台指結算／MSCI調整／CPI／…　　　詳細 >")

    print()
    print("事件 ≠ 訊號；事件只提高注意層級。")

    # ========================================================
    # FOOTER
    # ========================================================

    print()
    print("-" * 82)
    print("更多個股 > ｜ 詳細證據 > ｜ 方法說明 >")
    print()
    print("前台講人話，後台留證據。")
    print("刪掉不必要的腦內轉換。")
    print("新・速・實・簡")
    print("=" * 82)


OUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

with OUT.open(
    "w",
    encoding="utf-8"
) as f:
    with redirect_stdout(f):
        report()

report()

print()
print("Saved:")
print(" ", OUT)
