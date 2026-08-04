# User Manual

## Getting Started
1. Open the frontend at http://localhost:8501.
2. Log in via **Admin Login** (sidebar) with the default seeded account
   (`admin` / `Admin@123`) or register a new account.

## Product Catalog
- Use the search box, category dropdown, and brand filter to find products.
- Expand **➕ Add category** or use the **➕ Add product** panel to add catalog data.

## Inventory
- **⚠️ Low Stock** tab shows every product location at or below its reorder level.
- **📍 By Product** tab shows stock across all locations for a chosen product.
- **➕ Add / Adjust** tab lets you create new stock records or apply a manual
  adjustment (e.g. `+50` for a restock, `-5` for shrinkage) with a required reason.

## Placing an Order
1. Go to **Orders → 🛒 Place Order**.
2. Choose a customer and sales channel, then select one or more products and set
   quantities.
3. Click **Place order**. The system reserves stock and computes the total
   automatically; it will show an error if stock is insufficient.
4. Track and update order status from **🔎 Lookup Orders**.

## Asking the Knowledge Assistant (RAG)
1. Go to **RAG Assistant → 📤 Ingest PDF** and upload a retail PDF (catalog, price
   list, planogram, invoice, or flyer).
2. Once ingested, go to **💬 Ask a Question** and type a natural-language question.
3. Review the answer along with cited sources (document, page, content type, and a
   relevance score) in the expandable **Sources** section.

## Using the AI Agents Studio
1. Go to **AI Agents Studio**.
2. Enter a project brief (e.g. "Add a loyalty points redemption flow").
3. Choose which agent(s) to run, then click **Run agents**.
4. Review each agent's output and quality metrics. Without an OpenAI API key
   configured, output is clearly labeled as simulated/template-based — this is
   expected and lets you explore the workflow at zero cost.
5. Optionally rate the output using the **📝 Feedback** form at the bottom of the
   page to help track quality over time.

## Roles
- **customer** — browsing/ordering only.
- **staff** — catalog/inventory/order management.
- **admin** — full access, including user management (future extension point).
