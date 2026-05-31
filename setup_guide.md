# Database Setup Guide

## Step 1: Install MySQL
Make sure MySQL is installed and running on your computer.

## Step 2: Open MySQL command line
```bash
mysql -u root -p
```

## Step 3: Run the schema file
```bash
source /path/to/tourist_recommender/database/schema.sql
```

## Step 4: Run the data file
```bash
source /path/to/tourist_recommender/database/destinations_data.sql
```

## Step 5: Verify data loaded
```sql
USE tourist_recommender;
SELECT COUNT(*) FROM destinations;
-- Should return 116
SELECT place_name, state, budget_category, rating FROM destinations LIMIT 10;
```

## Step 6: Update database.py
In database.py, update these lines:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',           # Your MySQL username
    'password': 'YOUR_PASSWORD',  # Your MySQL password
    'database': 'tourist_recommender',
}
```

## Step 7: Install Python packages
```bash
pip install -r requirements.txt
```

## Step 8: Run the app
```bash
python app.py
```
Open browser: http://localhost:5000
