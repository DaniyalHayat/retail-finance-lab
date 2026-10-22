import copy, math, sqlite3, unittest
import finance as f

class FinanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.r=f.build()
    def test_order_count(self): self.assertEqual(self.r['orders'],3240)
    def test_segment_count(self): self.assertEqual(len(self.r['segment_actuals']),162)
    def test_periods(self): self.assertEqual(len(self.r['actuals']),18)
    def test_bridge_reconciles(self): self.assertAlmostEqual(self.r['bridge']['residual'],0,places=6)
    def test_known_bridge(self):
        z=f.bridge({'a':(10,20,8)},{'a':(12,21,9)},10,12)
        self.assertEqual(z['effects'],{'Volume':24,'Mix':0,'Price':12,'Variable cost':-12,'Fixed cost':-2})
        self.assertEqual(z['residual'],0)
    def test_mix(self):
        z=f.bridge({'a':(5,20,10),'b':(5,10,8)},{'a':(8,20,10),'b':(2,10,8)},0,0)
        self.assertEqual(z['effects']['Mix'],24)
    def test_bridge_missing_segments(self):
        with self.assertRaises(ValueError): f.bridge({'a':(1,1,1)},{},0,0)
    def test_bridge_zero_base(self):
        with self.assertRaises(ValueError): f.bridge({'a':(0,1,1)},{'a':(1,1,1)},0,0)
    def test_cash_rollforward(self):
        for rows in self.r['forecasts'].values():
            for i,x in enumerate(rows):
                self.assertAlmostEqual(x['ending_cash'],x['opening_cash']+x['free_cash_flow'])
                if i:self.assertEqual(x['opening_cash'],rows[i-1]['ending_cash'])
    def test_tax_floor(self):
        for rows in self.r['forecasts'].values():
            for x in rows:self.assertAlmostEqual(x['taxes'],max(0,x['ebit'])*.25)
    def test_fcf_equation(self):
        for rows in self.r['forecasts'].values():
            for x in rows:self.assertAlmostEqual(x['free_cash_flow'],x['ebit']-x['taxes']+x['depreciation']-x['change_nwc']-x['capex'])
    def test_case_horizon(self):
        for rows in self.r['forecasts'].values():
            self.assertEqual(len(rows),12);self.assertEqual(rows[0]['month'],'2026-07');self.assertEqual(rows[-1]['month'],'2027-06')
    def test_downside_ebitda(self): self.assertLess(sum(x['ebitda'] for x in self.r['forecasts']['Downside']),sum(x['ebitda'] for x in self.r['forecasts']['Base']))
    def test_actuals_immutable(self):
        h=copy.deepcopy(self.r['actuals']);f.forecast(h,'Upside');self.assertEqual(h,self.r['actuals'])
    def test_sql_source_tie(self):
        con=sqlite3.connect(f.ROOT/'outputs/retail.sqlite')
        total=con.execute('SELECT SUM(units*net_price) FROM orders').fetchone()[0]; con.close()
        self.assertAlmostEqual(total,sum(x['revenue'] for x in self.r['actuals']),places=5)
    def test_duplicate_rejected(self):
        c=sqlite3.connect(':memory:');c.executescript((f.ROOT/'sql/model.sql').read_text());c.execute("INSERT INTO orders VALUES('a','2025-01','East','Home',1,5,3,2)")
        with self.assertRaises(sqlite3.IntegrityError):c.execute("INSERT INTO orders VALUES('a','2025-01','East','Home',1,5,3,2)")
        c.close()
    def test_wape_zero(self):self.assertIsNone(f.wape([0,0],[1,1]))
    def test_wape_known(self):self.assertEqual(f.wape([100,100],[90,110]),.1)
    def test_wape_bad_shape(self):
        with self.assertRaises(ValueError): f.wape([1],[])
    def test_unknown_case(self):
        with self.assertRaises(ValueError): f.forecast(self.r['actuals'],'Other')
    def test_backtest_no_test_inputs(self):self.assertEqual(self.r['backtest']['seasonal_prediction'],[x['units'] for x in self.r['actuals'][:6]])
    def test_deterministic(self):self.assertEqual(f.generate(),f.generate())

if __name__=='__main__':unittest.main()
