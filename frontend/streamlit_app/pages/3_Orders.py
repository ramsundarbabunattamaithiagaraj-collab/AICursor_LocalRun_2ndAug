from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.api_client import ApiError, api_get, api_patch, api_post

st.set_page_config(page_title="Orders - RetailIQ", page_icon="🧾", layout="wide")

st.title("🧾 Order Management")

try:
    customers = api_get("/api/v1/customers", params={"limit": 500})
    products = api_get("/api/v1/products", params={"limit": 500})
except ApiError as exc:
    st.error(f"Could not load data: {exc.detail}")
    customers, products = [], []

customer_lookup = {f"{c['full_name']} ({c['email']})": c["id"] for c in customers}
product_lookup = {f"{p['sku']} - {p['name']} (${p['selling_price']})": p["id"] for p in products}

tab_place, tab_lookup, tab_new_customer = st.tabs(["🛒 Place Order", "🔎 Lookup Orders", "👤 New Customer"])

with tab_place:
    if not customer_lookup or not product_lookup:
        st.warning("You need at least one customer and one product before placing an order.")
    else:
        selected_customer = st.selectbox("Customer", list(customer_lookup.keys()))
        channel = st.selectbox("Channel", ["online", "in-store", "mobile"])
        selected_products = st.multiselect("Products", list(product_lookup.keys()))

        quantities: dict[str, int] = {}
        for p in selected_products:
            quantities[p] = st.number_input(f"Quantity - {p}", min_value=1, value=1, key=f"qty_{p}")

        if st.button("Place order", disabled=not selected_products):
            try:
                items = [{"product_id": product_lookup[p], "quantity": quantities[p]} for p in selected_products]
                order = api_post(
                    "/api/v1/orders",
                    {"customer_id": customer_lookup[selected_customer], "channel": channel, "items": items},
                )
                st.success(f"Order {order['order_number']} placed! Total: ${order['total_amount']}")
            except ApiError as exc:
                st.error(f"Failed to place order: {exc.detail}")

with tab_lookup:
    if not customer_lookup:
        st.info("No customers yet.")
    else:
        selected_lookup = st.selectbox("Customer", list(customer_lookup.keys()), key="lookup_customer")
        try:
            orders = api_get(f"/api/v1/orders/customer/{customer_lookup[selected_lookup]}")
        except ApiError as exc:
            st.error(f"Could not load orders: {exc.detail}")
            orders = []

        if not orders:
            st.info("No orders found for this customer.")
        else:
            for order in orders:
                with st.expander(f"{order['order_number']} — {order['status'].upper()} — ${order['total_amount']}"):
                    items_df = pd.DataFrame(order["items"])
                    st.dataframe(items_df, use_container_width=True, hide_index=True)

                    new_status = st.selectbox(
                        "Update status", ["placed", "paid", "shipped", "delivered", "return_requested", "returned", "refunded", "cancelled"],
                        index=0, key=f"status_{order['id']}",
                    )
                    if st.button("Update", key=f"update_{order['id']}"):
                        try:
                            api_patch(f"/api/v1/orders/{order['id']}/status", {"status": new_status})
                            st.success("Order status updated.")
                            st.rerun()
                        except ApiError as exc:
                            st.error(f"Failed: {exc.detail}")

with tab_new_customer:
    with st.form("new_customer_form"):
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
        phone = st.text_input("Phone", value="")
        submitted = st.form_submit_button("Create customer")
    if submitted:
        try:
            api_post("/api/v1/customers", {"full_name": full_name, "email": email, "phone": phone or None})
            st.success(f"Customer '{full_name}' created.")
            st.rerun()
        except ApiError as exc:
            st.error(f"Failed to create customer: {exc.detail}")
