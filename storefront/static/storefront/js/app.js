
"use strict";

/* ============================================================
   ENOCK SHOPPING CENTER
   Global marketplace storefront
   Django REST Framework compatible
   ============================================================ */

const CONFIG = {
  csrfUrl: "/api/users/csrf/",
  productsUrl: "/api/catalog/products/",
  categoriesUrl: "/api/catalog/categories/",
  sellersUrl: "/api/sellers/",
  meUrl: "/api/users/me/",
  loginUrl: "/api/users/login/",
  registerUrl: "/api/users/register/",
  logoutUrl: "/api/users/logout/",
  checkoutUrl: "/api/orders/checkout/",
  ordersUrl: "/api/orders/",
  sellerDashboardUrl: "/api/sellers/dashboard/",

  // Set this to your actual public-advertising API endpoint
  // once it exists in your Django project.
  advertsUrl: null
};

const state = {
  products: [],
  categories: [],
  sellers: [],
  adverts: [],
  cart: readStorage("enock_cart", []),
  wishlist: readStorage("enock_wishlist", []),
  user: null,
  selectedCategory: null,
  search: "",
  loadingProducts: false
};

/* ============================================================
   BASIC HELPERS
   ============================================================ */

function $(id) {
  return document.getElementById(id);
}

function readStorage(key, fallback) {
  try {
    const value = JSON.parse(localStorage.getItem(key) || "null");
    return value == null ? fallback : value;
  } catch {
    return fallback;
  }
}

function csrf() {
  const match = document.cookie.match(
    /(?:^|;\s*)csrftoken=([^;]+)/
  );

  return match ? decodeURIComponent(match[1]) : "";
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[char]);
}

function money(value, currency = "UGX") {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    return `${currency} 0`;
  }

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currency || "UGX",
      maximumFractionDigits: 2
    }).format(amount);
  } catch {
    return `${currency || "UGX"} ${amount.toLocaleString()}`;
  }
}

function toast(message) {
  const el = $("toast");

  if (!el) {
    console.info(message);
    return;
  }

  el.textContent = message;
  el.classList.add("show");

  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    el.classList.remove("show");
  }, 3000);
}

function save() {
  try {
    localStorage.setItem(
      "enock_cart",
      JSON.stringify(state.cart)
    );

    localStorage.setItem(
      "enock_wishlist",
      JSON.stringify(state.wishlist)
    );
  } catch {
    toast("Unable to save your cart in this browser.");
  }

  updateCounts();
}

function updateCounts() {
  const cartCount = $("cartCount");
  const wishCount = $("wishCount");

  if (cartCount) {
    cartCount.textContent = state.cart.reduce(
      (total, item) => total + Number(item.quantity || 0),
      0
    );
  }

  if (wishCount) {
    wishCount.textContent = state.wishlist.length;
  }
}

function showModal(html) {
  const modal = $("modal");
  const content = $("modalContent");

  if (!modal || !content) {
    console.error("Modal elements are missing.");
    return;
  }

  content.innerHTML = html;
  modal.classList.add("show");
  modal.setAttribute("aria-hidden", "false");
}

function hideModal() {
  const modal = $("modal");

  if (!modal) return;

  modal.classList.remove("show");
  modal.setAttribute("aria-hidden", "true");
}

function closeModal(event) {
  if (event.target.id === "modal") {
    hideModal();
  }
}

function go(id) {
  const target = $(id);

  if (target) {
    target.scrollIntoView({ behavior: "smooth" });
    history.replaceState(null, "", `#${id}`);
  }
}

function loadNav(id) {
  history.replaceState(null, "", `#${id}`);
}

function toggleNav() {
  const nav = $("mainNav");
  if (!nav) return;

  nav.style.display =
    nav.style.display === "flex" ? "none" : "flex";
}

/* ============================================================
   API CLIENT
   ============================================================ */

