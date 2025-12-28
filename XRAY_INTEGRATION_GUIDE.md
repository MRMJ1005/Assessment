# X-Ray SDK Integration Guide

## Overview
The X-Ray SDK is a lightweight wrapper that captures decision context at each step of your multi-step process. It tracks:
- **Inputs**: What data went into each step
- **Candidates**: What options were considered
- **Filters**: What filters were applied and their results
- **Outcomes**: What came out of each step
- **Reasoning**: Why decisions were made

## Quick Start

### 1. Import the SDK
```python
from xray import XRayContext, get_storage, set_storage, XRayStorage
import os
```

### 2. Initialize Storage (once at app startup)
```python
# In your app.py, add this after creating the FastAPI app
storage_path = os.getenv("XRAY_STORAGE_PATH", "./xray_trails")
xray_storage = XRayStorage(storage_path=storage_path)
set_storage(xray_storage)
```

### 3. Wrap Your Logic with X-Ray Context

Here's how to modify your `/related-products` endpoint:

```python
@app.get('/related-products')
async def get_related_products(
    keywords: str = Query(..., description="Keywords to search for in products"),
    price: float = Query(..., description="Price of the product"),
    session: AsyncSession = Depends(get_async_session)
):
    if not keywords:
        raise HTTPException(status_code=400, detail="At least one keyword should be provided")
    
    # Create X-Ray context for this execution
    with XRayContext(metadata={"endpoint": "/related-products", "keywords": keywords, "price": price}) as xray:
        
        # Step 1: Keyword Generation
        xray.start_step(
            step_name="keyword_generation",
            inputs={"raw_keywords": keywords, "price": price}
        )
        keyword_list = [k.strip() for k in keywords.split(',')]
        xray.complete_step(
            outcomes={"generated_keywords": keyword_list, "keyword_count": len(keyword_list)},
            reasoning="Keywords extracted from comma-separated input string"
        )
        
        # Step 2: Product Search
        xray.start_step(
            step_name="product_search",
            inputs={"keywords": keyword_list, "search_type": "database_query"}
        )
        
        search_conditions = []
        for keyword in keyword_list:
            keyword_pattern = f"%{keyword}%"
            search_conditions.append(
                func.lower(Table.description_product).like(func.lower(keyword_pattern))
            )
        
        query = select(Table).where(and_(*search_conditions))
        result = await session.execute(query)
        products = result.scalars().all()
        
        # Convert products to dicts for X-Ray
        product_dicts = [{"id": str(p.id), "description": p.description_product, 
                         "price": p.price, "rating": p.rating, "reviews": p.reviews} 
                        for p in products]
        
        xray.add_candidates(product_dicts, description="Products matching search keywords")
        xray.complete_step(
            outcomes={"candidates_found": len(products)},
            reasoning=f"Database query returned {len(products)} candidate products"
        )
        
        # Step 3: Filtering
        xray.start_step(
            step_name="filter_and_select",
            inputs={
                "candidate_count": len(products),
                "reference_price": price,
                "filter_criteria": {
                    "min_rating": 3.5,
                    "min_reviews": 100,
                    "price_range": [0.75 * price, 2 * price]
                }
            }
        )
        
        # Your existing filter_products function
        passed, rejected = filter_products(products, price)
        
        # Track filters in X-Ray (modify filter_products to accept xray_context)
        # Or track them here after filtering
        xray.add_filter(
            filter_name="rating_threshold",
            filter_config={"min_rating": 3.5},
            passed=[{"id": str(p.id)} for p in passed],
            rejected=[r for r in rejected if "rating" in str(r)],
            reasoning="Products with rating < 3.5 are excluded"
        )
        
        xray.add_filter(
            filter_name="review_count_threshold",
            filter_config={"min_reviews": 100},
            passed=[{"id": str(p.id)} for p in passed],
            rejected=[r for r in rejected if "reviews" in str(r)],
            reasoning="Products with < 100 reviews are excluded"
        )
        
        xray.add_filter(
            filter_name="price_range",
            filter_config={"min_price": 0.75 * price, "max_price": 2 * price},
            passed=[{"id": str(p.id), "price": p.price} for p in passed],
            rejected=[r for r in rejected if "price" in r],
            reasoning=f"Products outside price range [0.75x, 2x] of {price} are excluded"
        )
        
        # Select best match
        best_match = None
        if passed:
            best_match = max(passed, key=lambda p: (p.rating or 0, p.reviews or 0))
        
        xray.complete_step(
            outcomes={
                "passed_count": len(passed),
                "rejected_count": len(rejected),
                "best_match": {"id": str(best_match.id), "price": best_match.price} if best_match else None
            },
            reasoning="Applied all filters and selected best match based on rating and reviews"
        )
        
        # Save the trail
        get_storage().save(xray)
        
        return {
            "execution_id": xray.execution_id,
            "result": {
                "best_match": {"id": str(best_match.id)} if best_match else None,
                "passed_products": len(passed),
                "rejected_count": len(rejected)
            },
            "xray_trail_url": f"/xray/trail/{xray.execution_id}"
        }
```

### 4. Add Endpoints to Retrieve Trails

```python
@app.get('/xray/trail/{execution_id}')
async def get_xray_trail(execution_id: str):
    """Retrieve the complete decision trail for a given execution"""
    storage = get_storage()
    trail = storage.get(execution_id)
    
    if not trail:
        raise HTTPException(status_code=404, detail=f"Trail not found: {execution_id}")
    
    return trail

@app.get('/xray/trails')
async def list_xray_trails(limit: int = Query(10, description="Maximum number of trails")):
    """List all available decision trails"""
    storage = get_storage()
    trails = storage.list_all(limit=limit)
    return {"count": len(trails), "trails": trails}
```

## Key Concepts

### XRayContext
- Use as a context manager (`with XRayContext() as xray:`)
- Tracks one complete execution/decision process
- Automatically generates a unique `execution_id`

### Steps
- Each step represents one decision point in your process
- Use `start_step()` to begin tracking
- Use `complete_step()` to finish tracking
- Add candidates, filters, and outcomes between start and complete

### Storage
- Trails are saved automatically when you call `get_storage().save(xray)`
- Stored in memory and optionally to JSON files
- Can be retrieved later using the `execution_id`

## Best Practices

1. **Start a step before doing work**: Call `start_step()` before the logic
2. **Add candidates early**: Use `add_candidates()` right after getting candidates
3. **Record filters as you apply them**: Use `add_filter()` for each filter
4. **Complete steps with outcomes**: Always call `complete_step()` with outcomes
5. **Save the trail**: Call `get_storage().save(xray)` before returning

## Next Steps

After integrating the SDK:
1. Test your endpoint - it should return an `execution_id`
2. Call `/xray/trail/{execution_id}` to see the decision trail
3. Build a dashboard UI to visualize the trails (see Dashboard UI requirements)

