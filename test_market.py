from app.market.market_engine import MarketEngine

engine = MarketEngine()

snapshot = engine.get_snapshot()

print(snapshot)