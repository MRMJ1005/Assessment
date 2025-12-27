from fastapi import FastAPI,HTTPException,Depends,Query
from src.db_prep.db import get_async_session,Table
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List
from sqlalchemy import func,select,or_,and_
app=FastAPI(
    title="Assessment",
    description="api to get competitive search",
    version='0.1.0',
    docs='/docs',
    redoc_url='/redocs'
)

def filter_products(products,price):
    passed = []
    rejected = []
    
    for p in products:
        if p.rating is not None and p.rating < 3.5:
            rejected.append({
                "id": str(p.id),
                # "reason": f"Rejected: rating {p.rating} < 3.5"
            })
            continue

        if p.reviews is not None and p.reviews < 100:
            rejected.append({
                "id": str(p.id),
                # "reason": f"Rejected: reviews {p.review} < 100"
            })
            continue
        
        if p.price<0.75*price or p.price>2*price:
            rejected.append({
                "id":p.id,
                "description_product":p.description_product,
                "price":p.price,
                # "reason":"Price not in range"
            })
            continue
        passed.append(p)

    return passed, rejected
    

@app.get('/related-products')
async def get_related_products(keywords:str= Query(..., description="Keywords to search for in products"),
                               price:float=Query(...,description="Price of the product"),
                               session:AsyncSession=Depends(get_async_session)):
    if not keywords:
        raise HTTPException(status_code=400,detail="Atleast one keyword should be provided")
    search_conditons=[]
    keyword_list = [k.strip() for k in keywords.split(',')]
    for keyword in keyword_list:
        keyword_pattern=f"%{keyword}%"
        search_conditons.append(
            func.lower(Table.description_product).like(func.lower(keyword_pattern))
        )
        
    query=select(Table).where(and_(*search_conditons))
    result=await session.execute(query)
    
    products=result.scalars().all()
    passed,rejected=filter_products(products,price)
    return {
        "step":"product_search",
        "input":{
            "keywords":keywords
            },
        "output":{
            "count":len(products),
            "product":products,
            "passed":passed,
            "rejected":rejected
        }
        
    }
    



