#!/bin/bash
# Script to fix shares outstanding based on market cap / price calculation
# This script compares shares in database with shares calculated from market_cap/price
# and updates database if difference > 10%

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "=== Fix Shares Outstanding from Market Cap Calculation ==="
echo ""

# Get all tickers
TICKERS=$(docker-compose exec -T postgres psql -U dcf_user -d dcf_db -t -c "SELECT ticker FROM stocks ORDER BY ticker;" | tr -d ' ')

FIXED_COUNT=0
CHECKED_COUNT=0

for TICKER in $TICKERS; do
    if [ -z "$TICKER" ]; then
        continue
    fi
    
    CHECKED_COUNT=$((CHECKED_COUNT + 1))
    
    echo "Checking $TICKER..."
    
    # Get shares from database
    SHARES_DB=$(docker-compose exec -T postgres psql -U dcf_user -d dcf_db -t -c \
        "SELECT so.shares_outstanding FROM stocks s JOIN shares_outstanding so ON s.id = so.stock_id WHERE s.ticker = '$TICKER' ORDER BY so.period_date DESC LIMIT 1;" | tr -d ' ')
    
    if [ -z "$SHARES_DB" ] || [ "$SHARES_DB" = "0" ]; then
        echo "  ⚠️  No shares found in database"
        continue
    fi
    
    # Get market cap and price from API
    MARKET_CAP=$(curl -s "http://localhost:8000/api/stocks/$TICKER" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('result', {}).get('market_cap', 0))" 2>/dev/null || echo "0")
    PRICE=$(curl -s "http://localhost:8000/api/stocks/$TICKER" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('result', {}).get('price', 0))" 2>/dev/null || echo "0")
    
    if [ "$MARKET_CAP" = "0" ] || [ "$PRICE" = "0" ]; then
        echo "  ⚠️  Could not get market cap or price from API"
        continue
    fi
    
    # Calculate shares from market cap
    SHARES_CALC=$(python3 -c "print(int($MARKET_CAP / $PRICE))" 2>/dev/null || echo "0")
    
    if [ "$SHARES_CALC" = "0" ]; then
        echo "  ⚠️  Could not calculate shares from market cap"
        continue
    fi
    
    # Calculate difference percentage
    DIFF_PCT=$(python3 -c "diff = abs($SHARES_DB - $SHARES_CALC) / $SHARES_CALC * 100 if $SHARES_CALC > 0 else 0; print(f'{diff:.2f}')" 2>/dev/null || echo "0")
    
    echo "  DB: $SHARES_DB, MC/Price: $SHARES_CALC, Diff: ${DIFF_PCT}%"
    
    # If difference > 10%, update database
    if (( $(echo "$DIFF_PCT > 10" | bc -l) )); then
        echo "  ❌ Difference > 10%, updating database..."
        
        # Update shares in database
        docker-compose exec -T postgres psql -U dcf_user -d dcf_db -c "
            UPDATE shares_outstanding 
            SET shares_outstanding = $SHARES_CALC,
                calculation_method = 'market_cap_calculation',
                source_column = 'market_cap / price',
                updated_at = CURRENT_TIMESTAMP
            WHERE stock_id = (SELECT id FROM stocks WHERE ticker = '$TICKER')
            AND period_date = (SELECT MAX(period_date) FROM shares_outstanding WHERE stock_id = (SELECT id FROM stocks WHERE ticker = '$TICKER'));
        " > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Updated shares to $SHARES_CALC"
            FIXED_COUNT=$((FIXED_COUNT + 1))
        else
            echo "  ❌ Failed to update database"
        fi
    elif (( $(echo "$DIFF_PCT > 5" | bc -l) )); then
        echo "  ⚠️  Difference > 5%, please review manually"
    else
        echo "  ✓ OK"
    fi
    
    echo ""
done

echo "=== Summary ==="
echo "Checked: $CHECKED_COUNT tickers"
echo "Fixed: $FIXED_COUNT tickers"
echo ""

