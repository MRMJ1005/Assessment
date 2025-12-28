from fastapi import FastAPI,HTTPException,Depends,Query
from src.db_prep.db import get_async_session,Table
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List
from sqlalchemy import func,select,or_,and_
from xray import XRayContext, get_storage, set_storage, XRayStorage
import os

app=FastAPI(
    title="Assessment",
    description="api to get competitive search",
    version='0.1.0',
    docs='/docs',
    redoc_url='/redocs'
)

storage_path = os.getenv("XRAY_STORAGE_PATH", "./xray_trails")
xray_storage = XRayStorage(storage_path=storage_path)
set_storage(xray_storage)

# def filter_products(products,price):
#     passed = []
#     rejected = []
    
#     for p in products:
#         if p.rating is not None and p.rating < 3.5:
#             rejected.append({
#                 "id": str(p.id),
#                 # "reason": f"Rejected: rating {p.rating} < 3.5"
#             })
#             continue

#         if p.reviews is not None and p.reviews < 100:
#             rejected.append({
#                 "id": str(p.id),
#                 # "reason": f"Rejected: reviews {p.review} < 100"
#             })
#             continue
        
#         if p.price<0.75*price or p.price>2*price:
#             rejected.append({
#                 "id":p.id,
#                 "description_product":p.description_product,
#                 "price":p.price,
#                 # "reason":"Price not in range"
#             })
#             continue
#         passed.append(p)

#     return passed, rejected

def filter_products(products, price, xray=None):
    passed = []
    rejected = []
    
    rating_rejected = []
    review_rejected = []
    price_rejected = []
    
    for p in products:
        if p.rating is not None and p.rating < 3.5:
            rating_rejected.append({"id": str(p.id), "rating": p.rating})
            rejected.append({"id": str(p.id)})
            continue

        if p.reviews is not None and p.reviews < 100:
            review_rejected.append({"id": str(p.id), "reviews": p.reviews})
            rejected.append({"id": str(p.id)})
            continue
        
        if p.price < 0.75*price or p.price > 2*price:
            price_rejected.append({
                "id": p.id,
                "description_product": p.description_product,
                "price": p.price
            })
            rejected.append({
                "id": p.id,
                "description_product": p.description_product,
                "price": p.price
            })
            continue
        passed.append(p)
    
    # Track individual filters if xray is provided
    if xray:
        if rating_rejected:
            xray.add_filter(
                filter_name="rating_threshold",
                filter_config={"min_rating": 3.5},
                passed=[],
                rejected=rating_rejected,
                reasoning="Products with rating < 3.5 are excluded"
            )
        
        if review_rejected:
            xray.add_filter(
                filter_name="review_count_threshold",
                filter_config={"min_reviews": 100},
                passed=[],
                rejected=review_rejected,
                reasoning="Products with < 100 reviews are excluded"
            )
        
        if price_rejected:
            xray.add_filter(
                filter_name="price_range",
                filter_config={"min_price": 0.75 * price, "max_price": 2 * price},
                passed=[],
                rejected=price_rejected,
                reasoning=f"Products outside price range [0.75x, 2x] of {price} are excluded"
            )

    return passed, rejected

@app.get('/related-products')
async def get_related_products(keywords:str= Query(..., description="Keywords to search for in products"),
                               price:float=Query(...,description="Price of the product"),
                               session:AsyncSession=Depends(get_async_session)):
    if not keywords:
        raise HTTPException(status_code=400,detail="Atleast one keyword should be provided")
    # Create X-Ray context for this execution
    with XRayContext(metadata={"endpoint": "/related-products", "keywords": keywords, "price": price}) as xray:
        
        # Step 1: Keyword Processing
        xray.start_step(
            step_name="keyword_processing",
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
            inputs={"keywords": keyword_list}
        )
        
        search_conditons = []
        for keyword in keyword_list:
            keyword_pattern = f"%{keyword}%"
            search_conditons.append(
                func.lower(Table.description_product).like(func.lower(keyword_pattern))
            )
        
        query = select(Table).where(and_(*search_conditons))
        result = await session.execute(query)
        products = result.scalars().all()
        
        # Record candidates found
        product_dicts = [
            {
                "id": str(p.id),
                "description": p.description_product,
                "price": p.price,
                "rating": p.rating,
                "reviews": p.reviews
            }
            for p in products
        ]
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
        
        passed, rejected = filter_products(products, price)
        
        # Track individual filters (you'll need to modify filter_products or track here)
        # For now, let's track the overall filtering result
        xray.add_filter(
            filter_name="combined_filters",
            filter_config={
                "min_rating": 3.5,
                "min_reviews": 100,
                "price_range": [0.75 * price, 2 * price]
            },
            passed=[{"id": str(p.id), "price": p.price, "rating": p.rating} for p in passed],
            rejected=rejected,
            reasoning="Applied rating, review count, and price range filters"
        )
        
        xray.complete_step(
            outcomes={
                "passed_count": len(passed),
                "rejected_count": len(rejected),
                "final_products": len(passed)
            },
            reasoning=f"Filtered {len(products)} candidates down to {len(passed)} products"
        )
        
        # Save the trail
        get_storage().save(xray)
        
        return {
            "execution_id": xray.execution_id,
            "step": "product_search",
            "input": {
                "keywords": keywords
            },
            "output": {
                "count": len(products),
                "product": products,
                "passed": passed,
                "rejected": rejected
            },
            "xray_trail_url": f"/xray/trail/{xray.execution_id}"
        }
    



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