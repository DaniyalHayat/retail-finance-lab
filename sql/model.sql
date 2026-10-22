DROP VIEW IF EXISTS monthly_actuals;
DROP VIEW IF EXISTS segment_actuals;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS budget;
CREATE TABLE orders(order_id TEXT PRIMARY KEY, month TEXT NOT NULL, region TEXT NOT NULL, category TEXT NOT NULL, units INTEGER NOT NULL CHECK(units>0), net_price REAL NOT NULL CHECK(net_price>=0), variable_cost REAL NOT NULL CHECK(variable_cost>=0), merchandise_unit_cost REAL NOT NULL CHECK(merchandise_unit_cost>=0));
CREATE TABLE budget(month TEXT, region TEXT, category TEXT, units REAL, net_price REAL, variable_cost REAL, fixed_cost REAL, PRIMARY KEY(month,region,category));
CREATE VIEW segment_actuals AS SELECT month,region,category,SUM(units) AS units,SUM(units*net_price) AS revenue,SUM(units*variable_cost) AS variable_cost,SUM(units*merchandise_unit_cost) AS merchandise_cost,18000.0*(1.02+0.005*(CAST(substr(month,6,2) AS INTEGER)%3)) AS fixed_cost FROM orders GROUP BY month,region,category;
CREATE VIEW monthly_actuals AS SELECT month,SUM(units) AS units,SUM(revenue) AS revenue,SUM(variable_cost) AS variable_cost,SUM(merchandise_cost) AS merchandise_cost,SUM(fixed_cost) AS fixed_cost,SUM(revenue-variable_cost-fixed_cost) AS ebitda FROM segment_actuals GROUP BY month;