async function api(url, options = {}) {
  const headers = {
    Accept: "application/json",
    ...(options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(options.headers || {})
  };

  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers
  });

  if (response.status === 204) {
    if (!response.ok) throw new Error("Request failed.");
    return {};
  }

  const contentType = response.headers.get("content-type") || "";

  let data;

  if (contentType.includes("application/json")) {
    data = await response.json().catch(() => ({}));
  } else {
    data = await response.text().catch(() => "");
  }

  if (!response.ok) {
    let message = "Request failed. Please try again.";

    if (data && typeof data === "object") {
      message =
        data.detail ||
        data.message ||
        data.error ||
        firstValidationError(data) ||
        message;
    } else if (typeof data === "string" && data.trim()) {
      message = data.slice(0, 250);
    }

    throw new Error(message);
  }

  return data;
}

function firstValidationError(data) {
  if (!data || typeof data !== "object") return "";

  for (const [field, value] of Object.entries(data)) {
    if (Array.isArray(value) && value.length) {
      return `${field}: ${value[0]}`;
    }

    if (typeof value === "string") {
      return `${field}: ${value}`;
    }
  }

  return "";
}

function listFromResponse(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

async function getCsrf() {
  try {
    await api(CONFIG.csrfUrl);
  } catch (error) {
    console.warn("CSRF initialization failed:", error.message);
  }
}

/* ============================================================
   INITIALIZATION
   ============================================================ */

async function init() {
  await getCsrf();

  const jobs = [
    loadCategories(),
    loadProducts(),
    loadSellers(),
    loadMe(),
    loadAdverts()
  ];

  const results = await Promise.allSettled(jobs);

  results.forEach((result, index) => {
    if (result.status === "rejected") {
      console.error(
        `Storefront initialization task ${index + 1} failed:`,
        result.reason
      );
    }
  });

  updateCounts();
}

document.addEventListener("DOMContentLoaded", () => {
  init().catch(error => {
    console.error("Storefront initialization failed:", error);
    toast("Some marketplace content could not load.");
  });
});

/* ============================================================
   CATEGORIES
   ============================================================ */

async function loadCategories() {
  const container = $("categories");
  if (!container) return;

  const data = await api(CONFIG.categoriesUrl);
  state.categories = listFromResponse(data);

  const icons = [
    "🛍️", "📱", "💻", "👕", "🏠", "🎮",
    "🚗", "💄", "⚽", "📚", "🔧", "🎁"
  ];

  container.innerHTML = state.categories
    .slice(0, 12)
    .map((category, index) => `
      <button
        type="button"
        class="category-card"
        onclick="filterCategory(${Number(category.id)})"
      >
        <span class="emoji">${icons[index % icons.length]}</span>
        <h4>${esc(category.name)}</h4>
      </button>
    `)
    .join("");

  if (!state.categories.length) {
    container.innerHTML =
      '<p class="loading">Categories will appear here.</p>';
  }
}

/* ============================================================
   PRODUCTS, SEARCH, FILTERING AND SORTING
   ============================================================ */

async function loadProducts(search = state.search) {
  if (state.loadingProducts) return;

  state.loadingProducts = true;
  state.search = search || "";

  const sort = $("sortSelect")?.value || "-created_at";
  const params = new URLSearchParams();

  params.set("ordering", sort);

  if (state.search.trim()) {
    params.set("search", state.search.trim());
  }

  if (state.selectedCategory !== null) {
    params.set("category", String(state.selectedCategory));
  }

  const grid = $("productGrid");

  if (grid) {
    grid.innerHTML = '<p class="loading">Loading products...</p>';
  }

  try {
    const data = await api(
      `${CONFIG.productsUrl}?${params.toString()}`
    );

    state.products = listFromResponse(data);
    renderProducts();

    const resultText = $("resultText");

    if (resultText) {
      resultText.textContent = state.search.trim()
        ? `${state.products.length} results for "${state.search.trim()}"`
        : "Fresh listings from Enock sellers.";
    }
  } finally {
    state.loadingProducts = false;
  }
}

function renderProducts() {
  const grid = $("productGrid");
  if (!grid) return;

  if (!state.products.length) {
    grid.innerHTML = `
      <div class="loading">
        No products found. Try another search.
      </div>
    `;
    return;
  }

  grid.innerHTML = state.products.map(product => {
    const id = Number(product.id);
    const liked = state.wishlist.includes(id);
    const stock = Number(product.stock_quantity || 0);

    return `
      <article class="product">
        <button
          type="button"
          class="heart"
          aria-label="${liked ? "Remove from wishlist" : "Add to wishlist"}"
          aria-pressed="${liked}"
          onclick="toggleWish(${id})"
        >${liked ? "♥" : "♡"}</button>

        <div class="product-img" onclick="openProduct(${id})">
          ${product.image
            ? `<img src="${esc(product.image)}"
                    alt="${esc(product.name)}"
                    loading="lazy">`
            : '<span aria-hidden="true">🛍️</span>'}
        </div>

        <div class="product-body">
          <h3 title="${esc(product.name)}">
            ${esc(product.name)}
          </h3>

          <div class="seller-line">
            ${esc(product.seller_name || "Enock seller")}
            ${product.seller_verified
              ? '<span class="verified">✓ Verified</span>'
              : ""}
          </div>

          <div class="price">
            ${money(product.price, product.currency || "UGX")}
          </div>

          <div class="stock">
            ${stock > 0 ? `${stock} available` : "Out of stock"}
          </div>

          <div class="product-actions">
            <button type="button" onclick="openProduct(${id})">
              Details
            </button>

            <button
              type="button"
              onclick="addCart(${id})"
              ${stock < 1 ? "disabled" : ""}
            >
              Add to cart
            </button>
          </div>
        </div>
      </article>
    `;
  }).join("");
}

async function filterCategory(id) {
  state.selectedCategory = Number(id);
  go("market");
  await loadProducts();
}

async function clearCategoryFilter() {
  state.selectedCategory = null;
  await loadProducts();
}

async function searchProducts(query) {
  state.search = String(query || "").trim();
  go("market");
  await loadProducts();
}

function handleSearchSubmit(event) {
  event.preventDefault();

  const field =
    $("searchInput") ||
    $("search") ||
    document.querySelector('[name="search"]');

  searchProducts(field?.value || "");
}

const sortSelect = $("sortSelect");

if (sortSelect) {
  sortSelect.addEventListener("change", () => {
    loadProducts().catch(error => toast(error.message));
  });
}

/* ============================================================
   PRODUCT DETAILS
   ============================================================ */

function openProduct(id) {
  const product = state.products.find(
    item => Number(item.id) === Number(id)
  );

  if (!product) {
    toast("Product details are not available.");
    return;
  }

  showModal(`
    <div class="product-detail">
      <div class="product-img"
           style="height:260px;border-radius:15px">
        ${product.image
          ? `<img src="${esc(product.image)}"
                  alt="${esc(product.name)}">`
          : "🛍️"}
      </div>

      <h2>${esc(product.name)}</h2>

      <div class="seller-line">
        ${esc(product.seller_name || "Enock seller")}
        ${product.seller_verified
          ? '<span class="verified">✓ Verified seller</span>'
          : ""}
      </div>

      <div class="price">
        ${money(product.price, product.currency || "UGX")}
      </div>

      <p>${esc(product.description || "No description provided.")}</p>

      <p class="modal-note">
        SKU: ${esc(product.sku || "Not specified")}
        · ${Number(product.stock_quantity || 0)} available
        · Category: ${esc(product.category_name || "General")}
      </p>

      <button
        type="button"
        class="primary"
        onclick="addCart(${Number(product.id)});hideModal()"
      >
        Add to cart
      </button>
    </div>
  `);
}

/* ============================================================
   WISHLIST
   ============================================================ */

function toggleWish(id) {
  id = Number(id);

  const index = state.wishlist.indexOf(id);

  if (index >= 0) {
    state.wishlist.splice(index, 1);
    toast("Removed from wishlist.");
  } else {
    state.wishlist.push(id);
    toast("Added to wishlist.");
  }

  save();
  renderProducts();
}

function openWishlist() {
  const products = state.products.filter(product =>
    state.wishlist.includes(Number(product.id))
  );

  showModal(`
    <h2>Your wishlist</h2>

    ${products.length
      ? products.map(product => `
        <div class="cart-item">
          <div style="font-size:30px">♡</div>
          <div>
            <b>${esc(product.name)}</b>
            <p class="modal-note">
              ${money(product.price, product.currency || "UGX")}
            </p>
          </div>
          <button
            type="button"
            class="primary"
            onclick="addCart(${Number(product.id)})"
          >Add</button>
        </div>
      `).join("")
      : '<p class="modal-note">Your wishlist is empty, or its products have not loaded yet.</p>'}
  `);
}

/* ============================================================
   CART
   ============================================================ */

function addCart(id) {
  id = Number(id);

  const product = state.products.find(
    item => Number(item.id) === id
  );

  if (!product) {
    toast("Product not found. Reload the marketplace.");
    return;
  }

  const stock = Number(product.stock_quantity || 0);

  if (stock < 1) {
    toast("This product is out of stock.");
    return;
  }

  const item = state.cart.find(
    cartItem => Number(cartItem.product_id) === id
  );

  if (item) {
    if (Number(item.quantity) >= stock) {
      toast("You have reached the available stock limit.");
      return;
    }

    item.quantity = Number(item.quantity) + 1;
  } else {
    state.cart.push({
      product_id: id,
      quantity: 1,
      name: product.name,
      price: product.price,
      currency: product.currency || "UGX",
      image: product.image || ""
    });
  }

  save();
  toast("Added to your cart.");
}

function changeQty(id, delta) {
  id = Number(id);

  const index = state.cart.findIndex(
    item => Number(item.product_id) === id
  );

  if (index < 0) return;

  const item = state.cart[index];
  const product = state.products.find(
    p => Number(p.id) === id
  );

  if (!product) {
    toast("Product details are unavailable. Reload the marketplace.");
    return;
  }

  const next = Number(item.quantity) + Number(delta);
  const stock = Number(product.stock_quantity || 0);

  if (next > stock) {
    toast("Not enough stock available.");
    return;
  }

  if (next < 1) {
    state.cart.splice(index, 1);
  } else {
    item.quantity = next;
  }

  save();
  openCart();
}

function removeFromCart(id) {
  state.cart = state.cart.filter(
    item => Number(item.product_id) !== Number(id)
  );

  save();
  openCart();
}

function cartTotal() {
  return state.cart.reduce(
    (total, item) =>
      total + Number(item.price || 0) * Number(item.quantity || 0),
    0
  );
}

function openCart() {
  const currencies = [
    ...new Set(state.cart.map(item => item.currency || "UGX"))
  ];

  const mixedCurrencies = currencies.length > 1;

  showModal(`
    <h2>Your cart</h2>

    ${state.cart.length
      ? state.cart.map(item => `
        <div class="cart-item">
          <div>
            ${item.image
              ? `<img src="${esc(item.image)}"
                      alt=""
                      style="width:55px;height:55px;object-fit:cover;border-radius:9px">`
              : "🛍️"}
          </div>

          <div>
            <b>${esc(item.name)}</b>
            <p class="modal-note">
              ${money(item.price, item.currency || "UGX")}
            </p>

            <div class="cart-qty">
              <button type="button"
                      onclick="changeQty(${Number(item.product_id)},-1)">−</button>
              <span>${Number(item.quantity)}</span>
              <button type="button"
                      onclick="changeQty(${Number(item.product_id)},1)">+</button>
            </div>

            <button type="button"
                    onclick="removeFromCart(${Number(item.product_id)})">
              Remove
            </button>
          </div>

          <b>
            ${money(
              Number(item.price) * Number(item.quantity),
              item.currency || "UGX"
            )}
          </b>
        </div>
      `).join("") : '<p class="modal-note">Your cart is empty.</p>'}

    ${state.cart.length ? `
      <div class="total-row">
        <span>Total</span>
        <span>
          ${mixedCurrencies
            ? "See item totals above; currencies differ"
            : money(cartTotal(), currencies[0] || "UGX")}
        </span>
      </div>

      <button
        type="button"
        class="primary"
        style="width:100%"
        onclick="openCheckout()"
        ${mixedCurrencies ? "disabled" : ""}
      >
        Checkout
      </button>

      ${mixedCurrencies
        ? '<p class="modal-note">Remove items in other currencies before checkout.</p>'
        : ""}
    ` : ""}
  `);
}

/* ============================================================
   CHECKOUT AND ORDER SUBMISSION
   ============================================================ */

function openCheckout() {
  if (!state.cart.length) {
    toast("Your cart is empty.");
    return;
  }

  if (!state.user) {
    openAccount("login");
    toast("Please sign in before checkout.");
    return;
  }

  const currencies = [
    ...new Set(state.cart.map(item => item.currency || "UGX"))
  ];

  if (currencies.length > 1) {
    toast("Your cart contains different currencies.");
    return;
  }

  showModal(`
    <h2>Secure checkout</h2>

    <p class="modal-note">
      You are ordering as
      <b>${esc(state.user.email || state.user.username || "")}</b>.
    </p>

    <form class="form" onsubmit="submitCheckout(event)">
      <label for="shipAddress">Delivery address</label>
      <textarea id="shipAddress"
                required
                maxlength="2000"
                placeholder="Full delivery address"></textarea>

      <label for="shipCountry">Country</label>
      <input id="shipCountry"
             required
             maxlength="100"
             value="${esc(state.user.country || "Uganda")}">

      <label for="paymentMethod">Payment method</label>
      <select id="paymentMethod" required>
        <option value="cash_on_delivery">Cash on delivery</option>
        <option value="mobile_money">Mobile money</option>
        <option value="card">Bank card</option>
      </select>

      <p class="modal-note">
        Mobile money and card payments require server-side payment
        provider integration and confirmation.
      </p>

      <button class="primary" type="submit">
        Place order
      </button>
    </form>
  `);
}

async function submitCheckout(event) {
  event.preventDefault();

  const button = event.submitter;
  if (button) button.disabled = true;

  try {
    const items = state.cart.map(item => ({
      product_id: Number(item.product_id),
      quantity: Number(item.quantity)
    }));

    const order = await api(CONFIG.checkoutUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: JSON.stringify({
        items,
        shipping_address: $("shipAddress").value.trim(),
        shipping_country: $("shipCountry").value.trim(),
        payment_method: $("paymentMethod").value
      })
    });

    state.cart = [];
    save();
    hideModal();

    toast(`Order #${order.id ?? ""} submitted successfully.`);
    openOrders();
  } catch (error) {
    toast(error.message);
  } finally {
    if (button) button.disabled = false;
  }
}

