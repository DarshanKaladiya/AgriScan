CREATE DATABASE IF NOT EXISTS agri_intelligence;
USE agri_intelligence;

-- 1. Master Crops Table (A-Z details)
CREATE TABLE IF NOT EXISTS master_crops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50),
    scientific_name VARCHAR(255),
    growth_duration_days INT,
    best_season ENUM('Kharif', 'Rabi', 'Zaid', 'Perennial'),
    ideal_temperature_range VARCHAR(50),
    best_soil_types TEXT,
    growing_months VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Companies Table
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    website_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Input Products Table (Seeds, Fertilizers, Pesticides)
CREATE TABLE IF NOT EXISTS input_products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category ENUM('Seed', 'Fertilizer', 'Pesticide', 'Herbicide', 'Fungicide', 'Other') NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    brand_id INT,
    technical_name VARCHAR(255), -- Active ingredient
    price DECIMAL(10, 2),
    original_price DECIMAL(10, 2),
    unit_value DECIMAL(10, 2), -- e.g., 500
    unit_measure VARCHAR(20), -- e.g., gm, kg, ml, L
    source_url VARCHAR(500),
    image_url VARCHAR(500),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES companies(id),
    UNIQUE KEY unique_product (category, product_name, brand_id, technical_name)
);

-- 4. Crop Advisories Table (Mapping Crops to technical requirements)
CREATE TABLE IF NOT EXISTS crop_advisories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    growth_stage VARCHAR(100), -- e.g., Sowing, Flowering, Harvest
    requirement_type ENUM('Seed', 'Fertilizer', 'Pesticide'),
    technical_recommendation VARCHAR(255), -- e.g., "Urea", "NPK 19:19:19"
    dosage_per_acre VARCHAR(100),
    notes TEXT,
    FOREIGN KEY (crop_id) REFERENCES master_crops(id)
);

-- 5. Mandi Prices Table
CREATE TABLE IF NOT EXISTS mandi_prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_id INT,
    state VARCHAR(100),
    district VARCHAR(100),
    mandi_name VARCHAR(255),
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    modal_price DECIMAL(10, 2),
    retail_min_price DECIMAL(10, 2),
    retail_max_price DECIMAL(10, 2),
    mall_min_price DECIMAL(10, 2),
    mall_max_price DECIMAL(10, 2),
    units VARCHAR(50),
    price_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (crop_id) REFERENCES master_crops(id),
    UNIQUE KEY unique_mandi_price (mandi_name, crop_id, price_date)
);

-- 6. Seed Master Crops
INSERT INTO master_crops (id, crop_name, category, scientific_name, growth_duration_days, best_season, ideal_temperature_range, best_soil_types, growing_months, description) VALUES
(1, 'Wheat', 'Cereal', 'Triticum aestivum', 120, 'Rabi', '15-25°C', 'Well-drained fertile loamy and clayey loam', 'Nov - Apr', 'Major staple cereal crop widely grown in northern and central India during the winter season.'),
(2, 'Rice', 'Cereal', 'Oryza sativa', 135, 'Kharif', '20-35°C', 'Deep clayey and alluvial soils with water retention', 'Jun - Nov', 'Principal food grain of India, predominantly cultivated in Kharif season with abundant irrigation.'),
(3, 'Cotton', 'Fiber / Cash', 'Gossypium hirsutum', 180, 'Kharif', '21-30°C', 'Deep black cotton soil (Regur) and alluvial soil', 'May - Dec', 'Primary commercial cash crop supporting the textile industry, largely grown in Gujarat, Maharashtra, and Telangana.'),
(4, 'Maize', 'Cereal', 'Zea mays', 100, 'Kharif', '18-27°C', 'Well-drained sandy loam to silty loam', 'Jun - Oct', 'High-yielding multi-purpose grain utilized for food, poultry feed, and industrial starch.'),
(5, 'Potato', 'Tuber / Vegetable', 'Solanum tuberosum', 90, 'Rabi', '15-20°C', 'Loose, friable sandy loam rich in organic matter', 'Oct - Feb', 'Extensively consumed root tuber crop grown across the Indo-Gangetic plains during winter.'),
(6, 'Tomato', 'Vegetable', 'Solanum lycopersicum', 110, 'Zaid', '18-28°C', 'Well-drained sandy loam to clay loam rich in humus', 'Year-round', 'High-value commercial horticultural crop with high demand in fresh and processing markets.'),
(7, 'Onion', 'Bulb / Vegetable', 'Allium cepa', 140, 'Rabi', '13-24°C', 'Well-drained sandy loam with pH 6.5-7.5', 'Nov - May', 'Key horticultural vegetable crop with prominent production belts in Maharashtra, Gujarat, and Karnataka.'),
(8, 'Soybean', 'Oilseed / Legume', 'Glycine max', 105, 'Kharif', '20-30°C', 'Well-drained fertile loam to clay loam', 'Jun - Oct', 'Rich protein and edible oil source grown extensively in Madhya Pradesh and Maharashtra.'),
(9, 'Mustard', 'Oilseed', 'Brassica juncea', 110, 'Rabi', '10-25°C', 'Light to heavy loamy soils with good drainage', 'Oct - Mar', 'Major edible oilseed crop of north-western India requiring dry, cool winter climate.'),
(10, 'Sugarcane', 'Commercial / Sugar', 'Saccharum officinarum', 360, 'Perennial', '20-35°C', 'Deep, rich loamy and alluvial soils', 'Year-round', 'Primary raw material for the sugar and bio-ethanol industries in UP, Maharashtra, and Karnataka.')
ON DUPLICATE KEY UPDATE 
    category=VALUES(category), 
    scientific_name=VALUES(scientific_name), 
    growth_duration_days=VALUES(growth_duration_days), 
    best_season=VALUES(best_season),
    ideal_temperature_range=VALUES(ideal_temperature_range),
    description=VALUES(description);

