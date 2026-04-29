import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_full_pipeline():
    print("\n" + "="*60)
    print("KISAAN MITRA — PIPELINE TEST")
    print("="*60)

    # 1. MongoDB
    print("\n[1/5] Testing MongoDB connection...")
    try:
        from app.utils.database import connect_db, get_db
        await connect_db()
        db = get_db()
        user_count = await db.users.count_documents({})
        price_count = await db.prices.count_documents({})
        notif_count = await db.notifications.count_documents({})
        print(f"  ✅ Connected!")
        print(f"     Users:         {user_count}")
        print(f"     Prices:        {price_count}")
        print(f"     Notifications: {notif_count}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return

    # 2. API Key
    print("\n[2/5] Checking AgMarket API key...")
    from app.config import settings
    if not settings.AGMARKET_API_KEY:
        print("  ❌ AGMARKET_API_KEY is empty in .env!")
        print("     Get free key: https://data.gov.in/user/register")
        api_ok = False
    else:
        print(f"  ✅ Key found: {settings.AGMARKET_API_KEY[:8]}...")
        api_ok = True

    # 3. Real API fetch
    print("\n[3/5] Testing AgMarket API fetch...")
    if not api_ok:
        print("  ⏭️  Skipped — no API key")
    else:
        from app.services.agmarket_service import agmarket_service
        records = await agmarket_service.fetch_prices(
            state="Karnataka", commodity="Tomato", limit=3
        )
        if records:
            r = records[0]
            print(f"  ✅ Got {len(records)} records!")
            print(f"     {r.get('commodity')} @ {r.get('market')} = ₹{r.get('modal_price')}")
            stored = await agmarket_service.fetch_and_store(
                state="Karnataka", commodity="Tomato"
            )
            print(f"  ✅ Stored {stored} records in DB")
        else:
            print("  ❌ No records — check API key or try Onion/Potato")

    # 4. Users and crops
    print("\n[4/5] Checking users and crops...")
    db = get_db()
    users = await db.users.find({}).to_list(length=5)
    if not users:
        print("  ❌ No users found — register in the app first")
    else:
        for u in users:
            crops = u.get("crops", [])
            fcm = u.get("fcm_token")
            print(f"  User: {u.get('name')} | Phone: {u.get('phone')}")
            print(f"  Crops: {[c['commodity'] for c in crops] if crops else 'NONE'}")
            print(f"  FCM token: {'✅ Set' if fcm else '❌ Missing — push wont work'}")

    # 5. Notification test
    print("\n[5/5] Testing notification pipeline...")
    user_with_crops = await db.users.find_one({
        "is_active": True,
        "crops": {"$exists": True, "$not": {"$size": 0}}
    })

    if not user_with_crops:
        print("  ⏭️  Skipped — no users with crops")
        print("     → Open app → My Crops → Add crop → Save")
    else:
        test_crop = user_with_crops["crops"][0]
        print(f"  Simulating 25% jump for {test_crop['commodity']}...")

        from app.services.alert_engine import alert_engine
        before = await db.notifications.count_documents({})

        await alert_engine.process_price_update(
            commodity=test_crop["commodity"],
            market="Yeshwanthpur",
            state=test_crop.get("state", "Karnataka"),
            district="Bangalore Urban",
            current_price=2500.0,
            previous_price=2000.0,
        )

        after = await db.notifications.count_documents({})
        if after > before:
            last = await db.notifications.find_one(sort=[("created_at", -1)])
            print(f"  ✅ Notification created!")
            print(f"     Type:     {last['alert_type']}")
            print(f"     Push:     {last['firebase_sent']}")
            print(f"     SMS:      {last['sms_sent']}")
            print(f"     Status:   {last['status']}")
        else:
            print("  ❌ No notification created — check logs above")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

asyncio.run(test_full_pipeline())