/* ============================================================
   ACCOUNT, LOGIN, REGISTRATION AND LOGOUT
   ============================================================ */

async function loadMe() {
  try {
    const user = await api(CONFIG.meUrl);

    state.user = user && (user.id || user.email || user.username)
      ? user
      : null;
  } catch {
    state.user = null;
  }
}

function openAccount(mode = "login") {
  if (state.user) {
    showModal(`
      <h2>Your Enock account</h2>

      <p>
        <b>${esc(state.user.first_name || state.user.username || "Customer")}</b>
        <br>${esc(state.user.email || "")}
      </p>

      <p class="modal-note">
        Country: ${esc(state.user.country || "Not set")}
        · Currency: ${esc(state.user.currency || "UGX")}
      </p>

      <button type="button"
              class="primary"
              onclick="hideModal();openOrders()">
        View orders
      </button>

      <button type="button"
              onclick="openSellerDashboard()">
        Seller Center
      </button>

      <button type="button"
              onclick="doLogout()">
        Sign out
      </button>
    `);

    return;
  }

  const registering = mode === "register";

  showModal(`
    <h2>${registering ? "Create your account" : "Welcome to Enock"}</h2>

    <form class="form" onsubmit="${
      registering ? "doRegister(event)" : "doLogin(event)"
    }">
      <label for="authEmail">Email address</label>
      <input id="authEmail"
             name="email"
             type="email"
             autocomplete="email"
             required>

      ${registering ? `
        <label for="authName">Full name</label>
        <input id="authName"
               name="name"
               autocomplete="name"
               maxlength="150"
               required>
      ` : ""}

      <label for="authPassword">Password</label>
      <input id="authPassword"
             name="password"
             type="password"
             autocomplete="${registering ? "new-password" : "current-password"}"
             required
             minlength="8">

      <button class="primary" type="submit">
        ${registering ? "Create account" : "Sign in"}
      </button>
    </form>

    <button type="button"
            onclick="openAccount('${registering ? "login" : "register"}')">
      ${registering
        ? "Already have an account? Sign in"
        : "New to Enock? Create an account"}
    </button>

    <p class="modal-note">
      By continuing, you agree to Enock marketplace terms and policies.
    </p>
  `);
}

