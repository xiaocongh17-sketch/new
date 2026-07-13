"""Seed the database with sample data for development."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.database import async_session_factory
from app.infrastructure.persistence.repositories.store_repo import SQLAlchemyStoreRepository
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.infrastructure.persistence.repositories.house_repo import SQLAlchemyHouseRepository
from app.domain.entities.store import Store
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.value_objects.enums import UserRole
from decimal import Decimal


async def seed():
    async with async_session_factory() as session:
        store_repo = SQLAlchemyStoreRepository(session)
        user_repo = SQLAlchemyUserRepository(session)
        house_repo = SQLAlchemyHouseRepository(session)

        # Create store
        store = Store.create(name="示范门店", code="DEMO001", address="无锡市示范路88号")
        store = await store_repo.save(store)
        print(f"Store: {store.name} ({store.id})")

        # Create users
        users = {}
        for wecom_id, name, role in [
            ("admin", "系统管理员", UserRole.ADMIN),
            ("manager01", "张店长", UserRole.STORE_MANAGER),
            ("agent01", "李业务员", UserRole.AGENT),
            ("agent02", "王业务员", UserRole.AGENT),
            ("landlord01", "赵房东", UserRole.LANDLORD),
            ("landlord02", "钱房东", UserRole.LANDLORD),
        ]:
            user = User.create(
                wecom_userid=wecom_id, name=name, role=role, store_id=store.id,
                username=wecom_id, password="123456",
            )
            user = await user_repo.save(user)
            users[wecom_id] = user
            print(f"  User: {name} ({role.value})")

        # Create sample houses
        houses_data = [
            ("融创文旅城", Decimal("89.50"), "3室2厅1卫", Decimal("2800"), "精装", "12/28"),
            ("万科城市花园", Decimal("120.00"), "3室2厅2卫", Decimal("3800"), "精装", "8/18"),
            ("绿城玉兰花园", Decimal("95.00"), "2室2厅1卫", Decimal("3200"), "简装", "15/22"),
            ("中海珑玺", Decimal("142.00"), "4室2厅2卫", Decimal("4500"), "豪华", "22/32"),
            ("太湖国际社区", Decimal("75.00"), "2室1厅1卫", Decimal("2200"), "简装", "3/11"),
        ]
        for community, area, room_type, price, decoration, floor in houses_data:
            house = House.create(
                community=community, area=area, room_type=room_type,
                rent_price=price, decoration=decoration, floor_info=floor,
                owner_id=users["landlord01"].id, store_id=store.id,
            )
            await house_repo.save(house)
            print(f"  House: {community} {room_type} {price}元/月")

        await session.commit()
        print("Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed())
