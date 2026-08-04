from __future__ import annotations


def _create_category(client) -> int:
    response = client.post("/api/v1/categories", json={"name": "Apparel"})
    assert response.status_code == 201
    return response.json()["id"]


class TestProductsApi:
    def test_create_and_get_product(self, client):
        category_id = _create_category(client)
        create_response = client.post(
            "/api/v1/products",
            json={"sku": "APP-100", "name": "Hoodie", "brand": "UrbanThread", "category_id": category_id, "list_price": 39.99},
        )
        assert create_response.status_code == 201
        product_id = create_response.json()["id"]

        get_response = client.get(f"/api/v1/products/{product_id}")
        assert get_response.status_code == 200
        assert get_response.json()["sku"] == "APP-100"

    def test_get_nonexistent_product_returns_404(self, client):
        response = client.get("/api/v1/products/99999")
        assert response.status_code == 404

    def test_create_product_missing_required_field_returns_422(self, client):
        response = client.post("/api/v1/products", json={"name": "Missing SKU"})
        assert response.status_code == 422

    def test_duplicate_sku_returns_409(self, client):
        category_id = _create_category(client)
        payload = {"sku": "APP-DUP", "name": "Item", "brand": "Brand", "category_id": category_id, "list_price": 10}
        assert client.post("/api/v1/products", json=payload).status_code == 201
        assert client.post("/api/v1/products", json=payload).status_code == 409

    def test_negative_price_rejected(self, client):
        category_id = _create_category(client)
        response = client.post(
            "/api/v1/products",
            json={"sku": "APP-NEG", "name": "Item", "brand": "Brand", "category_id": category_id, "list_price": -5},
        )
        assert response.status_code == 422


class TestProductsPagination:
    def _seed(self, client, category_id, count: int) -> None:
        for i in range(count):
            client.post(
                "/api/v1/products",
                json={"sku": f"PAG-{i:03d}", "name": f"Item {i}", "brand": "Brand", "category_id": category_id, "list_price": 10},
            )

    def test_total_count_header_reflects_full_result_set(self, client):
        category_id = _create_category(client)
        self._seed(client, category_id, 7)

        response = client.get("/api/v1/products", params={"limit": 5, "skip": 0})
        assert response.status_code == 200
        assert response.headers["X-Total-Count"] == "7"
        assert len(response.json()) == 5

    def test_second_page_returns_remainder(self, client):
        category_id = _create_category(client)
        self._seed(client, category_id, 7)

        response = client.get("/api/v1/products", params={"limit": 5, "skip": 5})
        assert response.headers["X-Total-Count"] == "7"
        assert len(response.json()) == 2

    def test_total_count_header_reflects_filters(self, client):
        category_id = _create_category(client)
        self._seed(client, category_id, 3)
        client.post(
            "/api/v1/products",
            json={"sku": "SHO-999", "name": "Sneaker", "brand": "Stridex", "category_id": category_id, "list_price": 50},
        )

        response = client.get("/api/v1/products", params={"keyword": "Sneaker"})
        assert response.headers["X-Total-Count"] == "1"
        assert len(response.json()) == 1
