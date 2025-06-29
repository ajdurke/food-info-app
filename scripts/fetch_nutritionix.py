import argparse
from food_project.database.nutritionix_service import get_nutrition_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch nutrition data and store in SQLite")
    parser.add_argument("food", help="Food item to search")
    args = parser.parse_args()

    data = get_nutrition_data(args.food)
    if data:
        for k, v in data.items():
            print(f"{k}: {v}")
    else:
        print("No data found")


if __name__ == "__main__":
    main()