-- 7. Seed Companies
INSERT INTO companies (id, name, website_url) VALUES
(1, 'Bayer CropScience India', 'https://www.bayer.in'),
(2, 'Syngenta India', 'https://www.syngenta.co.in'),
(3, 'UPL Limited', 'https://www.upl-ltd.com'),
(4, 'IFFCO (Indian Farmers Fertiliser Coop)', 'https://www.iffco.in'),
(5, 'Corteva Agriscience', 'https://www.corteva.in'),
(6, 'Godrej Agrovet', 'https://www.godrejagrovet.com'),
(7, 'PI Industries', 'https://www.piindustries.com')
ON DUPLICATE KEY UPDATE website_url=VALUES(website_url);

-- 8. Seed Input Products
INSERT INTO input_products (category, product_name, brand_id, technical_name, price, original_price, unit_value, unit_measure) VALUES
('Seed', 'HD-2967 High Yield Certified Seed', 4, 'Wheat Certified Seed', 1250.00, 1400.00, 40.00, 'kg'),
('Seed', 'Pusa Basmati 1121 Seed', 4, 'Paddy Basmati Seed', 1850.00, 2100.00, 10.00, 'kg'),
('Seed', 'RCH 659 BG II Bt Cotton Seed', 1, 'Bollgard II Hybrid Cotton', 864.00, 950.00, 450.00, 'gm'),
('Seed', 'Pioneer P3396 Hybrid Maize Seed', 5, 'Hybrid Maize F1', 1950.00, 2200.00, 4.00, 'kg'),
('Fertilizer', 'IFFCO Neem Coated Urea', 4, 'Urea (46% N)', 266.50, 290.00, 45.00, 'kg'),
('Fertilizer', 'IFFCO DAP (Di-Ammonium Phosphate)', 4, 'DAP 18:46:0', 1350.00, 1450.00, 50.00, 'kg'),
('Fertilizer', 'IFFCO NPK 19:19:19 Water Soluble', 4, 'NPK 19:19:19', 180.00, 220.00, 1.00, 'kg'),
('Fertilizer', 'MOP Muriate of Potash', 4, 'Potassium Chloride (60% K2O)', 1700.00, 1850.00, 50.00, 'kg'),
('Pesticide', 'Confidor Super', 1, 'Imidacloprid 30.5% SC', 420.00, 480.00, 100.00, 'ml'),
('Pesticide', 'Coragen Insecticide', 5, 'Chlorantraniliprole 18.5% SC', 1750.00, 1950.00, 150.00, 'ml'),
('Fungicide', 'Saaf Fungicide', 3, 'Carbendazim 12% + Mancozeb 63% WP', 350.00, 410.00, 500.00, 'gm'),
('Herbicide', 'Roundup Speed', 1, 'Glyphosate 41% SL', 580.00, 650.00, 1000.00, 'ml'),
('Pesticide', 'Tata M-45 Contact Fungicide', 3, 'Mancozeb 75% WP', 290.00, 340.00, 500.00, 'gm')
ON DUPLICATE KEY UPDATE price=VALUES(price), original_price=VALUES(original_price);

