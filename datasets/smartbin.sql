-- Specify the schema when dropping the table
DROP TABLE IF EXISTS smartbin.mockdata;

-- Create table in the 'smartbin_data' schema
CREATE TABLE smartbin.mockdata (
    bin_id VARCHAR(10) PRIMARY KEY,  -- Changed bin_id to VARCHAR(10)
    latitude NUMERIC(12,8),
    longitude NUMERIC(12,8),
    collection_frequency_per_month INT,
    average_collection_time_days INT,
    tilt_status VARCHAR(20),
    fill_level_percentage DECIMAL(5,2),
    temperature_celsius DECIMAL(5,2),
    displacement VARCHAR(20),
    days_since_last_emptied INT,
    communication_status VARCHAR(20),
    battery_level_percentage DECIMAL(4,2)
);

-- Insert data with bin_id as '1' to '10'
INSERT INTO smartbin.mockdata (
    bin_id, latitude, longitude, collection_frequency_per_month, average_collection_time_days, 
    tilt_status, fill_level_percentage, temperature_celsius, displacement, 
    days_since_last_emptied, communication_status, battery_level_percentage
) VALUES
('1', -31.977812347421, 115.816781085037, 10, 3, 'Not Tilted', 3.20, 28.6, 'Not Displaced', 3, 'Connected', 74.00),
('2', -31.979226039519, 115.817843840388, 14, 2, 'Not Tilted', 16.20, 24.7, 'Displaced', 2, 'Connected', 77.00),
('3', -31.980276215358, 115.819028679182, 7, 4, 'Not Tilted', 61.60, 28.2, 'Not Displaced', 4, 'Connected', 80.00),
('4', -31.980789710659, 115.815956300412, 10, 3, 'Not Tilted', 22.50, 29.0, 'Not Displaced', 3, 'Connected', 76.00),
('5', -31.983955156070, 115.818708147926, 8, 4, 'Not Tilted', 20.40, 29.7, 'Not Displaced', 3, 'Connected', 78.00),
('6', -31.985110981622, 115.819793755005, 15, 2, 'Tilted', 83.40, 24.3, 'Not Displaced', 2, 'Connected', 77.00),
('7', -31.981733270195, 115.819140203677, 9, 3, 'Not Tilted', 56.40, 24.3, 'Not Displaced', 3, 'Connected', 74.00),
('8', -31.977791373953, 115.818810169397, 3, 10, 'Not Tilted', 5.20, 28.3, 'Not Displaced', 10, 'Connected', 75.00),
('9', -31.976295100794, 115.81966926, 9, 3, 'Not Tilted', 30.20, 24.9, 'Not Displaced', 3, 'Connected', 81.00),
('10', -31.982761823075, 115.819669259596, 4, 8, 'Not Tilted', 90.60, 30.0, 'Not Displaced', 8, 'Connected', 80.00);