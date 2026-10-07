from api import api_bp
# from sqlalchemy import text
# from extension import db

@api_bp.get("/product")
def product():
    products = [
        {
            "id": 1,
            "name": "Jasmine Rice",
            "category": "rice",
            "origin": "Battambang",
            "unit": "5kg bag",
            "price": 8.50,
            "badge": "Organic",
            "description": "Premium Cambodian jasmine rice with a fragrant aroma and soft texture.",
            "rating": "★★★★★",
            "image": "/static/images/rice.jpg"
        },
        {
            "id": 2,
            "name": "Brown Rice",
            "category": "rice",
            "origin": "Siem Reap",
            "unit": "5kg bag",
            "price": 9.20,
            "badge": "Healthy",
            "description": "Nutritious whole-grain rice rich in fiber and natural vitamins.",
            "rating": "★★★★☆",
            "image": "/static/images/brown_rice.jpg"
        },
        {
            "id": 3,
            "name": "Sticky Rice",
            "category": "rice",
            "origin": "Kampong Thom",
            "unit": "3kg bag",
            "price": 6.80,
            "badge": "Fresh",
            "description": "Traditional sticky rice perfect for desserts and local dishes.",
            "rating": "★★★★☆",
            "image": "/static/images/sticky_rice.jpg"
        },
        {
            "id": 4,
            "name": "White Rice",
            "category": "rice",
            "origin": "Takeo",
            "unit": "10kg bag",
            "price": 15.00,
            "badge": "Popular",
            "description": "Clean and fluffy white rice suitable for everyday meals.",
            "rating": "★★★★★",
            "image": "/static/images/white_rice.jpg"
        },
        {
            "id": 5,
            "name": "Black Rice",
            "category": "rice",
            "origin": "Pursat",
            "unit": "2kg bag",
            "price": 11.50,
            "badge": "Premium",
            "description": "Premium antioxidant-rich black rice with a nutty flavor.",
            "rating": "★★★★★",
            "image": "/static/images/black_rice.jpg"
        },
        {
            "id": 6,
            "name": "Fresh Carrot",
            "category": "vegetable",
            "origin": "Mondulkiri",
            "unit": "1kg",
            "price": 2.30,
            "badge": "Organic",
            "description": "Fresh organic carrots packed with vitamins and natural sweetness.",
            "rating": "★★★★☆",
            "image": "/static/images/carrot.jpg"
        },
        {
            "id": 7,
            "name": "Broccoli",
            "category": "vegetable",
            "origin": "Phnom Penh",
            "unit": "500g",
            "price": 3.10,
            "badge": "Fresh",
            "description": "Crisp broccoli florets ideal for healthy meals and stir-fries.",
            "rating": "★★★★☆",
            "image": "/static/images/broccoli.jpg"
        },
        {
            "id": 8,
            "name": "Tomato",
            "category": "vegetable",
            "origin": "Kandal",
            "unit": "1kg",
            "price": 1.90,
            "badge": "Local",
            "description": "Juicy local tomatoes perfect for salads, soups, and cooking.",
            "rating": "★★★★☆",
            "image": "/static/images/tomato.jpg"
        },
        {
            "id": 11,
            "name": "Mango",
            "category": "fruit",
            "origin": "Kampong Speu",
            "unit": "1kg",
            "price": 4.20,
            "badge": "Sweet",
            "description": "Naturally sweet and juicy mangoes harvested at peak ripeness.",
            "rating": "★★★★★",
            "image": "/static/images/mango.jpg"
        },
        {
            "id": 16,
            "name": "Orange Juice",
            "category": "drink",
            "origin": "Phnom Penh",
            "unit": "1 bottle",
            "price": 2.80,
            "badge": "Cold",
            "description": "Refreshing orange juice made from freshly squeezed oranges.",
            "rating": "★★★★☆",
            "image": "/static/images/orange_juice.jpg"
        },
        {
            "id": 21,
            "name": "Potato Chips",
            "category": "snack",
            "origin": "Phnom Penh",
            "unit": "1 pack",
            "price": 1.50,
            "badge": "Crunchy",
            "description": "Golden crispy potato chips with a delicious savory flavor.",
            "rating": "★★★★☆",
            "image": "/static/images/chips.jpg"
        },
        {
            "id": 26,
            "name": "Bread",
            "category": "bakery",
            "origin": "Phnom Penh",
            "unit": "1 loaf",
            "price": 2.50,
            "badge": "Fresh",
            "description": "Freshly baked bread with a soft interior and golden crust.",
            "rating": "★★★★★",
            "image": "/static/images/bread.jpg"
        }
    ]

    return products