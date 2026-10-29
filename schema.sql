-- =====================================================================
-- BFB321 Inventory - MySQL schema (run with: python init_db.py)
--   categories  -> one row per category, stored once
--   products    -> what we sell, each product points to one category
--   clients     -> who buys
--   orders      -> what was bought (links clients and products)
-- CREATE TABLE IF NOT EXISTS makes this file safe to run more than once.
-- =====================================================================

CREATE TABLE IF NOT EXISTS categories (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(120)  NOT NULL,
    category_id    INT           NOT NULL,
    stock          INT           NOT NULL DEFAULT 0,
    reorder_level  INT           NOT NULL DEFAULT 10,
    price          DECIMAL(10,2) NOT NULL,
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories (id),
    CONSTRAINT chk_products_stock   CHECK (stock >= 0),
    CONSTRAINT chk_products_reorder CHECK (reorder_level >= 0),
    CONSTRAINT chk_products_price   CHECK (price >= 0)
);

-- active = 1 or 0. We deactivate clients instead of deleting them.
CREATE TABLE IF NOT EXISTS clients (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    email       VARCHAR(160) NOT NULL UNIQUE,
    company     VARCHAR(160) NULL,
    active      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- unit_price copies the product price AT THE TIME of the order,
-- so changing a price later never rewrites history.
CREATE TABLE IF NOT EXISTS orders (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    client_id   INT           NOT NULL,
    product_id  INT           NOT NULL,
    quantity    INT           NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    ordered_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_client  FOREIGN KEY (client_id)  REFERENCES clients (id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products (id),
    CONSTRAINT chk_orders_quantity CHECK (quantity > 0),
    CONSTRAINT chk_orders_price    CHECK (unit_price >= 0)
);

-- Extra table for the registration exercise (/register and /users pages).
CREATE TABLE IF NOT EXISTS users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    business_name  VARCHAR(150) NOT NULL,
    email          VARCHAR(255) NOT NULL UNIQUE,
    phone          VARCHAR(30)  NOT NULL,
    address        VARCHAR(500) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