-- 9. Seed Crop Advisories
INSERT INTO crop_advisories (crop_id, growth_stage, requirement_type, technical_recommendation, dosage_per_acre, notes) VALUES
(1, 'Sowing', 'Seed', 'HD-2967 or PBW-550 certified seeds', '40-45 kg/acre', 'Treat seed with Carbendazim 2g/kg seed before sowing.'),
(1, 'Crown Root Initiation (21 DAS)', 'Fertilizer', 'Urea top dressing + First Irrigation', '30 kg Urea/acre', 'Critical moisture stage; light irrigation essential.'),
(1, 'Tillering', 'Fertilizer', 'NPK 19:19:19 spray for vigor', '1 kg/acre in 150L water', 'Enhances effective tillers and grain weight.'),
(2, 'Transplanting', 'Fertilizer', 'DAP + Zinc Sulphate 21%', '50 kg DAP + 10 kg ZnSO4/acre', 'Apply in puddled field before transplanting.'),
(2, 'Tillering to Panicle Initiation', 'Fertilizer', 'Neem Coated Urea split application', '35 kg Urea/acre', 'Maintain 2-3 cm standing water.'),
(3, 'Square Formation', 'Pesticide', 'Imidacloprid 17.8% SL for sucking pests', '60-80 ml/acre', 'Controls whitefly, aphids, and jassids effectively.'),
(3, 'Boll Development', 'Fertilizer', 'Potassium Nitrate (13:0:45) foliar spray', '1.5 kg/acre', 'Improves boll size, fiber strength, and retention.')
ON DUPLICATE KEY UPDATE technical_recommendation=VALUES(technical_recommendation);

-- 10. Seed Baseline Mandi Prices
INSERT INTO mandi_prices (crop_id, state, district, mandi_name, min_price, max_price, modal_price, price_date) VALUES
(1, 'Punjab', 'Ludhiana', 'Khanna Mandi', 2250.00, 2320.00, 2275.00, CURRENT_DATE),
(1, 'Haryana', 'Karnal', 'Karnal APMC', 2260.00, 2340.00, 2290.00, CURRENT_DATE),
(1, 'Madhya Pradesh', 'Indore', 'Indore Mandi', 2380.00, 2490.00, 2420.00, CURRENT_DATE),
(1, 'Gujarat', 'Rajkot', 'Rajkot APMC', 2450.00, 2580.00, 2510.00, CURRENT_DATE),
(1, 'Rajasthan', 'Kota', 'Kota Mandi', 2310.00, 2400.00, 2350.00, CURRENT_DATE),
(2, 'Haryana', 'Karnal', 'Taraori Mandi', 3700.00, 4050.00, 3850.00, CURRENT_DATE),
(2, 'Punjab', 'Amritsar', 'Amritsar APMC', 3780.00, 4100.00, 3920.00, CURRENT_DATE),
(2, 'Andhra Pradesh', 'Krishna', 'Vijayawada Mandi', 2400.00, 2550.00, 2450.00, CURRENT_DATE),
(3, 'Gujarat', 'Rajkot', 'Rajkot APMC', 7000.00, 7500.00, 7250.00, CURRENT_DATE),
(3, 'Maharashtra', 'Amravati', 'Amravati Mandi', 6950.00, 7400.00, 7180.00, CURRENT_DATE),
(3, 'Telangana', 'Warangal', 'Warangal APMC', 7100.00, 7550.00, 7320.00, CURRENT_DATE),
(4, 'Karnataka', 'Davangere', 'Davangere APMC', 2080.00, 2240.00, 2150.00, CURRENT_DATE),
(4, 'Madhya Pradesh', 'Chhindwara', 'Chhindwara Mandi', 2020.00, 2190.00, 2100.00, CURRENT_DATE),
(5, 'Uttar Pradesh', 'Agra', 'Agra Mandi', 1380.00, 1550.00, 1450.00, CURRENT_DATE),
(5, 'Gujarat', 'Banaskantha', 'Deesa Mandi', 1500.00, 1720.00, 1600.00, CURRENT_DATE),
(6, 'Karnataka', 'Kolar', 'Kolar APMC', 1600.00, 2100.00, 1850.00, CURRENT_DATE),
(6, 'Maharashtra', 'Nashik', 'Nashik Mandi', 1750.00, 2150.00, 1920.00, CURRENT_DATE),
(7, 'Maharashtra', 'Nashik', 'Lasalgaon APMC', 1950.00, 2600.00, 2250.00, CURRENT_DATE),
(7, 'Gujarat', 'Bhavnagar', 'Mahuva Mandi', 1850.00, 2400.00, 2100.00, CURRENT_DATE),
(8, 'Madhya Pradesh', 'Indore', 'Indore Mandi', 4500.00, 4820.00, 4650.00, CURRENT_DATE),
(8, 'Maharashtra', 'Latur', 'Latur APMC', 4580.00, 4890.00, 4720.00, CURRENT_DATE),
(9, 'Rajasthan', 'Bharatpur', 'Bharatpur Mandi', 5300.00, 5600.00, 5450.00, CURRENT_DATE),
(9, 'Haryana', 'Hisar', 'Hisar Mandi', 5250.00, 5550.00, 5400.00, CURRENT_DATE)
ON DUPLICATE KEY UPDATE modal_price=VALUES(modal_price), min_price=VALUES(min_price), max_price=VALUES(max_price);

