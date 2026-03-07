from typing import Dict, Optional
import random


def mock_food_recommendation(meal_type: str) -> Optional[Dict]:
    meals = {
        "breakfast": [
            {
                "meal": "breakfast",
                "foods": [
                    {
                        "name": "Ragi dosa with mint chutney",
                        "quantity": "2 medium",
                        "calories": 290,
                        "carbs_g": 42,
                        "protein_g": 9,
                        "fat_g": 7,
                        "fiber_g": 6,
                    }
                ],
            },
            {
                "meal": "breakfast",
                "foods": [
                    {
                        "name": "Vegetable oats upma",
                        "quantity": "1 bowl",
                        "calories": 280,
                        "carbs_g": 40,
                        "protein_g": 8,
                        "fat_g": 6,
                        "fiber_g": 7,
                    }
                ],
            },
            {
                "meal": "breakfast",
                "foods": [
                    {
                        "name": "Kambu (pearl millet) koozh with sundal",
                        "quantity": "1 bowl",
                        "calories": 300,
                        "carbs_g": 45,
                        "protein_g": 10,
                        "fat_g": 6,
                        "fiber_g": 8,
                    }
                ],
            },
        ],
        "lunch": [
            {
                "meal": "lunch",
                "foods": [
                    {
                        "name": "Brown rice with sambar and keerai poriyal",
                        "quantity": "1 plate",
                        "calories": 420,
                        "carbs_g": 55,
                        "protein_g": 16,
                        "fat_g": 9,
                        "fiber_g": 11,
                    }
                ],
            },
            {
                "meal": "lunch",
                "foods": [
                    {
                        "name": "Millet lemon rice with vegetable kootu",
                        "quantity": "1 plate",
                        "calories": 410,
                        "carbs_g": 50,
                        "protein_g": 14,
                        "fat_g": 10,
                        "fiber_g": 9,
                    }
                ],
            },
        ],
        "snacks": [
            {
                "meal": "snacks",
                "foods": [
                    {
                        "name": "Sundal (boiled channa)",
                        "quantity": "1 cup",
                        "calories": 180,
                        "carbs_g": 22,
                        "protein_g": 9,
                        "fat_g": 4,
                        "fiber_g": 7,
                    }
                ],
            },
            {
                "meal": "snacks",
                "foods": [
                    {
                        "name": "Sprouts salad",
                        "quantity": "1 bowl",
                        "calories": 160,
                        "carbs_g": 18,
                        "protein_g": 10,
                        "fat_g": 3,
                        "fiber_g": 6,
                    }
                ],
            },
        ],
        "dinner": [
            {
                "meal": "dinner",
                "foods": [
                    {
                        "name": "Vegetable kootu with 2 small phulka",
                        "quantity": "1 plate",
                        "calories": 380,
                        "carbs_g": 42,
                        "protein_g": 16,
                        "fat_g": 8,
                        "fiber_g": 10,
                    }
                ],
            },
            {
                "meal": "dinner",
                "foods": [
                    {
                        "name": "Ragi kali with keerai masiyal",
                        "quantity": "1 plate",
                        "calories": 370,
                        "carbs_g": 45,
                        "protein_g": 12,
                        "fat_g": 6,
                        "fiber_g": 9,
                    }
                ],
            },
        ],
    }

    options = meals.get(meal_type.lower())
    if not options:
        return None

    return random.choice(options)

