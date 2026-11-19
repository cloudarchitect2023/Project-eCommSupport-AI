from backend.database import initialize_database, seed_demo_data


if __name__ == "__main__":
    initialize_database()
    seed_demo_data()
    print("Database schema is ready; demo data is present.")