async function doLogin(event) {
  if (event) event.preventDefault();

  try {
    const user = await api(CONFIG.loginUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: JSON.stringify({
        identifier: $("authEmail").value.trim(),
        password: $("authPassword").value
      })
    });

    state.user = user;
    hideModal();
    updateCounts();
    toast("Welcome back.");
  } catch (error) {
    toast(error.message);
  }
}

async function doRegister(event) {
  if (event) event.preventDefault();

  try {
    const user = await api(CONFIG.registerUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: JSON.stringify({
        email: $("authEmail").value.trim(),
        name: $("authName").value.trim(),
        password: $("authPassword").value
      })
    });

    state.user = user;
    hideModal();
    toast("Account created.");
  } catch (error) {
    toast(error.message);
  }
}

async function doLogout() {
  try {
    await api(CONFIG.logoutUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf() },
      body: JSON.stringify({})
    });

    state.user = null;
    hideModal();
    toast("Signed out.");
  } catch (error) {
    toast(error.message);
  }
}

/* ============================================================
   CUSTOMER ORDERS
   ============================================================ */

async function openOrders() {
  if (!state.user) {
    openAccount("login");
    return;
  }

  try {
    const data = await api(CONFIG.ordersUrl);
    const orders = listFromResponse(data);

    showModal(`
      <h2>Your orders</h2>

      ${orders.length
        ? orders.map(order => `
          <div class="cart-item">
            <div>📦</div>
            <div>
              <b>Order #${esc(order.id)}</b>
              <p class="modal-note">
                ${esc(order.created_at
                  ? new Date(order.created_at).toLocaleString()
                  : "Date unavailable")}
                · ${esc(order.status || "Processing")}
                · ${money(order.total, order.currency || "UGX")}
              </p>
            </div>
          </div>
        `).join("")
        : '<p class="modal-note">No orders yet.</p>'}
    `);
  } catch (error) {
    toast(error.message);
  }
}

