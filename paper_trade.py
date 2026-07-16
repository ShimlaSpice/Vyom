from app.market.market_data_provider import MarketDataProvider
from app.scanner.scoring import ScoringEngine
from app.scanner.decision_engine import DecisionEngine
from app.scanner.technical_indicators import TechnicalIndicatorEngine
from app.scanner.candidate_builder import build_candidate
from data.nifty50 import NIFTY50
from app.scanner.formatter import ScannerFormatter
from app.scanner.ranking import RankingEngine

SYMBOLS = NIFTY50

provider = MarketDataProvider()
indicator_engine = TechnicalIndicatorEngine()
scoring_engine = ScoringEngine()
decision_engine = DecisionEngine()
formatter = ScannerFormatter()

recommendations = []

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

        recommendations.append(recommendation)
    
        successful += 1
    
    except Exception as e:
        print(f"❌ {symbol}: {e}")
        failed += 1
        continue


ranking_engine = RankingEngine()

ranked_recommendations = ranking_engine.rank(recommendations)

print()
print(formatter.format(ranked_recommendations))

print("\n" + "=" * 70)
print("SCAN COMPLETE")
print("=" * 70)
print(f"Successful : {successful}")
print(f"Failed     : {failed}")
print(f"Total      : {len(SYMBOLS)}")
print("=" * 70)