######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_get_product(self):
        """ Should get a product """
        test_product = self._create_products()[0]

        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json, test_product.serialize())

    def test_get_product_not_found(self):
        """ Should return not found for unknown product """
        url = f"{BASE_URL}/{5000}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Write a test case to Update a Product and watch it fail
    # Write the code to make the Update test case pass
    def test_update_product(self):
        """ Should update a product """
        test_product = self._create_products()[0]
        test_product.name = "BrandSpankingNewProduct"
        test_product.description = "It's a never before seen product that's gonna knock yer socks off!"
        test_product.price = 111.11
        test_product.available = True
        test_product.category = Category.TOOLS

        payload = test_product.serialize()
        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.put(url, json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload, response.json)

    def test_update_product_no_data(self):
        """ Should return bad request when missing all data """
        test_product = self._create_products()[0]
        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.put(url, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_extra_attribute(self):
        """ Should return bad request when it has an invalid category """
        test_product = self._create_products()[0]
        payload = test_product.serialize()
        payload["category"] = 1000
        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.put(url, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_product_missing_key(self):
        """ Should return bad request when it is missing a key """
        test_product = self._create_products()[0]
        payload = test_product.serialize()
        del payload["name"]
        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.put(url, json=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        

    def test_delete_product(self):
        """ Should delete a product """
        test_product = self._create_products()[0]
        url = f"{BASE_URL}/{test_product.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        found_product = Product.find(test_product.id)
        self.assertIsNone(found_product)

    def test_delete_unknown_product(self):
        """ Should return not found when deleting an unknown product """
        url = f"{BASE_URL}/{1000}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_all_products(self):
        """ Should get all products """
        products = self._create_products(10)

        url = f"{BASE_URL}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 10)

    # Write a test case to List by name a Product and watch it fail
    # Write the code to make the List by name test case pass
    def test_list_products_by_name(self):
        """ Should search by product name """
        products = self._create_products(10)
        search_name = products[0].name
        name_count = sum([p.name == search_name for p in products])

        url = f"{BASE_URL}?name={search_name}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), name_count)

    def test_list_products_by_category(self):
        """ Should search by product category """
        products = self._create_products(10)
        search_category = products[0].category.name
        category_count = sum([p.category.name == search_category for p in products])

        url = f"{BASE_URL}?category={search_category}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), category_count)

    def test_list_products_by_invalid_category(self):
        """ Should return bad request when searching by invalid category """
        url = f"{BASE_URL}?category={'BAD_CATEGORY'}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_products_by_availability(self):
        """ Should search by product availability """
        products = self._create_products(10)
        search_available = products[0].available
        available_count = sum([p.available == search_available for p in products])

        url = f"{BASE_URL}?available={search_available}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), available_count)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