/* ============================================================
   SELLER CENTER
   ============================================================ */

async function openSellerDashboard() {
  if (!state.user) {
    openAccount("login");
    return;
  }

  try {
    const data = await api(CONFIG.sellerDashboardUrl);
    const metrics = data.metrics || {};
    const seller = data.seller || {};
    const products = Array.isArray(data.products) ? data.products : [];

    showModal(`
      <h2>Seller Center</h2>

      <div class="stats">
        <div><b>${Number(metrics.products || 0)}</b><small>Products</small></div>
        <div><b>${Number(metrics.orders || 0)}</b><small>Orders</small></div>
        <div><b>${Number(metrics.stock_units || 0)}</b><small>Stock units</small></div>
      </div>

      <p class="modal-note">
        Store: ${esc(seller.store_name || "Seller profile")}
        · ${esc(seller.country || "")}
      </p>

      <h3>Your catalog</h3>

      ${products.length
        ? products.map(product => `
          <div class="cart-item">
            <div>
              <b>${esc(product.name)}</b>
              <p class="modal-note">
                ${money(product.price, product.currency || "UGX")}
              </p>
            </div>
            <span>${Number(product.stock_quantity || 0)} in stock</span>
          </div>
        `).join("")
        : '<p class="modal-note">No products are listed yet.</p>'}

      <p>
        <a href="/seller-center/">Open full Seller Center</a>
      </p>

      <p>
        <a href="/advertising/">Manage advertising campaigns</a>
      </p>
    `);
  } catch (error) {
    toast(error.message);
  }
}

