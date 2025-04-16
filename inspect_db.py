from sqlalchemy import create_engine, inspect, text

# Yhdistetään tietokantaan suhteellisella polulla
engine = create_engine("sqlite:///instance/default.db")

# Käytetään inspectoria taulurakenteeseen
inspector = inspect(engine)

print("📦 Taulut tietokannassa:\n")
for table_name in inspector.get_table_names():
    print(f"🗂️ {table_name}")
    
    columns = inspector.get_columns(table_name)
    for col in columns:
        print(f"   - {col['name']} ({col['type']})")
    
    # Esimerkkirivit
    with engine.connect() as conn:
        print("   Esimerkkirivit:")
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
        for row in result:
            print(f"     {row._mapping}")
