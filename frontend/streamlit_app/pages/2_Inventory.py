from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.api_client import ApiError, api_get, api_post

st.set_page_config(page_title="Inventory - RetailIQ", page_icon="🏬", layout="wide")

st.title("🏬 Inventory & Stock Availability")

try:
    products = api_get("/api/v1/products", params={"active_only": False, "limit": 500})
except ApiError as exc:
    st.error(f"Could not load products: {exc.detail}")
    products = []

product_lookup = {f"{p['sku']} - {p['name']}": p["id"] for p in products}

tab_low_stock, tab_by_product, tab_add = st.tabs(["⚠️ Low Stock", "📍 By Product", "➕ Add / Adjust"])

with tab_low_stock:
    try:
        low_stock = api_get("/api/v1/inventory/low-stock")
    except ApiError as exc:
        st.error(f"Could not load low-stock items: {exc.detail}")
        low_stock = []
    if low_stock:
        st.dataframe(pd.DataFrame(low_stock), use_container_width=True, hide_index=True)
    else:
        st.success("No items are currently at or below their reorder level.")

with tab_by_product:
    if not product_lookup:
        st.info("No products available yet.")
    else:
        selected = st.selectbox("Select a product", list(product_lookup.keys()))
        product_id = product_lookup[selected]
        try:
            records = api_get(f"/api/v1/inventory/product/{product_id}")
        except ApiError as exc:
            st.error(f"Could not load inventory: {exc.detail}")
            records = []
        if records:
            st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
        else:
            st.info("No inventory records for this product yet.")

with tab_add:
    col_add, col_adjust = st.columns(2)

    with col_add:
        st.subheader("Add inventory record")
        if not product_lookup:
            st.warning("Create a product first.")
        else:
            with st.form("add_inventory_form"):
                selected_add = st.selectbox("Product", list(product_lookup.keys()), key="add_inv_product")
                location_code = st.text_input("Location code", value="STORE-001")
                quantity = st.number_input("Quantity available", min_value=0, value=50)
                reorder_level = st.number_input("Reorder level", min_value=0, value=10)
                submit_add = st.form_submit_button("Create inventory record")
            if submit_add:
                try:
                    api_post(
                        "/api/v1/inventory",
                        {
                            "product_id": product_lookup[selected_add], "location_code": location_code,
                            "quantity_available": quantity, "reorder_level": reorder_level,
                        },
                    )
                    st.success("Inventory record created.")
                    st.rerun()
                except ApiError as exc:
                    st.error(f"Failed: {exc.detail}")

    with col_adjust:
        st.subheader("Adjust stock")
        inventory_id = st.number_input("Inventory record ID", min_value=1, step=1)
        delta = st.number_input("Delta (+ add / - remove)", value=0, step=1)
        reason = st.text_input("Reason", value="Manual adjustment")
        if st.button("Apply adjustment"):
            try:
                from utils.api_client import api_post as _post

                _post(f"/api/v1/inventory/{int(inventory_id)}/adjust", {"delta": int(delta), "reason": reason})
                st.success("Stock adjusted.")
                st.rerun()
            except ApiError as exc:
                st.error(f"Failed: {exc.detail}")
