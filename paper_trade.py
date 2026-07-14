from app.market.market_data_provider import MarketDataProvider
from app.scanner.scoring import ScoringEngine
from app.scanner.decision_engine import DecisionEngine
from app.scanner.technical_indicators import TechnicalIndicatorEngine
from app.scanner.candidate_builder import build_candidate
from data.nifty50 import NIFTY50


SYMBOLS = NIFTY50

provider = MarketDataProvider()
indicator_engine = TechnicalIndicatorEngine()
scoring_engine = ScoringEngine()
decision_engine = DecisionEngine()

successful = 0
failed = 0

print("=" * 70)
print(f"🚀 VYOM PAPER TRADING ({len(SYMBOLS)} Stocks)")
print("=" * 70)

for symbol in SYMBOLS:

    print(f"\nProcessing {symbol}...")

    qualified_symbol = f"{symbol}.NS"

    frame_map = provider.fetch_ohlcv(
        symbols=[qualified_symbol],
        period="2mo",
        interval="1d",
    )

    try:
        dataframe = frame_map.get(qualified_symbol)

        if dataframe is None:
            print(f"❌ {symbol}: No market data")
            continue

        candidate = build_candidate(
            symbol,
            dataframe,
        )

        score_result = scoring_engine.score_stock(candidate)

        recommendation = decision_engine.make_recommendation(score_result)

        print("=" * 60)
        print(f"Symbol      : {recommendation.symbol}")
        print(f"Action      : {recommendation.action}")
        print(f"Confidence  : {recommendation.confidence:.2f}%")
        print(f"Risk        : {recommendation.risk_level}")
        print(f"Quality     : {recommendation.trade_quality}")
        print("=" * 60)
    
        successful += 1
    
    except Exception as e:
        print(f"❌ {symbol}: {e}")
        failed += 1
        continue

print("\n" + "=" * 70)
print("SCAN COMPLETE")
print("=" * 70)
print(f"Successful : {successful}")
print(f"Failed     : {failed}")
print(f"Total      : {len(SYMBOLS)}")
print("=" * 70)