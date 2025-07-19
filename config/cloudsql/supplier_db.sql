CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Product Suppliers Table (Mapping suppliers to products)
CREATE TABLE product_suppliers (
    supplier_id,
    product_id,
    supply_price DECIMAL(10, 2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (supplier_id, product_id)
);
-- Create trigger for auto-updating last_updated column in product_suppliers
CREATE TRIGGER update_product_suppliers_last_updated BEFORE
UPDATE ON product_suppliers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
-- Insert supplier records
INSERT INTO suppliers (
        supplier_name,
        contact_name,
        phone,
        email,
        address,
        city,
        country
    )
VALUES (
        'ABC Suppliers',
        'John Doe',
        '+1-555-1234',
        'john@abc.com',
        '123 Main St',
        'New York',
        'USA'
    ),
    (
        'Global Distributors',
        'Alice Smith',
        '+44-203-4567',
        'alice@global.com',
        '456 High St',
        'London',
        'UK'
    ),
    (
        'Asian Traders',
        'Raj Kumar',
        '+91-9876543210',
        'raj@asian.com',
        '789 MG Road',
        'Mumbai',
        'India'
    ),
    (
        'Tech Supplies Ltd',
        'Mike Johnson',
        '+1-555-6789',
        'mike@techsupplies.com',
        '987 Elm St',
        'San Francisco',
        'USA'
    ),
    (
        'Euro Parts',
        'Sophie Laurent',
        '+33-123-4567',
        'sophie@europarts.com',
        '32 Rue de Lyon',
        'Paris',
        'France'
    ),
    (
        'Gulf Traders',
        'Omar Al-Farsi',
        '+971-50-1234567',
        'omar@gulftraders.com',
        'Al Maktoum St',
        'Dubai',
        'UAE'
    ),
    (
        'Pacific Imports',
        'Lily Chen',
        '+86-21-98765432',
        'lily@pacificimports.com',
        '456 Nanjing Road',
        'Shanghai',
        'China'
    );
-- Insert product supplier mapping records
INSERT INTO product_suppliers (supplier_id, product_id, supply_price)
VALUES (1, 101, 12.50),
    (1, 102, 15.00),
    (2, 103, 10.75),
    (3, 101, 11.25),
    (3, 104, 9.90),
    (4, 105, 14.30),
    (5, 106, 13.20),
    (6, 107, 16.40),
    (7, 108, 18.75),
    (1, 109, 12.85);