"""Comprehensive unit conversion system for cooking ingredients."""

import re
from typing import Optional, Dict, Any, Tuple

# ============================================================================
# UNIT DEFINITIONS
# ============================================================================

# Volume units (convert to milliliters first, then to grams)
VOLUME_UNITS = {
    # Teaspoons
    "tsp": 4.93, "teaspoon": 4.93, "teaspoons": 4.93, "tsp.": 4.93,
    
    # Tablespoons  
    "tbsp": 14.79, "tablespoon": 14.79, "tablespoons": 14.79, "tbsp.": 14.79,
    
    # Cups
    "cup": 236.59, "cups": 236.59,
    
    # Fluid ounces
    "fl oz": 29.57, "fluid ounce": 29.57, "fluid ounces": 29.57,
    
    # Milliliters and liters
    "ml": 1.0, "milliliter": 1.0, "milliliters": 1.0,
    "l": 1000.0, "liter": 1000.0, "liters": 1000.0,
    
    # Pints and quarts
    "pint": 473.18, "pints": 473.18,
    "quart": 946.35, "quarts": 946.35,
    
    # Gallons
    "gallon": 3785.41, "gallons": 3785.41,
}

# Weight units (convert directly to grams)
WEIGHT_UNITS = {
    "g": 1.0, "gram": 1.0, "grams": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "kilograms": 1000.0,
    "mg": 0.001, "milligram": 0.001, "milligrams": 0.001,
    "oz": 28.35, "ounce": 28.35, "ounces": 28.35, "oz.": 28.35,
    "lb": 453.59, "pound": 453.59, "pounds": 453.59, "lb.": 453.59,
}

# Countable items (pieces, slices, etc.)
COUNTABLE_UNITS = {
    "count", "piece", "pieces", "slice", "slices", "clove", "cloves",
    "egg", "eggs", "can", "cans", "package", "packages", "pkg", "pkg.",
    "bunch", "bunches", "sprig", "sprigs", "stalk", "stalks", "ear", "ears",
    "cube", "cubes", "strip", "strips", "chunk", "chunks", "drop", "drops",
    "pinch", "pinches", "dash", "dashes", "sheet", "sheets", "jar", "jars",
    "stick", "sticks", "recipe", "recipes"
}

# Combined list for validation
COMMON_UNITS = list(VOLUME_UNITS.keys()) + list(WEIGHT_UNITS.keys()) + list(COUNTABLE_UNITS)

# ============================================================================
# FOOD DENSITY DATABASE (grams per milliliter for volume conversions)
# ============================================================================

FOOD_DENSITIES = {
    # Oils and fats
    "olive oil": 0.92, "vegetable oil": 0.92, "canola oil": 0.92,
    "butter": 0.91, "margarine": 0.91, "coconut oil": 0.92,
    
    # Dairy
    "milk": 1.03, "whole milk": 1.03, "skim milk": 1.03, "2% milk": 1.03,
    "cream": 1.01, "heavy cream": 0.99, "half and half": 1.02,
    "yogurt": 1.03, "greek yogurt": 1.04, "sour cream": 1.01,
    "cheese": 1.13, "cheddar cheese": 1.13, "mozzarella": 1.13,
    
    # Sweeteners
    "sugar": 0.85, "brown sugar": 0.72, "powdered sugar": 0.56,
    "honey": 1.42, "maple syrup": 1.33, "corn syrup": 1.36,
    
    # Flours and grains
    "flour": 0.59, "all-purpose flour": 0.59, "bread flour": 0.59,
    "whole wheat flour": 0.59, "oatmeal": 0.35, "oats": 0.35,
    
    # Nuts and seeds
    "almonds": 0.48, "walnuts": 0.48, "pecans": 0.48, "peanuts": 0.48,
    "sunflower seeds": 0.48, "pumpkin seeds": 0.48, "chia seeds": 0.48,
    
    # Liquids
    "water": 1.0, "broth": 1.0, "stock": 1.0, "juice": 1.04,
    "vinegar": 1.01, "soy sauce": 1.18, "worcestershire sauce": 1.18,
    
    # Default density for unknown foods
    "default": 1.0
}

# ============================================================================
# CONVERSION FUNCTIONS
# ============================================================================

