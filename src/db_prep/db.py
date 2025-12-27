import uuid
from collections.abc import AsyncGenerator
from sqlalchemy import Column,String,Text,Integer,Float
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession ,create_async_engine,async_sessionmaker

DATABASE_URL="sqlite+aiosqlite:///./test.db"

class Base(DeclarativeBase):
    pass

class Table(Base):
    __tablename__ = "product_reviews"  
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    description_product: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float)
    reviews: Mapped[int | None] = mapped_column(Integer)


engine=create_async_engine(DATABASE_URL)
async_session_maker=async_sessionmaker(engine,expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
async def get_async_session()->AsyncGenerator[AsyncSession,None]:
    async with async_session_maker() as session:
        yield session

if __name__=="__main__":
    print("Everything is good")