######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
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

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################


@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################


@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################


@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()
    location_url = url_for("get_product", product_id=product.id, _external=True)
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################


@app.route("/products", methods=['GET'])
def get_products():
    """
    Gets products, filtered by query parametes if provided
    """
    name = request.args.get("name")                 # Check for ?name=
    category_str = request.args.get("category")     # Check for ?category=
    available_str = request.args.get("available")     # Check for ?available=

    # Start with all products:
    products = Product.all()

    if name:
        # Filter by Name:
        products = [p for p in products if p.name == name]

    if category_str:
        try:
            # Filter by Category:
            category = getattr(Category, category_str.upper())
            products = [p for p in products if p.category == category]
        except AttributeError:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Invalid category: {category_str}"
            )

    if available_str:
        # Filter by Available:
        available = None
        if available_str.lower() in ('true', 't', '1', 'yes'):
            available = True
        elif available_str.lower() in ('false', 'f', '0', 'no'):
            available = False
        else:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"Invalid value for 'available': {available_str}"
            )
        products = [p for p in products if p.available == available]

    product_list = [p.serialize() for p in products]
    return jsonify(product_list), status.HTTP_200_OK

######################################################################
# R E A D   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=['GET'])
def get_product(product_id):
    """
    Gets a Product by ID
    This endpoint will get a Product based on the ID provided in the URL
    """
    app.logger.info("Request to Get a Product...")

    found_product = Product.find(product_id)
    if not found_product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product not found for id: {product_id}"
        )

    message = found_product.serialize()
    return jsonify(message), status.HTTP_200_OK

######################################################################
# U P D A T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=['PUT'])
def update_product(product_id):
    """
    Updates a product with specified id
    This endpoint will update the specified product with newly provided values
    """
    app.logger.info("Request to Update a Product...")

    found_product = Product.find(product_id)
    if not found_product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product not found for id: {product_id}"
        )

    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)

    try:
        found_product.deserialize(data)
    except AttributeError as error:
        abort(
            status.HTTP_400_BAD_REQUEST,
            error.message
        )
    except KeyError as error:
        abort(
            status.HTTP_400_BAD_REQUEST,
            error.message
        )
    except TypeError as error:
        abort(
            status.HTTP_400_BAD_REQUEST,
            error.message
        )

    found_product.update()

    message = found_product.serialize()
    return jsonify(message), status.HTTP_200_OK

######################################################################
# D E L E T E   A   P R O D U C T
######################################################################


@app.route("/products/<int:product_id>", methods=['DELETE'])
def delete_product(product_id):
    """
    Deletes a product with specified id
    This endpoint will delete the specified product
    """
    app.logger.info("Request to Update a Product...")

    found_product = Product.find(product_id)
    if not found_product:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Product not found for id: {product_id}"
        )

    found_product.delete()
    return '', status.HTTP_204_NO_CONTENT
