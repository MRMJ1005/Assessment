"""
Example: How to integrate X-Ray SDK into your existing code

This shows how to modify your app.py to use the X-Ray SDK
"""

from xray import XRayContext, get_storage, set_storage, XRayStorage
import os

# 1. Initialize storage (do this once at app startup)
storage_path = os.getenv("XRAY_STORAGE_PATH", "./xray_trails")
xray_storage = XRayStorage(storage_path=storage_path)
set_storage(xray_storage)


def example_integration():
    """
    Example showing how to wrap your existing logic with X-Ray tracking
    """
    
    # 2. Create X-Ray context for each execution
    with XRayContext(metadata={"endpoint": "/related-products"}) as xray:
        
        # Step 1: Track keyword generation
        xray.start_step(
            step_name="keyword_generation",
            inputs={"raw_keywords": "water,bottle"}
        )
        # Your existing logic here
        keyword_list = ["water", "bottle"]
        xray.complete_step(
            outcomes={"generated_keywords": keyword_list},
            reasoning="Keywords extracted from comma-separated input"
        )
        
        # Step 2: Track product search
        xray.start_step(
            step_name="product_search",
            inputs={"keywords": keyword_list}
        )
        # Your existing search logic here
        candidates = [{"id": "1", "name": "Product A"}, {"id": "2", "name": "Product B"}]
        xray.add_candidates(candidates, description="Products from database search")
        xray.complete_step(
            outcomes={"candidates_found": len(candidates)},
            reasoning=f"Found {len(candidates)} candidate products"
        )
        
        # Step 3: Track filtering
        xray.start_step(
            step_name="filter_and_select",
            inputs={"candidate_count": len(candidates), "price": 29.99}
        )
        # Your existing filter logic here
        passed = [candidates[0]]
        rejected = [candidates[1]]
        
        # Record each filter
        xray.add_filter(
            filter_name="rating_threshold",
            filter_config={"min_rating": 3.5},
            passed=[],
            rejected=[],
            reasoning="Filter products with rating >= 3.5"
        )
        
        xray.add_filter(
            filter_name="price_range",
            filter_config={"min_price": 0.75 * 29.99, "max_price": 2 * 29.99},
            passed=passed,
            rejected=rejected,
            reasoning="Filter products within price range"
        )
        
        xray.complete_step(
            outcomes={"passed": len(passed), "rejected": len(rejected)},
            reasoning="Applied filters and selected best match"
        )
        
        # 3. Save the trail
        get_storage().save(xray)
        
        return xray.execution_id


if __name__ == "__main__":
    exec_id = example_integration()
    print(f"Execution ID: {exec_id}")
    
    # Retrieve the trail
    trail = get_storage().get(exec_id)
    print(f"Trail has {trail['total_steps']} steps")