function openSell() {
  if (!state.user) {
    openAccount("login");
    toast("Sign in to start selling.");
    return;
  }

  showModal(`
    <h2>Sell on Enock</h2>

    <p>
      Individuals and businesses can apply to become marketplace sellers.
    </p>

    <form class="form" onsubmit="submitSellerApplication(event)">
      <label for="storeName">Store or seller name</label>
      <input id="storeName" required maxlength="150">

      <label for="sellerType">Seller type</label>
      <select id="sellerType" required>
        <option value="individual">Individual — C2C</option>
        <option value="business">Business — B2C</option>
        <option value="brand">Brand</option>
        <option value="professional">Professional / services</option>
      </select>

      <label for="storeDescription">Store description</label>
      <textarea id="storeDescription"
                maxlength="2000"
                required></textarea>

      <button class="primary" type="submit">
        Submit application
      </button>
    </form>
  `);
}

async function submitSellerApplication(event) {
  event.preventDefault();

  // Connect this form to your actual seller onboarding endpoint.
  // Do not show success until Django confirms the application.
  toast(
    "Seller application API is not configured yet. " +
    "Connect the form to your Django onboarding endpoint."
  );
}

/* ============================================================
   ADVERTISING
   ============================================================ */

async function loadAdverts() {
  if (!CONFIG.advertsUrl) return;

  try {
    const data = await api(CONFIG.advertsUrl);
    state.adverts = listFromResponse(data);
    renderAdverts();
  } catch (error) {
    console.warn("Advertising could not be loaded:", error.message);
  }
}

