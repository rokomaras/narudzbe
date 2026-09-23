import asyncio

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.product import Product
from app.models.user import User
from app.repositories import user_repo
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services import order_service

PRODUCTS = [
    ("Nike Air Max 90", "Klasične tenisice, bijela/crna kombinacija", 12999, 12),
    ("Nike Air Force 1 '07", "Ikonske bijele tenisice, kožno gornjište", 11999, 18),
    ("Adidas Superstar", "Ikonske tenisice s gumenom kapicom", 9999, 15),
    ("Adidas Spezial", "Retro dizajn, semiš gornjište", 10999, 8),
    ("Converse Chuck Taylor All Star", "Platnene tenisice, visoki model", 6499, 20),
    ("New Balance 9060", "Chunky silueta, \"dad shoe\" stil", 15999, 10),
    ("New Balance 530", "Minimalistički retro dizajn, popularne boje", 11999, 14),
    ("Nike Dunk Low", "Kultni model, više kolorita", 11999, 9),
    ("Vezice za tenisice (par)", "Pamučne vezice, više boja", 499, 50),
    ("Uložak za tenisice", "Ortopedski uložak, univerzalna veličina", 1299, 30),
    ("Sredstvo za čišćenje tenisica", "Pjena za sve vrste materijala, 250 ml", 999, 25),
    ("Četkica za tenisice", "Meka četkica za detaljno čišćenje", 699, 40),
    ("Impregnacijski sprej", "Zaštita od vode i prljavštine, 200 ml", 1199, 18),
    ("Kutija za odlaganje tenisica", "Prozirna plastična kutija za pohranu", 799, 0),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        if await user_repo.get_by_username(db, "admin"):
            print("Seed preskočen: podaci već postoje.")
            return

        admin = User(
            username="admin",
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            full_name="Administrator",
            email="admin@example.com",
        )
        roko = User(
            username="roko",
            password_hash=hash_password("roko123"),
            role="customer",
            full_name="Roko Maraš",
            email="roko@example.com",
        )
        kupac2 = User(
            username="kupac2",
            password_hash=hash_password("kupac123"),
            role="customer",
            full_name="Ana Anić",
            email="ana@example.com",
        )
        products = [
            Product(name=n, description=d, price_cents=p, stock=s)
            for n, d, p, s in PRODUCTS
        ]
        db.add_all([admin, roko, kupac2, *products])
        await db.flush()

        o1 = await order_service.create_order(
            db,
            OrderCreate(
                shipping_address="Ulica kralja Zvonimira 1, Zadar",
                items=[
                    OrderItemCreate(product_id=products[0].id, quantity=1),
                    OrderItemCreate(product_id=products[10].id, quantity=1),
                ],
            ),
            roko,
        )
        await order_service.pay_order(db, o1.id, roko)

        await order_service.create_order(
            db,
            OrderCreate(
                shipping_address="Ulica kralja Zvonimira 1, Zadar",
                items=[OrderItemCreate(product_id=products[8].id, quantity=2)],
            ),
            roko,
        )

        await order_service.create_order(
            db,
            OrderCreate(
                shipping_address="Put Supavla 5, Split",
                items=[OrderItemCreate(product_id=products[5].id, quantity=1)],
            ),
            kupac2,
        )
        await db.commit()
        print("Seed gotov. Korisnici: admin / (ADMIN_PASSWORD), roko / roko123, kupac2 / kupac123")


if __name__ == "__main__":
    asyncio.run(seed())
