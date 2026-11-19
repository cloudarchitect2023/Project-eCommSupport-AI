CREATE TABLE products (
    product_id VARCHAR(40) PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    inventory INTEGER NOT NULL
);

CREATE TABLE customers (
    customer_id VARCHAR(40) PRIMARY KEY,
    display_name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE
);

CREATE TABLE orders (
    order_id VARCHAR(40) PRIMARY KEY,
    customer_id VARCHAR(40) NOT NULL,
    product_id VARCHAR(40) NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX ix_orders_customer_id ON orders(customer_id);