function renderAdverts() {
  const containers = [
    $("advertisingBanner"),
    $("sponsoredProducts"),
    $("marketplaceAdverts")
  ].filter(Boolean);

  if (!containers.length) return;

  const adverts = state.adverts.filter(advert =>
    advert.status === "approved" &&
    advert.is_paid !== false
  );

  containers.forEach(container => {
    container.innerHTML = adverts.map(advert => `
      <article class="sponsored-ad">
        <span class="ad-label">Sponsored</span>

        ${advert.image
          ? `<img src="${esc(advert.image)}"
                  alt="${esc(advert.title || "Sponsored advert")}"
                  loading="lazy">`
          : ""}

        <h3>${esc(advert.title || "Sponsored advert")}</h3>
        <p>${esc(advert.description || "")}</p>

        ${advert.destination_url
          ? `<a href="${esc(advert.destination_url)}"
                target="_blank"
                rel="noopener noreferrer"
                onclick="recordAdClick(${Number(advert.id)})">
                Learn more
             </a>`
          : ""}
      </article>
    `).join("");
  });
}

async function recordAdClick(id) {
  // Optional: configure a real click-tracking endpoint in Django.
  // Never increment trusted billing metrics solely in the browser.
  console.info("Advert clicked:", id);
}

/* ============================================================
   MULTI-TEMPLATE STOREFRONT HELPERS
   ============================================================ */

