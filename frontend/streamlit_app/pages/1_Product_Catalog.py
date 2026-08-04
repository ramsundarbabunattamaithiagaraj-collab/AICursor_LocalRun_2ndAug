from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from utils.api_client import ApiError, api_get, api_get_paginated, api_post
from utils.auth_state import init_session_state, is_authenticated

PAGE_SIZE_OPTIONS = [5, 10, 25]

st.set_page_config(page_title="Product Catalog - RetailIQ", page_icon="📦", layout="wide")
init_session_state()

st.title("📦 Product Catalog")

try:
    categories = api_get("/api/v1/categories")
except ApiError as exc:
    st.error(f"Could not load categories: {exc.detail}")
    categories = []

category_lookup = {c["name"]: c["id"] for c in categories}

with st.expander("➕ Add category", expanded=False):
    if not is_authenticated():
        st.warning("Log in from the Admin Login page to add categories.")
    with st.form("add_category_form"):
        name = st.text_input("Category name")
        description = st.text_area("Description", height=68)
        submitted = st.form_submit_button("Create category")
    if submitted:
        try:
            api_post("/api/v1/categories", {"name": name, "description": description or None})
            st.success(f"Category '{name}' created.")
            st.rerun()
        except ApiError as exc:
            st.error(f"Failed to create category: {exc.detail}")

st.divider()

col_filters, col_add = st.columns([2, 1])

with col_filters:
    st.subheader("🔍 Search products")
    keyword = st.text_input("Keyword (name, description, or SKU)")
    category_filter = st.selectbox("Category", ["All"] + list(category_lookup.keys()))
    brand_filter = st.text_input("Brand contains")

    filter_col, size_col = st.columns([3, 1])
    with size_col:
        page_size = st.selectbox("Per page", PAGE_SIZE_OPTIONS, index=1, key="catalog_page_size")

    params = {"keyword": keyword or None, "brand": brand_filter or None}
    if category_filter != "All":
        params["category_id"] = category_lookup[category_filter]

    # Reset to page 1 whenever a filter or the page size changes, so the
    # user never lands on a stale/out-of-range page after refining a search.
    filter_signature = (keyword, category_filter, brand_filter, page_size)
    if st.session_state.get("catalog_filter_signature") != filter_signature:
        st.session_state["catalog_page"] = 1
        st.session_state["catalog_filter_signature"] = filter_signature

    current_page = st.session_state.get("catalog_page", 1)
    skip = (current_page - 1) * page_size

    try:
        products, total_count = api_get_paginated(
            "/api/v1/products", params={**params, "skip": skip, "limit": page_size}
        )
    except ApiError as exc:
        st.error(f"Could not load products: {exc.detail}")
        products, total_count = [], 0

    total_pages = max(1, math.ceil(total_count / page_size))

    # Clamp defensively (e.g. a product was deleted elsewhere, shrinking the
    # result set below the current page) rather than showing a blank page.
    if current_page > total_pages:
        st.session_state["catalog_page"] = total_pages
        st.rerun()

    if products:
        df = pd.DataFrame(products)[
            ["id", "sku", "name", "brand", "variant", "size", "color", "list_price", "discount_percent", "tax_percent", "selling_price", "is_active"]
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No products found. Try adjusting filters or add a new product.")

    nav_prev, nav_info, nav_next = st.columns([1, 2, 1])
    with nav_prev:
        if st.button("⬅ Previous", disabled=current_page <= 1, use_container_width=True):
            st.session_state["catalog_page"] = current_page - 1
            st.rerun()
    with nav_info:
        st.markdown(
            f"<div style='text-align:center'>Page <b>{current_page}</b> of <b>{total_pages}</b> "
            f"&nbsp;|&nbsp; {total_count} product(s)</div>",
            unsafe_allow_html=True,
        )
    with nav_next:
        if st.button("Next ➡", disabled=current_page >= total_pages, use_container_width=True):
            st.session_state["catalog_page"] = current_page + 1
            st.rerun()

with col_add:
    st.subheader("➕ Add product")
    if not categories:
        st.warning("Create a category first.")
    else:
        with st.form("add_product_form"):
            sku = st.text_input("SKU")
            pname = st.text_input("Name")
            brand = st.text_input("Brand")
            category_name = st.selectbox("Category", list(category_lookup.keys()))
            variant = st.text_input("Variant", value="")
            size = st.text_input("Size", value="")
            color = st.text_input("Color", value="")
            list_price = st.number_input("List price", min_value=0.01, value=19.99, step=0.5)
            discount_percent = st.slider("Discount %", 0, 100, 0)
            tax_percent = st.slider("Tax %", 0, 50, 5)
            submitted_product = st.form_submit_button("Create product")
        if submitted_product:
            try:
                api_post(
                    "/api/v1/products",
                    {
                        "sku": sku, "name": pname, "brand": brand,
                        "category_id": category_lookup[category_name],
                        "variant": variant or None, "size": size or None, "color": color or None,
                        "list_price": list_price, "discount_percent": discount_percent, "tax_percent": tax_percent,
                    },
                )
                st.success(f"Product '{pname}' created.")
                st.rerun()
            except ApiError as exc:
                st.error(f"Failed to create product: {exc.detail}")
