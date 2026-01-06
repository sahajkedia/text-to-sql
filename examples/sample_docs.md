# Database Documentation

## Business Context

This database supports an e-commerce platform with customer management, product catalog, order processing, and inventory tracking.

## Key Relationships

- Customers place Orders, which contain Order Items
- Each Order Item references a Product
- Inventory tracks stock levels for Products
- Employees process Orders
- Users can have Carts that may convert to Orders

## Common Conventions

- All timestamps are stored in UTC
- Monetary values use DECIMAL(10, 2)
- Soft deletes use a `deleted_at` column where applicable
- Customer segments: 'enterprise', 'small_business', 'individual'
- Order statuses: 'pending', 'processing', 'shipped', 'delivered', 'cancelled'

## Performance Notes

- The `orders.created_at` column is indexed for time-range queries
- Customer lookups by email are optimized
- Use date_trunc() for monthly/weekly aggregations

