from engine.download_engine import download_stock
from engine.indicator_engine import build_indicators

from reports.evidence_matrix import (
    build_evidence_matrix,
    build_market_pulse, 
    build_market_council,
    build_today_action,
    build_evidence_convergence,
    build_elite_intelligence,
)

watch_list = [
    "2330.TW",
    "2454.TW",
    "2882.TW",
    "0050.TW",
]


# ===== Multi-stock Loop ====

elite_results = []

for ticker in watch_list:
    print("\n" + "=" * 60)
    print(f"📈 {ticker}")
    print("=" * 60)

    # 下載資料
    df = download_stock(ticker)

    #建立指標
    df = build_indicators(df)

    # Evidence Engine + Council 
    matrix, confidence, reasons, council = build_evidence_matrix(df, ticker)

    # Market Pulse
    market_pulse, overall_market = build_market_pulse()
    market_council, market_overall = build_market_council()
    external_evidence, convergence_level = build_evidence_convergence()
    selected_signals, waiting_signals = build_elite_intelligence(council)


    # Today's Action
    today_action = build_today_action(confidence)

green_count = sum(
    1
    for report in council.values()
    if "🟢" in report["current_position"]
)

reason_count = len(reasons)

confidence_bonus = {
    "Neutral": 0,
    "Increasing": 5,
}.get(confidence, 0)

action_bonus = {
    "🟡 Wait": 0,
    "🟢 Observe / Prepare": 2,
    "🟢 Prepare / Enter": 5,
}.get(today_action, 0)


elite_score = (
    green_count * 10
    + reason_count * 2
    + confidence_bonus
    + action_bonus
)


elite_results.append({
    "ticker": ticker,
    "elite_score": elite_score,
    "green_count": green_count,
    "reason_count": reason_count,
    "confidence": confidence,
    "today_action": today_action,
    "confidence_bonus": confidence_bonus,
    "action_bonus": action_bonus,
}) 


# print(df[["Close", "WR14","KDJ", "PSY5", "MTM5", "ROC5",]].tail())
    

print("\n🌅 MORNING LIGHT")
print("=" * 50)

print("\n🗳️ Morning Light Council")
print("=" * 40)

 
for member, report in council.items():

    print(f"\n{member}")

    print(f"Role             : {report['role']}")

    print(f"New Event        : {report['new_event']}")

    print(f"Current Position : {report['current_position']}")

    print(f"Confidence       : {report['confidence']}")

    print(f"Next Trigger     : {report['next_trigger']}")

    print(f"Explanation      : {report['explanation']}")


print("\n📌 Next Trigger Queue")
print("=" * 40)

for member, report in council.items():
    print(f"{member:<6} → {report['next_trigger']}")


print("\n📊 Decision Board")
print(matrix)

print("\n🌅 Today's Confidence")
print(confidence)

print("\nReasons")
for r in reasons:
    print("-", r)

print("\n🌍 Market Council")
print("=" * 40)

for item, status in market_council.items():
    print(f"{item:<10} {status}")

print("\nOverall")
print(market_overall)

print("\n🌟 Evidence Convergence")
print("=" * 40)

print("\n⭐ Elite Pool Intelligence")

print("=" * 40)

print("\nWhy Selected Today")

for signal in selected_signals:
    print(signal)

print("\nWaiting")

for signal in waiting_signals:
    print(signal)














for item in external_evidence:
    print(item)

print("\nConvergence Level")
print(convergence_level)

print("\n🌍 Market Pulse")

print(market_pulse)

print("Overall:", overall_market)




print("\n🧭 Today's Action")
print(today_action)

# ==========================
# Elite Pool Ranking
# ==========================


elite_results = sorted(
    elite_results,
    key=lambda item: item["elite_score"],
    reverse=True,
)

print("\n⭐ ELITE POOL RANKING")
print("=" * 60)

for rank, item in enumerate(elite_results, start=1):
    print(
        f"{rank}. {item['ticker']:<10} "
        f"Score={item['elite_score']:<3} "
        f"Green={item['green_count']} "
        f"Reasons={item['reason_count']} "
        f"Confidence={item['confidence']} "
        f"Action={item['today_action']}"
    )

print("\n🌅 MORNING BRIEF")
print("=" * 40)

top = elite_results[0]

print(f"\n🌍 Market")
print(market_overall)

print(f"\n⭐ Today's Top Pick")
print(top["ticker"])

print(f"\n🎯 Action")
print(top["today_action"])

print("\n💡 Why")

for signal in selected_signals:
    print(signal)

print("\n⏳ Waiting")

for signal in waiting_signals:
    print(signal)
























