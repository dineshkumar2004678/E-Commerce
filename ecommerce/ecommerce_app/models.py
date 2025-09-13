from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from bson import ObjectId
import pymongo

# MongoDB connection setup
try:
    MONGODB_URI = "mongodb://localhost:27017/"
    MONGODB_DB = "ecommerce"
    mongodb_client = pymongo.MongoClient(MONGODB_URI)
    mongodb = mongodb_client[MONGODB_DB]
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    mongodb = None

class ProductManager:
    @staticmethod
    def get_all_products():
        if mongodb is not None:  # FIXED: Compare with None instead of using if mongodb:
            return list(mongodb.products.find({}))
        return []
    
    @staticmethod
    def get_product_by_id(product_id):
        if mongodb is not None:  # FIXED
            try:
                return mongodb.products.find_one({"_id": ObjectId(product_id)})
            except:
                return None
        return None
    
    @staticmethod
    def get_products_by_category(category):
        if mongodb is not None:  # FIXED
            return list(mongodb.products.find({"category": category}))
        return []
    
    @staticmethod
    def search_products(query):
        if mongodb is not None:  # FIXED
            return list(mongodb.products.find({
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"category": {"$regex": query, "$options": "i"}}
                ]
            }))
        return []

# Rest of your models remain the same
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Cart of {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    @property
    def item_count(self):
        return self.items.count()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    def __str__(self):
        return f"{self.quantity} x {self.product_id}"
    
    @property
    def product(self):
        return ProductManager.get_product_by_id(self.product_id)
    
    @property
    def total_price(self):
        product = self.product
        if product:
            return float(product.get('price', 0)) * self.quantity
        return 0

class Order(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Confirmed'),
        ('S', 'Shipped'),
        ('D', 'Delivered'),
        ('X', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.JSONField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"