function initPage(page) {
  const el = $("pageContent");

  if (page === "marketplace") {
    loadProducts().catch(error => toast(error.message));
    return;
  }

  if (page === "login" || page === "register") return;
  if (!el) return;

  const content = {
    sellers: `
      <p>Discover verified C2C and B2C stores.</p>
      <a class="primary" href="/seller-center/">Open Seller Center</a>
    `,

    cart: `
      <p>Your cart is managed through the Enock checkout flow.</p>
      <button class="primary" onclick="openCart()">View cart</button>
    `,

    wishlist: `
      <p>Your saved products will appear here.</p>
      <button class="primary" onclick="openWishlist()">View wishlist</button>
    `,

    account: `
      <p>Manage your profile, country, currency and account settings.</p>
      <button class="primary" onclick="openAccount()">Open account</button>
    `,

    orders: `
      <p>Your orders and delivery status appear here after sign-in.</p>
      <button class="primary" onclick="openOrders()">View orders</button>
    `,

    checkout: `
      <h2>Secure checkout</h2>
      <p>Review your cart and continue to checkout.</p>
      <button class="primary" onclick="openCheckout()">Continue</button>
    `,

    payment: `
      <h2>Payment methods</h2>
      <div class="feature-grid">
        <article><h3>MTN MoMo</h3><p>Requires provider integration.</p></article>
        <article><h3>Airtel Money</h3><p>Requires provider integration.</p></article>
        <article><h3>International cards</h3><p>Requires a payment processor.</p></article>
      </div>
    `,

    tracking: `
      <h2>Shipment tracking</h2>
      <p>Connect your shipping provider to enable live tracking.</p>
    `,

    seller_dashboard: `
      <h2>Seller Center</h2>
      <p>Manage products, inventory, orders and revenue.</p>
      <a href="/seller-center/">Open Seller Center</a>
    `,

    seller_products: `
      <h2>Your products</h2>
      <p>Manage your marketplace listings in Seller Center.</p>
      <a href="/seller-center/">Open Seller Center</a>
    `,

    seller_orders: `
      <h2>Seller orders</h2>
      <p>Review and process customer orders.</p>
      <a href="/seller-center/">Open Seller Center</a>
    `,

    returns: `
      <h2>Returns and refunds</h2>
      <p>Return requests and refund processing must be handled by Django.</p>
    `
  };

  el.innerHTML = content[page] || "<p>Page ready.</p>";
}

/* ============================================================
   GLOBAL HANDLERS USED BY HTML onclick ATTRIBUTES
   ============================================================ */

Object.assign(window, {
  go,
  loadNav,
  toggleNav,
  closeModal,
  hideModal,
  showModal,
  openProduct,
  filterCategory,
  clearCategoryFilter,
  searchProducts,
  handleSearchSubmit,
  toggleWish,
  openWishlist,
  addCart,
  changeQty,
  removeFromCart,
  openCart,
  openCheckout,
  submitCheckout,
  openAccount,
  doLogin,
  doRegister,
  doLogout,
  openOrders,
  openSellerDashboard,
  openSell,
  submitSellerApplication,
  initPage,
  loadProducts
});

window.addEventListener("hashchange", () => {
  if (location.hash === "#orders") {
    openOrders();
  }
});

window.addEventListener("storage", event => {
  if (event.key === "enock_cart" || event.key === "enock_wishlist") {
    state.cart = readStorage("enock_cart", []);
    state.wishlist = readStorage("enock_wishlist", []);
    updateCounts();
    renderProducts();
  }
});
