-- =====================================================================
-- BFB321 Inventory - sample data (loaded by init_db.py only when the
-- products table is empty, so you never get duplicates).
-- Order dates use DATE_SUB(NOW(), ...) so the dashboard always shows
-- recent activity, whenever you run this.
-- =====================================================================

-- ids: 1 Electronics, 2 Furniture, 3 Accessories, 4 Warehouse Equipment
INSERT INTO categories (name) VALUES
    ('Electronics'), ('Furniture'), ('Accessories'), ('Warehouse Equipment');

-- Status is CALCULATED from stock and reorder_level (see models.stock_status):
--   Monitor 27      12 <= 15        -> Restock
--   Office Chair    26 <= 15 * 2    -> Low stock
--   USB-C Hub        0              -> Out of stock
INSERT INTO products (name, category_id, stock, reorder_level, price) VALUES
    ('BFB321',               1,  84, 20, 1250.00),
    ('Office Chair',         2,  26, 15,  320.00),
    ('Wireless Mouse',       3, 200, 40,   42.00),
    ('Monitor 27',           1,  12, 15,  610.00),
    ('Standing Desk',        2,  14,  5,  899.00),
    ('USB-C Hub',            3,   0, 10,   65.00),
    ('Pallet Jack',          4,   9,  3, 2400.00),
    ('Mechanical Keyboard',  3,  55, 20,  120.00),
    ('Laptop Stand',         3,  34, 15,   49.00),
    ('Barcode Scanner',      4,  18, 10,  185.00);

INSERT INTO clients (name, email, company, active) VALUES
    ('Thabo Mokoena',  'thabo@techhub.co.za',      'TechHub Retail',        1),
    ('Lerato Dlamini', 'lerato@homestyle.co.za',   'HomeStyle Furnishings', 1),
    ('Priya Naidoo',   'priya@capelogistics.co.za','Cape Logistics',        1),
    ('Johan van Wyk',  'johan@vwengineering.co.za','VW Engineering',        1),
    ('Sipho Ndlovu',   'sipho@ndlovutrading.co.za','Ndlovu Trading',        1),
    ('Anel Botha',     'anel@bothaoffice.co.za',   'Botha Office Supplies', 1),
    ('Kevin Pillay',   'kevin@pillaygroup.co.za',  NULL,                    0);

-- 30 orders over about 6 months. unit_price = the price at that moment.
INSERT INTO orders (client_id, product_id, quantity, unit_price, ordered_at) VALUES
    (1, 1,  3, 1250.00, DATE_SUB(NOW(), INTERVAL 2 DAY)),
    (2, 2,  4,  320.00, DATE_SUB(NOW(), INTERVAL 4 DAY)),
    (3, 3, 25,   42.00, DATE_SUB(NOW(), INTERVAL 6 DAY)),
    (4, 4,  2,  610.00, DATE_SUB(NOW(), INTERVAL 9 DAY)),
    (1, 8,  6,  120.00, DATE_SUB(NOW(), INTERVAL 12 DAY)),
    (5, 10, 2,  185.00, DATE_SUB(NOW(), INTERVAL 15 DAY)),
    (3, 1,  2, 1250.00, DATE_SUB(NOW(), INTERVAL 19 DAY)),
    (6, 9, 10,   49.00, DATE_SUB(NOW(), INTERVAL 24 DAY)),
    (2, 5,  1,  899.00, DATE_SUB(NOW(), INTERVAL 28 DAY)),
    (4, 1,  2, 1250.00, DATE_SUB(NOW(), INTERVAL 33 DAY)),
    (1, 3, 30,   42.00, DATE_SUB(NOW(), INTERVAL 38 DAY)),
    (5, 4,  3,  610.00, DATE_SUB(NOW(), INTERVAL 44 DAY)),
    (6, 6, 12,   65.00, DATE_SUB(NOW(), INTERVAL 51 DAY)),
    (3, 2,  6,  320.00, DATE_SUB(NOW(), INTERVAL 57 DAY)),
    (7, 1,  1, 1200.00, DATE_SUB(NOW(), INTERVAL 63 DAY)),
    (2, 8,  5,  120.00, DATE_SUB(NOW(), INTERVAL 70 DAY)),
    (1, 4,  2,  590.00, DATE_SUB(NOW(), INTERVAL 78 DAY)),
    (5, 1,  4, 1200.00, DATE_SUB(NOW(), INTERVAL 86 DAY)),
    (4, 10, 3,  185.00, DATE_SUB(NOW(), INTERVAL 93 DAY)),
    (6, 3, 40,   40.00, DATE_SUB(NOW(), INTERVAL 101 DAY)),
    (3, 5,  2,  899.00, DATE_SUB(NOW(), INTERVAL 108 DAY)),
    (7, 6, 15,   65.00, DATE_SUB(NOW(), INTERVAL 116 DAY)),
    (1, 1,  2, 1200.00, DATE_SUB(NOW(), INTERVAL 124 DAY)),
    (2, 9,  8,   49.00, DATE_SUB(NOW(), INTERVAL 131 DAY)),
    (5, 2,  5,  310.00, DATE_SUB(NOW(), INTERVAL 139 DAY)),
    (4, 4,  1,  590.00, DATE_SUB(NOW(), INTERVAL 146 DAY)),
    (6, 8,  4,  115.00, DATE_SUB(NOW(), INTERVAL 154 DAY)),
    (3, 1,  3, 1200.00, DATE_SUB(NOW(), INTERVAL 161 DAY)),
    (1, 3, 20,   40.00, DATE_SUB(NOW(), INTERVAL 167 DAY)),
    (2, 10, 1,  180.00, DATE_SUB(NOW(), INTERVAL 172 DAY));
