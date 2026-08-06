import pandas as pd

from indicators.wr import calculate_wr
from indicators.psy import calculate_psy
from indicators.kdj import calculate_j
from indicators.roc import calculate_roc
from indicators.mtm import calculate_mtm




def build_evidence_matrix(df,ticker):
    ticker_code = ticker.split(".")[0]

    council = {}







    matrix = pd.DataFrame(
    index=[
        "WR",
        "PSY",
        "KDJ",
        "ROC",
        "MTM",
        "BBI",
        "OBV",
        "MACD",
        "DMI_OSC",
        "BIAS",
    ],
    columns=[
        "2330",
        "2454",
        "2882",
        "0050",
    ]
)

    df["WR14"] = calculate_wr(df)
    
    wr_latest = df["WR14"].iloc[-1]

    if wr_latest > -20:
        matrix.loc["WR", ticker_code] = "🟢↑"
    elif wr_latest < -80:
        matrix.loc["WR", ticker_code] = "🔴↓"
    else:
        matrix.loc["WR",ticker_code] = "🟡→"

    council["WR"] = {
    "role": "Exhaustion",
    "new_event": "🟡 WAIT",
    "current_position": "🟡 WAIT",
    "confidence": 3,
    "next_trigger": "WR > -20",
    "explanation": "Oversold is improving, waiting for confirmation."
}


    df["PSY"] = calculate_psy(df)

    psy_latest = df["PSY"].iloc[-1]

    if psy_latest > 50:
        matrix.loc["PSY", ticker_code] = "🟢↑"

    elif psy_latest < 20:
        matrix.loc["PSY", ticker_code] = "🔴↓"

    else:
        matrix.loc["PSY", ticker_code] = "🟡→"


    council["PSY"] = {
    "role": "Emotion",
    "new_event": "🟡 WAIT",
    "current_position": "🟡 WAIT",
    "confidence": 3,
    "next_trigger": "PSY > 50",
    "explanation": "Market sentiment is recovering."
}


        
    df["KDJ"] = calculate_j(df)
    
    j_now = df["KDJ"].iloc[-1]
    j_prev = df["KDJ"].iloc[-2]
    j_prev2 = df["KDJ"].iloc[-3]

    j_v_turn = j_prev < j_prev2 and j_now > j_prev
    j_a_turn = j_prev > j_prev2 and j_now < j_prev

    if j_v_turn and j_now < 30:
        matrix.loc["KDJ",ticker_code ] = "🟢↑"
    elif j_a_turn and j_now > 70:
        matrix.loc["KDJ",ticker_code] = "🔴↓"
    else:
        matrix.loc["KDJ",ticker_code] = "🟡→"
 

    council["J"] = {

    "role": "Turning",

    "new_event": "🟢 EARLY TURN",

    "current_position": "🟢 YES",

    "confidence": 4,

    "next_trigger": "ROC > 0",

    "explanation": "Early turning detected. Waiting for momentum confirmation."

}


    df["ROC"] = calculate_roc(df)
    
    roc_latest = df["ROC"].iloc[-1]

   
    if roc_latest > 0:
        matrix.loc["ROC",ticker_code ] = "🟢↑"
    elif roc_latest < 0:
        matrix.loc["ROC", ticker_code] = "🔴↓"
    else:
        matrix.loc["ROC", ticker_code] = "🟡→"


    council["ROC"] = {

    "role": "Momentum",

    "new_event": "🟢 MOMENTUM",

    "current_position": "🟢 YES",

    "confidence": 4,

    "next_trigger": "MTM > 0",

    "explanation": "Momentum is turning positive."
}



    df["MTM"] = calculate_mtm(df)
    
    mtm_latest = df["MTM"].iloc[-1]

    if mtm_latest > 0:
        matrix.loc["MTM",ticker_code ] = "🟢↑"
    elif mtm_latest < 0:
        matrix.loc["MTM", ticker_code] = "🔴↓"
    else:
        matrix.loc["MTM", ticker_code] = "🟡→"      


    council["MTM"] = {

    "role": "Acceleration",

    "new_event": "🟢 ACCELERATING",

    "current_position": "🟢 YES",

    "confidence": 4,

    "next_trigger": "DMI > 0",

    "explanation": "Price acceleration is improving."
}


    dmi_now = df["DMI_OSC"].iloc[-1]
    dmi_prev = df["DMI_OSC"].iloc[-2]

    if dmi_prev <= 0 and dmi_now > 0:
        matrix.loc["DMI_OSC",ticker_code] = "🟢↑"
    elif dmi_prev >= 0 and dmi_now < 0:
        matrix.loc["DMI_OSC", ticker_code] = "🔴↓"
    else:
        matrix.loc["DMI_OSC", ticker_code] = "🟡→"


    council["DMI"] = {
    "role": "Trend",

    "new_event": "🟢 TREND",

    "current_position": "🟢 YES",

    "confidence": 5,

    "next_trigger": "Volume confirms",

    "explanation": "Trend confirmation is strengthening."
}





