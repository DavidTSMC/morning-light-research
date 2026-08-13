from pathlib import Path
from contextlib import redirect_stdout

OUT = Path(
    "reports/daily_report/daily_practical_report_v0_2.txt"
)

# ============================================================
# DAILY PRACTICAL REPORT v0.2
# UI / LANGUAGE PROTOTYPE ONLY
#
# IMPORTANT:
# - All values below are DISPLAY SAMPLES.
# - NOT production signals.
# - Multi-horizon rules are NOT yet defined.
# - Event Radar is NOT yet connected to live event data.
# ============================================================


def report():

    print("=" * 62)
    print("MORNING LIGHT — DAILY PRACTICAL REPORT v0.2")
    print("30秒實戰摘要｜DISPLAY PROTOTYPE ONLY")
    print("=" * 62)

    print()
    print("【市場脈動】")
    print("-" * 62)
    print("市場｜🟢 ↗  偏強")
    print("風險｜🟡 →  持續觀察")
    print("資料｜LIVE + Latest EOD（示意）")

    print()
    print("【個股核心】")
    print("-" * 62)
    print("2330 台積電　（示意案例）")
    print()
    print("短線｜🔴 ↓↓  新轉弱")
    print("中線｜🟡 ↑   持續偏多")
    print("長線｜🟡 ↑↑  結構偏多")
    print()
    print("多週期｜短弱、中長仍強｜目前未形成全面轉弱共振")

    print()
    print("【跨系確認】")
    print("-" * 62)
    print("J      ｜🔴 ↓   A型轉折")
    print("Bias5  ｜🟡 ↓   持續轉弱")
    print("Bias10 ｜🔴 ↓↓  新轉弱｜進入行動檢視")
    print("D-M    ｜🔴 ↓↓  新確認")
    print()
    print("跨系｜2 個獨立家族確認")
    print("狀態｜惡化中")
    print("部位｜檢視／考慮減碼")

    print()
    print("【事件雷達】")
    print("-" * 62)
    print("今日｜無重大事件")
    print("3日 ｜○○公司股東會　　　　[詳細資料 >]")
    print("7日 ｜台指／選擇權結算窗口　[詳細資料 >]")
    print()
    print("事件 ≠ 訊號；事件只提高注意層級。")

    print()
    print("【前台判讀原則】")
    print("-" * 62)
    print("🟢 = 新的正向 Trigger")
    print("🟡 = 延續／觀察，沒有新的 Trigger")
    print("🔴 = 新的負向 Trigger")
    print("↑ / ↑↑ / ↑↑↑ = 向上強度")
    print("↓ / ↓↓ / ↓↓↓ = 向下強度")
    print()
    print("燈號代表新事件方向，不代表嚴重程度。")
    print("嚴重程度由：跨系確認 × 持續性 × 傷害程度判斷。")

    print()
    print("【時間框架｜研究候選定義】")
    print("-" * 62)
    print("短線｜約 3–5 個交易日")
    print("中線｜約 10–20 個交易日")
    print("長線｜約 60 個交易日")
    print("半年線／年線｜保留為大結構背景，不占主畫面")
    print()
    print("注意：以上時間框架尚未取得 Production Authority。")

    print()
    print("=" * 62)
    print("前台講人話，後台留證據。")
    print("新・速・實・簡")
    print("=" * 62)


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
