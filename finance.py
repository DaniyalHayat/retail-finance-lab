"""Synthetic retail finance case. Python 3.11+, standard library only."""
from __future__ import annotations
import argparse, calendar, csv, json, math, random, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 42
CAT = {'Electronics': (95, 62, 5.2), 'Home': (44, 23, 4.1), 'Essentials': (19, 10, 2.8)}
REGIONS = ('East', 'Central', 'West')
CASES = {'Base': (0.06, 0.01, 0.02, 38, 30), 'Downside': (-0.08, -0.02, 0.06, 52, 25), 'Upside': (0.13, 0.02, 0.01, 32, 35)}

def dump(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def generate():
    """18 actual months, nine segment combinations, twenty records per segment."""
    rng = random.Random(SEED); orders = []; plan = []
    for t in range(18):
        y, m = 2025 + t // 12, 1 + t % 12
        season = 1.35 if m in (11, 12) else 0.9 if m in (1, 2) else 1
        for ri, region in enumerate(REGIONS):
            for ci, (cat, (price, cogs, fulfill)) in enumerate(CAT.items()):
                bp = price * (1 + .01 * (y - 2025)); bc = cogs + fulfill
                bq = round((1700 + 150 * ri + 350 * ci) * season * (1 + .04 * (y - 2025)))
                aq = max(20, round(bq * (1 + rng.uniform(-.09, .12))))
                ap = round(bp * (1 + rng.uniform(-.035, .025)), 4)
                cost_factor = 1 + rng.uniform(-.025, .06)
                ac = round(bc * cost_factor, 4)
                plan.append(dict(month=f'{y}-{m:02}', region=region, category=cat, units=bq, net_price=round(bp, 4), variable_cost=bc, fixed_cost=18000))
                pieces = [aq // 20] * 20
                for j in range(aq % 20): pieces[j] += 1
                for j, units in enumerate(pieces):
                    orders.append(dict(order_id=f'R{len(orders)+1:06}', month=f'{y}-{m:02}', region=region, category=cat, units=units, net_price=ap, variable_cost=ac, merchandise_unit_cost=round(cogs*cost_factor,4), source='Synthetic seed 42'))
    dump(ROOT/'data/orders.csv', orders); dump(ROOT/'data/budget.csv', plan)
    return orders, plan

def bridge(plan, actual, fixed_plan, fixed_actual):
    """Exact sequential volume/mix/price/cost bridge, expenses positive in input."""
    if set(plan) != set(actual): raise ValueError('Plan and actual segments must match')
    qb = sum(x[0] for x in plan.values()); qa = sum(x[0] for x in actual.values())
    if qb <= 0: raise ValueError('Positive budget volume required')
    baseline = sum(q*(p-c) for q,p,c in plan.values()) - fixed_plan
    am = sum(q*(p-c) for q,p,c in actual.values()) - fixed_actual
    margin = (baseline + fixed_plan)/qb
    effects = {
        'Volume': (qa-qb)*margin,
        'Mix': sum(actual[k][0]*(plan[k][1]-plan[k][2]) for k in plan)-qa*margin,
        'Price': sum(actual[k][0]*(actual[k][1]-plan[k][1]) for k in plan),
        'Variable cost': -sum(actual[k][0]*(actual[k][2]-plan[k][2]) for k in plan),
        'Fixed cost': -(fixed_actual-fixed_plan),
    }
    return dict(budget=baseline, actual=am, effects=effects, residual=am-baseline-sum(effects.values()))

def wape(actual, predicted):
    if len(actual) != len(predicted) or not actual: raise ValueError('Matching non-empty series required')
    den = sum(abs(x) for x in actual)
    return sum(abs(a-p) for a,p in zip(actual,predicted))/den if den else None

def forecast(history, case='Base'):
    """Seasonal prior-year units, trailing six-month YoY calibration; no future actuals."""
    if case not in CASES: raise ValueError('Unknown case')
    if len(history) != 18: raise ValueError('Eighteen months required')
    growth, price_change, cost_change, dio, dpo = CASES[case]
    ratio = sum(x['units'] for x in history[12:18])/sum(x['units'] for x in history[:6])
    last = history[-1]; price = last['revenue']/last['units']; vc = last['variable_cost']/last['units']
    merchandise_ratio=last['merchandise_cost']/last['variable_cost']
    cash = 900000.; prev_inventory = last['merchandise_cost']*38/30
    prev_ar = last['revenue']*2/30; prev_ap = last['merchandise_cost']*30/30
    rows = []
    for i in range(12):
        month_no = 6+i; year = 2026+month_no//12; month=month_no%12+1
        days = calendar.monthrange(year,month)[1]
        units = history[6+i]['units']*ratio*(1+growth)
        revenue = units*price*(1+price_change); cost=units*vc*(1+cost_change)
        fixed=162000.*1.02; depreciation=18000.; ebitda=revenue-cost-fixed; ebit=ebitda-depreciation
        tax=max(0,ebit)*.25
        merchandise_cost=cost*merchandise_ratio
        inventory=merchandise_cost*dio/days; ar=revenue*2/days; ap=merchandise_cost*dpo/days
        dnwc=(inventory+ar-ap)-(prev_inventory+prev_ar-prev_ap)
        capex=25000.; fcf=ebitda-tax-dnwc-capex
        rows.append(dict(month=f'{year}-{month:02}', units=units, price=price*(1+price_change), unit_cost=vc*(1+cost_change), revenue=revenue, variable_cost=cost, fixed_cost=fixed, ebitda=ebitda, depreciation=depreciation, ebit=ebit, taxes=tax, inventory=inventory, ar=ar, ap=ap, change_nwc=dnwc, capex=capex, free_cash_flow=fcf, opening_cash=cash, ending_cash=cash+fcf, days=days, case=case))
        cash+=fcf; prev_inventory,prev_ar,prev_ap=inventory,ar,ap
    return rows

def build():
    orders, plan=generate(); out=ROOT/'outputs'; out.mkdir(exist_ok=True)
    db=sqlite3.connect(out/'retail.sqlite'); db.executescript((ROOT/'sql/model.sql').read_text())
    db.executemany('INSERT INTO orders VALUES(:order_id,:month,:region,:category,:units,:net_price,:variable_cost,:merchandise_unit_cost)',orders)
    db.executemany('INSERT INTO budget VALUES(:month,:region,:category,:units,:net_price,:variable_cost,:fixed_cost)',plan)
    db.commit(); db.row_factory=sqlite3.Row
    segments=[dict(x) for x in db.execute('SELECT * FROM segment_actuals ORDER BY month,region,category')]
    monthly=[dict(x) for x in db.execute('SELECT * FROM monthly_actuals ORDER BY month')]
    b={f"{x['month']}|{x['region']}|{x['category']}":(x['units'],x['net_price'],x['variable_cost']) for x in plan}
    a={f"{x['month']}|{x['region']}|{x['category']}":(x['units'],x['revenue']/x['units'],x['variable_cost']/x['units']) for x in segments}
    br=bridge(b,a,18000*len(plan),sum(x['fixed_cost'] for x in monthly))
    forecasts={c:forecast(monthly,c) for c in CASES}
    # Held-out 2026 Jan-Jun. Predict using only 2025 matching calendar months;
    # no calibration on test months and no claim of outperforming the baseline.
    actual=[x['units'] for x in monthly[12:18]]
    seasonal=[x['units'] for x in monthly[:6]]
    flat=[sum(x['units'] for x in monthly[9:12])/3]*6
    backtest=dict(period='Jan-Jun 2026 holdout; training ends Dec 2025',seasonal_wape=wape(actual,seasonal),trailing_mean_wape=wape(actual,flat),actual_units=actual,seasonal_prediction=seasonal,trailing_prediction=flat)
    result=dict(seed=SEED,source='Entirely synthetic retailer; no Amazon internal data',orders=len(orders),segments=len(segments),actuals=monthly,segment_actuals=segments,budget=plan,bridge=br,forecasts=forecasts,backtest=backtest,assumptions=dict(cases=CASES,tax_rate=.25,depreciation=18000,monthly_capex=25000,receivable_days=2,opening_cash=900000))
    (out/'analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    dump(out/'monthly_actuals.csv',monthly); dump(out/'segment_actuals.csv',segments)
    for c,rows in forecasts.items(): dump(out/f'forecast_{c.lower()}.csv',rows)
    db.close()
    base=forecasts['Base']; down=forecasts['Downside']
    memo=f'''# Retail finance review\n\nSynthetic case as of June 30, 2026. All amounts USD.\n\n## Decision\nPrioritize unit-cost management and working-capital discipline before committing to the upside demand case.\n\n## Evidence\n- {len(orders):,} order records, {len(segments)} segment-months, three regions and three categories.\n- Actual EBITDA less budget: ${br['actual']-br['budget']:,.0f}. Largest bridge driver: {max(br['effects'],key=lambda k:abs(br['effects'][k]))}.\n- Base twelve-month revenue: ${sum(x['revenue'] for x in base):,.0f}; EBITDA: ${sum(x['ebitda'] for x in base):,.0f}.\n- Base ending cash: ${base[-1]['ending_cash']:,.0f}; downside ending cash: ${down[-1]['ending_cash']:,.0f}. No financing plug is applied.\n- Holdout seasonal WAPE: {backtest['seasonal_wape']:.1%}; trailing-mean benchmark: {backtest['trailing_mean_wape']:.1%}. This synthetic result does not establish real-world forecasting accuracy.\n\n## Proposed actions\nOperations: investigate fulfillment unit costs before next monthly review. Commercial: validate price elasticity before a price increase. Treasury: evaluate inventory days and supplier terms together. Finance: rerun all cases after replacing assumptions with approved inputs. These are proposed case-study actions, not stakeholder approvals.\n\n## Accounting and model boundaries\nNet price includes modeled discounts/returns. Inventory/AP use merchandise COGS only; fulfillment is expensed separately within variable costs. This is an operating cash forecast, not a full GAAP balance sheet. Sales tax, debt, financing, deferred tax, and opening fixed-asset rollforwards are excluded. Cash flow deducts capex and working capital, adds back noncash depreciation through EBITDA, and taxes only positive EBIT. Opening AR/inventory/AP use stated 30-day proxies; forecast uses actual calendar days.\n'''
    (out/'management_memo.md').write_text(memo,encoding='utf-8')
    print(json.dumps(dict(orders=len(orders),segments=len(segments),bridge_residual=br['residual'],base_revenue=sum(x['revenue'] for x in base),base_ebitda=sum(x['ebitda'] for x in base),base_ending_cash=base[-1]['ending_cash'],backtest=backtest),indent=2))
    return result

if __name__=='__main__': build()