# -----------------------
# Today's Confidence
# -----------------------

    confidence = "Neutral"

    reasons = []

    council_vote = {
        "WR": "🟢 YES" if wr_latest > -20 else "🟡 WAIT",
        "PSY": "🟡 WAIT",
        "J": "🟢 YES" if j_now > 30 else "🟡 WAIT",
        "ROC": "🟢 YES" if roc_latest > 0 else "🔴 NO",
        "MTM": "🟢 YES" if mtm_latest > 0 else "🔴 NO",
        "DMI": "🟢 YES" if dmi_now > 0 else "🔴 NO",
    }

   
    if wr_latest > -20:
         reasons.append("WR positive")

    if j_v_turn and j_now < 30:
        reasons.append("J low-level V-turn")

    if roc_latest > 0:
        reasons.append("ROC positive")

    if mtm_latest > 0:
        reasons.append("MTM positive")

    if len(reasons) >= 2:
        confidence = "Increasing"


    return matrix, confidence, reasons, council


# --------------------------
# Market Pulse
# --------------------------

def build_market_pulse():

    market_pulse = {
        "SOX": "🟢",
        "TSM ADR": "🟢",
        "VIX": "🟡",
        "DXY": "🟢",
        "US10Y": "🟡",
        "USD/TWD": "🟢"
    }

    overall_market = "Improving"

    return market_pulse, overall_market

def build_market_council():


    council = {
        "SOX": "🟢 Strong",
        "NASDAQ": "🟢 Strong",
        "TSM ADR": "🟢 Positive",
        "VIX": "🟡 Watch",
        "DXY": "🟢 Supportive",
        "US10Y": "🟢 Supportive",
        "Oil": "🟡 Neutral",
        "USD/TWD": "🟢 Supportive",
    }

    overall = "🌅 Improving"

    return council, overall

def build_evidence_convergence():

    evidence = [

        "🟢 Memory Trend",

        "🟢 AI Supply Chain",

        "🟢 TSM ADR Positive",

        "🟢 SOX Strong",

        "🟡 Financials Waiting",

    ]

    level = "HIGH"

    return evidence, level


def build_elite_intelligence(council):

    selected = []

    waiting = []

    for member, report in council.items():

        if "🟢" in report["current_position"]:

            selected.append(report["new_event"])

        else:

            waiting.append(member)

    return selected, waiting

def build_trigger_package():

    triggers = [

        {
            "name": "WR",
            "current": -92,
            "target": -80,
            "distance": 12,
            "status": "Waiting",
        },

        {
            "name": "PSY",
            "current": 28,
            "target": 35,
            "distance": 7,
            "status": "Waiting",
        },

    ]

    return triggers



def build_today_action(confidence):

    if confidence == "Increasing":
        return "🟢 Observe / Prepare"

    return "🟡 Wait"