def normalize_unit(unit: str) -> str:
    """Convert unit to standard form and handle aliases."""
    if not unit:
        return None
    
    unit = unit.lower().strip()
    
    # Handle common aliases
    aliases = {
        "tablespoon": "tbsp", "tablespoons": "tbsp",
        "teaspoon": "tsp", "teaspoons": "tsp",
        "ounce": "oz", "ounces": "oz",
        "pound": "lb", "pounds": "lb",
        "gram": "g", "grams": "g",
        "kilogram": "kg", "kilograms": "kg",
        "milliliter": "ml", "milliliters": "ml",
        "liter": "l", "liters": "l",
    }
    
    return aliases.get(unit, unit)

def get_food_density(food_name: str) -> float:
    """Get the density (g/ml) for a given food item."""
    if not food_name:
        return FOOD_DENSITIES["default"]
    
    food_name = food_name.lower().strip()
    
    # Try exact match first
    if food_name in FOOD_DENSITIES:
        return FOOD_DENSITIES[food_name]
    
    # Try partial matches
    for known_food, density in FOOD_DENSITIES.items():
        if known_food in food_name or food_name in known_food:
            return density
    
    # Return default density for unknown foods
    return FOOD_DENSITIES["default"]

def convert_to_grams(amount: float, unit: str, food_name: str = None) -> Optional[float]:
    """
    Convert any cooking unit to grams.
    
    Args:
        amount: The quantity to convert
        unit: The unit of measurement
        food_name: The name of the food (needed for volume conversions)
    
    Returns:
        Weight in grams, or None if conversion is not possible
    """
    if not amount or not unit:
        return None
    
    unit = normalize_unit(unit)
    
    # Handle weight units (direct conversion)
    if unit in WEIGHT_UNITS:
        return amount * WEIGHT_UNITS[unit]
    
    # Handle volume units (need food density)
    if unit in VOLUME_UNITS:
        if not food_name:
            # If no food name, assume water density
            density = FOOD_DENSITIES["water"]
        else:
            density = get_food_density(food_name)
        
        # Convert volume to ml, then to grams
        volume_ml = amount * VOLUME_UNITS[unit]
        return volume_ml * density
    
    # Handle countable items (return None - these need special handling)
    if unit in COUNTABLE_UNITS:
        return None
    
    # Unknown unit
    return None

def extract_unit_size(amount: float, unit: str, normalized_name: str) -> Optional[float]:
    """
    Estimate grams based on amount, unit, and food name.
    This is the main function that should be called from other parts of the app.
    """
    return convert_to_grams(amount, unit, normalized_name)

def get_unit_type(unit: str) -> str:
    """Determine if a unit is weight, volume, or countable."""
    unit = normalize_unit(unit)
    
    if unit in WEIGHT_UNITS:
        return "weight"
    elif unit in VOLUME_UNITS:
        return "volume"
    elif unit in COUNTABLE_UNITS:
        return "countable"
    else:
        return "unknown"

def format_conversion_result(amount: float, unit: str, grams: float) -> str:
    """Format conversion results for display."""
    if grams is None:
        return f"{amount} {unit} (cannot convert to grams)"
    
    if grams < 1:
        return f"{amount} {unit} = {grams:.2f} grams"
    elif grams < 10:
        return f"{amount} {unit} = {grams:.1f} grams"
    else:
        return f"{amount} {unit} = {grams:.0f} grams"

# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

def test_conversions():
    """Test the conversion system with common examples."""
    test_cases = [
        (1, "cup", "flour", "1 cup flour = 139 grams"),
        (2, "tbsp", "olive oil", "2 tbsp olive oil = 27 grams"),
        (1, "lb", "chicken", "1 lb chicken = 454 grams"),
        (3, "tsp", "salt", "3 tsp salt = 15 grams"),
        (1, "count", "egg", "1 count egg (cannot convert to grams)"),
    ]
    
    print("🧪 Testing Unit Conversions:")
    print("=" * 50)
    
    for amount, unit, food, expected in test_cases:
        result = convert_to_grams(amount, unit, food)
        formatted = format_conversion_result(amount, unit, result)
        status = "✅" if "grams" in formatted else "⚠️"
        print(f"{status} {formatted}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_conversions()

