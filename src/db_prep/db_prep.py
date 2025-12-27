import uuid
import asyncio
from db import Table, get_async_session,create_db_and_tables

dummy_data = [
    {"text": "Stainless steel insulated water bottle 32oz with vacuum seal, keeps drinks cold for 24 hours", "price": 29.99, "rating": 4.4, "review": 1247},
    {"text": "Plastic reusable water bottle 1 liter, lightweight and BPA free", "price": 9.99, "rating": 3.6, "review": 213},
    {"text": "Premium insulated steel water bottle 26oz with wide mouth and leak proof lid", "price": 34.99, "rating": 4.6, "review": 5632},
    {"text": "Water bottle cleaning brush set with long handle and sponge tip", "price": 7.49, "rating": 4.5, "review": 3421},
    {"text": "Glass water bottle with silicone sleeve 20oz, eco friendly design", "price": 18.99, "rating": 4.1, "review": 879},
    {"text": "Insulated stainless steel sports bottle 40oz for hiking and outdoor activities", "price": 39.99, "rating": 4.7, "review": 8124},
    {"text": "Replacement lid compatible with insulated stainless steel water bottles", "price": 6.99, "rating": 4.3, "review": 1543},
    {"text": "Collapsible silicone water bottle 500ml, travel friendly and foldable", "price": 14.99, "rating": 3.9, "review": 468},
    {"text": "Budget stainless steel water bottle 32oz, single wall, not insulated", "price": 12.99, "rating": 3.4, "review": 97},
    {"text": "High-end insulated water bottle 32oz with temperature display on lid", "price": 49.99, "rating": 4.8, "review": 2319},

    {"text": "Vacuum insulated travel water bottle 20oz with flip top lid", "price": 24.99, "rating": 4.2, "review": 1043},
    {"text": "Kids water bottle with straw lid and cartoon design", "price": 11.99, "rating": 4.0, "review": 658},
    {"text": "Copper coated insulated water bottle for long temperature retention", "price": 44.99, "rating": 4.6, "review": 2917},
    {"text": "Lightweight aluminum water bottle for gym and fitness", "price": 13.49, "rating": 3.7, "review": 412},
    {"text": "Water bottle carrier bag with adjustable shoulder strap", "price": 10.99, "rating": 4.4, "review": 1854},
    {"text": "Insulated stainless steel flask 500ml for hot and cold beverages", "price": 22.99, "rating": 4.3, "review": 1987},
    {"text": "Large capacity insulated water jug 1 gallon for workouts", "price": 59.99, "rating": 4.5, "review": 3204},
    {"text": "Slim metal water bottle 18oz suitable for car cup holders", "price": 16.99, "rating": 4.1, "review": 732},
    {"text": "Reusable plastic water bottle with measurement markings", "price": 8.99, "rating": 3.5, "review": 289},
    {"text": "Insulated water bottle with sports cap and carry loop", "price": 27.99, "rating": 4.4, "review": 2465},

    {"text": "Eco friendly bamboo insulated water bottle with steel interior", "price": 42.99, "rating": 4.6, "review": 1456},
    {"text": "Metal water bottle gift set with extra lids and brushes", "price": 31.99, "rating": 4.2, "review": 1134},
    {"text": "Thermal water bottle 750ml with scratch resistant coating", "price": 28.49, "rating": 4.3, "review": 1623},
    {"text": "Plastic squeeze water bottle for cycling and sports", "price": 6.99, "rating": 3.3, "review": 188},
    {"text": "Insulated water bottle with cup lid for office use", "price": 35.99, "rating": 4.5, "review": 2741},
    {"text": "Steel water bottle with powder coated matte finish", "price": 19.99, "rating": 4.0, "review": 901},
    {"text": "Wide mouth insulated bottle compatible with ice cubes", "price": 33.99, "rating": 4.6, "review": 3894},
    {"text": "Thermos style insulated flask 1 liter capacity", "price": 41.99, "rating": 4.7, "review": 5201},
    {"text": "Minimalist stainless steel water bottle 500ml", "price": 15.49, "rating": 3.8, "review": 367},
    {"text": "Heavy duty insulated bottle for camping and trekking", "price": 54.99, "rating": 4.8, "review": 6023},

    {"text": "Insulated bottle with detachable tea infuser", "price": 26.99, "rating": 4.2, "review": 1254},
    {"text": "Smart water bottle with hydration reminder LED", "price": 64.99, "rating": 4.1, "review": 948},
    {"text": "Stainless steel water bottle with classic screw cap", "price": 17.99, "rating": 3.9, "review": 621},
    {"text": "Vacuum insulated bottle designed for hot coffee", "price": 29.49, "rating": 4.4, "review": 1843},
    {"text": "Sports water bottle with locking flip lid and straw", "price": 21.99, "rating": 4.3, "review": 2139},
    {"text": "Ultra lightweight titanium water bottle for backpacking", "price": 89.99, "rating": 4.7, "review": 734},
    {"text": "Insulated bottle with anti slip rubber base", "price": 23.99, "rating": 4.2, "review": 1165},
    {"text": "Classic thermos vacuum bottle 750ml", "price": 38.99, "rating": 4.6, "review": 4987},
    {"text": "Economy metal water bottle without insulation", "price": 10.49, "rating": 3.2, "review": 154},
    {"text": "Luxury insulated water bottle with leather sleeve", "price": 79.99, "rating": 4.8, "review": 1289}
]


async def get_db_ready(data):
    async for session in get_async_session():
        for item in data:
            post = Table(
                id=uuid.uuid4(),
                description_product=item["text"],
                price=item["price"],
                rating=item["rating"],
                reviews=item["review"]
            )
            session.add(post)

        await session.commit()

    return True

async def main():
    await create_db_and_tables()   
    await get_db_ready(dummy_data)


if __name__ == "__main__":
    asyncio.run(main())
