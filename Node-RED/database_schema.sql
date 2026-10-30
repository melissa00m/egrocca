CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE inventory (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    unit_price REAL NOT NULL DEFAULT 0 CHECK(unit_price >= 0),
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    delivery_address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
    total_amount REAL NOT NULL DEFAULT 0,
    payment_status TEXT DEFAULT 'unpaid',
    order_status TEXT DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES inventory(product_id)
);
CREATE TABLE deliveries (
    delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    destination TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    departure_time TEXT,
    arrival_time TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
CREATE TABLE telemetry (
    telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    synced INTEGER DEFAULT 0 CHECK(synced IN (0, 1))
);
CREATE TABLE offline_queue (
    queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    synced INTEGER DEFAULT 0 CHECK(synced IN (0, 1))
);
CREATE TABLE system_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_inventory_supplier
ON inventory(supplier_id);
CREATE INDEX idx_orders_customer
ON orders(customer_id);
CREATE INDEX idx_deliveries_order
ON deliveries(order_id);
CREATE INDEX idx_telemetry_synced
ON telemetry(synced);
CREATE INDEX idx_offline_queue_synced
ON offline_queue(synced);
