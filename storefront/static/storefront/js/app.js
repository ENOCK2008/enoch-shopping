const state = { products: [], categories: [], sellers: [], cart: JSON.parse(localStorage.getItem("enock_cart") || "[]"), wishlist: JSON.parse(localStorage.getItem("enock_wishlist") || "[]"), user: null };

const $ = (id) => document.getElementById(id);
const api = async (url, options={}) => {
  const res = await fetch(url, {credentials:"same-origin", headers:{"Content-Type":"application/json", ...(options.headers||{})}, ...options});
  const data = await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.detail || "Request failed");
  return data;
};
function csrf(){ const m=document.cookie.match(/(?:^|; )csrftoken=([^;]+)/); return m ? decodeURIComponent(m[1]) : ""; }
function money(value, currency="UGX"){ try{return new Intl.NumberFormat(undefined,{style:"currency",currency}).format(Number(value));}catch{return `${currency} ${Number(value).toLocaleString()}`;} }
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
function toast(msg){$("toast").textContent=msg;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),2500);}
function save(){localStorage.setItem("enock_cart",JSON.stringify(state.cart));localStorage.setItem("enock_wishlist",JSON.stringify(state.wishlist));updateCounts();}
function updateCounts(){$("cartCount").textContent=state.cart.reduce((n,i)=>n+i.quantity,0);$("wishCount").textContent=state.wishlist.length;}
function showModal(html){$("modalContent").innerHTML=html;$("modal").classList.add("show");}
function hideModal(){$("modal").classList.remove("show");}
function closeModal(e){if(e.target.id==="modal")hideModal();}
function go(id){document.getElementById(id)?.scrollIntoView({behavior:"smooth"});loadNav(id);}
function loadNav(id){history.replaceState(null,"",`#${id}`);}
function toggleNav(){document.getElementById("mainNav").style.display=document.getElementById("mainNav").style.display==="flex"?"none":"flex";}

async function init(){
  await api("/api/users/csrf/");
  await Promise.all([loadCategories(),loadProducts(),loadSellers(),loadMe()]);
  updateCounts();
}
async function loadCategories(){
  const d=await api("/api/catalog/categories/"); state.categories=d.results||d;
  const icons=["🛍️","📱","💻","👕","🏠","🎮","🚗","💄","⚽","📚","🔧","🎁"];
  $("categories").innerHTML=state.categories.slice(0,12).map((c,i)=>`<div class="category-card" onclick="filterCategory(${c.id})"><div class="emoji">${icons[i%icons.length]}</div><h4>${esc(c.name)}</h4></div>`).join("") || `<div class="loading">Categories will appear here.</div>`;
}
async function loadProducts(search=""){
  const sort=$("sortSelect")?.value || "-created_at";
  const q=search ? `&search=${encodeURIComponent(search)}`:"";
  const d=await api(`/api/catalog/products/?ordering=${encodeURIComponent(sort)}${q}`);
  state.products=d.results||d;
  $("resultText").textContent=search ? `${state.products.length} results for “${search}”` : "Fresh listings from Enock sellers.";
  renderProducts();
}
function renderProducts(){
  if(!state.products.length){$("productGrid").innerHTML='<div class="loading">No products found. Try another search.</div>';return;}
  $("productGrid").innerHTML=state.products.map(p=>{
    const liked=state.wishlist.includes(p.id);
    return `<article class="product">
      <button class="heart" onclick="toggleWish(${p.id})">${liked?"♥":"♡"}</button>
      <div class="product-img" onclick="openProduct(${p.id})">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)}">`:"🛍️"}</div>
      <div class="product-body">
        <h3 title="${esc(p.name)}">${esc(p.name)}</h3>
        <div class="seller-line">${esc(p.seller_name||"Enock seller")} ${p.seller_verified?'<span class="verified">✓</span>':""}</div>
        <div class="price">${money(p.price,p.currency)}</div>
        <div class="stock">${p.stock_quantity>0?`${p.stock_quantity} available`:"Out of stock"}</div>
        <div class="product-actions"><button onclick="openProduct(${p.id})">Details</button><button onclick="addCart(${p.id})" ${p.stock_quantity<1?"disabled":""}>Add to cart</button></div>
      </div>
    </article>`;
  }).join("");
}
async function filterCategory(id){go("market");const d=await api(`/api/catalog/products/?category=${id}`);state.products=d.results||d;renderProducts();}
async function searchProducts(q){go("market");await loadProducts(q.trim());}
async function loadSellers(){
  const d=await api("/api/sellers/");state.sellers=d.results||d;
  $("sellerGrid").innerHTML=state.sellers.slice(0,6).map(s=>`<article class="seller-card"><div class="seller-avatar">${esc((s.store_name||"E")[0].toUpperCase())}</div><div><h3>${esc(s.store_name)} ${s.verified?"✓":""}</h3><p>${esc(s.country||"International")} · ${esc(s.description||"Marketplace seller")}</p></div></article>`).join("") || `<div class="loading">Seller stores will appear here.</div>`;
}
async function loadMe(){try{state.user=await api("/api/users/me/")}catch{state.user=null}}
function openProduct(id){
  const p=state.products.find(x=>x.id===id);if(!p)return;
  showModal(`<div class="product-detail"><div class="product-img" style="height:260px;border-radius:15px">${p.image?`<img src="${esc(p.image)}" alt="${esc(p.name)}">`:"🛍️"}</div><h2>${esc(p.name)}</h2><div class="seller-line">${esc(p.seller_name)} ${p.seller_verified?'<span class="verified">✓ Verified seller</span>':""}</div><div class="price">${money(p.price,p.currency)}</div><p>${esc(p.description||"No description provided.")}</p><p class="modal-note">SKU: ${esc(p.sku)} · ${p.stock_quantity} available · Category: ${esc(p.category_name||"General")}</p><button class="primary" onclick="addCart(${p.id});hideModal()">Add to cart</button></div>`);
}
function toggleWish(id){const i=state.wishlist.indexOf(id);i>=0?state.wishlist.splice(i,1):state.wishlist.push(id);save();renderProducts();}
function openWishlist(){const ps=state.products.filter(p=>state.wishlist.includes(p.id));showModal(`<h2>Your wishlist</h2>${ps.length?ps.map(p=>`<div class="cart-item"><div style="font-size:30px">♡</div><div><b>${esc(p.name)}</b><p class="modal-note">${money(p.price,p.currency)}</p></div><button class="primary" onclick="addCart(${p.id})">Add</button></div>`).join(""):'<p class="modal-note">Your wishlist is empty. Tap ♡ on products you love.</p>'}`);}
function addCart(id){const p=state.products.find(x=>x.id===id);if(!p)return;const item=state.cart.find(x=>x.product_id===id);if(item)item.quantity=Math.min(item.quantity+1,p.stock_quantity);else state.cart.push({product_id:id,quantity:1,name:p.name,price:p.price,currency:p.currency,image:p.image||""});save();toast("Added to your cart");}
function changeQty(id,delta){const i=state.cart.findIndex(x=>x.product_id===id);if(i<0)return;state.cart[i].quantity+=delta;if(state.cart[i].quantity<1)state.cart.splice(i,1);save();openCart();}
function openCart(){const total=state.cart.reduce((n,i)=>n+Number(i.price)*i.quantity,0);const cur=state.cart[0]?.currency||"UGX";showModal(`<h2>Your cart</h2>${state.cart.length?state.cart.map(i=>`<div class="cart-item"><div>${i.image?`<img src="${esc(i.image)}" style="width:55px;height:55px;object-fit:cover;border-radius:9px">`:"🛍️"}</div><div><b>${esc(i.name)}</b><p class="modal-note">${money(i.price,i.currency)}</p><div class="cart-qty"><button onclick="changeQty(${i.product_id},-1)">−</button><span>${i.quantity}</span><button onclick="changeQty(${i.product_id},1)">+</button></div></div><b>${money(Number(i.price)*i.quantity,i.currency)}</b></div>`).join("")+`<div class="total-row"><span>Total</span><span>${money(total,cur)}</span></div><button class="primary" style="width:100%" onclick="openCheckout()">Checkout</button>`:'<p class="modal-note">Your cart is empty.</p>'}`);}
function openCheckout(){
  if(!state.cart.length)return;
  if(!state.user){openAccount("login");toast("Please sign in before checkout");return;}
  showModal(`<h2>Secure checkout</h2><p class="modal-note">You are ordering as <b>${esc(state.user.email)}</b>. Payment providers can be connected to this checkout.</p><form class="form" onsubmit="submitCheckout(event)"><textarea id="shipAddress" required placeholder="Full delivery address"></textarea><input id="shipCountry" required value="${esc(state.user.country||"Uganda")}" placeholder="Country"><select id="paymentMethod"><option value="cash_on_delivery">Cash on delivery</option><option value="card">Card — integration ready</option><option value="mobile_money">Mobile money — integration ready</option><option value="wallet">Enock Wallet — coming next</option></select><button class="primary" type="submit">Place order</button></form>`);
}
async function submitCheckout(e){e.preventDefault();try{const order=await api("/api/orders/checkout/",{method:"POST",headers:{"X-CSRFToken":csrf()},body:JSON.stringify({items:state.cart.map(i=>({product_id:i.product_id,quantity:i.quantity})),shipping_address:$("shipAddress").value,shipping_country:$("shipCountry").value,payment_method:$("paymentMethod").value})});state.cart=[];save();hideModal();toast(`Order #${order.id} placed`);go("orders");}catch(err){toast(err.message);}}
function openAccount(mode="login"){
  if(state.user){showModal(`<h2>Your Enock account</h2><p><b>${esc(state.user.first_name||state.user.username)}</b><br>${esc(state.user.email)}</p><p class="modal-note">Country: ${esc(state.user.country)} · Currency: ${esc(state.user.currency)}</p><button class="primary" onclick="go('orders');hideModal()">View orders</button> <button onclick="openSellerDashboard()" style="padding:12px;border-radius:10px;background:var(--soft)">Seller Center</button> <button onclick="doLogout()" style="padding:12px;border-radius:10px;background:var(--soft)">Sign out</button>`);return;}
  showModal(`<h2>Welcome to Enock</h2><div class="form"><input id="authEmail" type="email" placeholder="Email" required><input id="authPassword" type="password" placeholder="Password" required>${mode==="register"?'<input id="authName" placeholder="Full name">':""}<button class="primary" onclick="${mode==="register"?"doRegister()":"doLogin()"}">${mode==="register"?"Create account":"Sign in"}</button><button onclick="openAccount('${mode==="register"?"login":"register"}')" style="padding:10px;background:none;color:var(--brand)">${mode==="register"?"Already have an account? Sign in":"New to Enock? Create an account"}</button></div><p class="modal-note">By continuing, you agree to Enock marketplace terms and buyer/seller policies.</p>`);
}
async function doLogin(){try{state.user=await api("/api/users/login/",{method:"POST",headers:{"X-CSRFToken":csrf()},body:JSON.stringify({identifier:$("authEmail").value,password:$("authPassword").value})});hideModal();toast("Welcome back");}catch(e){toast(e.message);}}
async function doRegister(){try{state.user=await api("/api/users/register/",{method:"POST",headers:{"X-CSRFToken":csrf()},body:JSON.stringify({email:$("authEmail").value,password:$("authPassword").value,name:$("authName").value})});hideModal();toast("Your Enock account is ready");}catch(e){toast(e.message);}}
async function doLogout(){try{await api("/api/users/logout/",{method:"POST",headers:{"X-CSRFToken":csrf()}});state.user=null;hideModal();toast("Signed out");}catch(e){toast(e.message);}}
function openOrders(){
  if(!state.user){openAccount("login");return;}
  api("/api/orders/").then(d=>{const orders=d.results||d;showModal(`<h2>Your orders</h2>${orders.length?orders.map(o=>`<div class="cart-item"><div>📦</div><div><b>Order #${o.id}</b><p class="modal-note">${new Date(o.created_at).toLocaleString()} · ${esc(o.status)} · ${money(o.total,o.currency)}</p></div></div>`).join(""):'<p class="modal-note">No orders yet.</p>'}`)}).catch(e=>toast(e.message));
}
async function openSellerDashboard(){
  if(!state.user){openAccount("login");return;}
  try{
    const d=await api("/api/sellers/dashboard/");
    showModal(`<h2>Seller Center</h2><div class="stats"><div><b>${d.metrics.products}</b><small>Products</small></div><div><b>${d.metrics.orders}</b><small>Orders</small></div><div><b>${d.metrics.stock_units}</b><small>Stock units</small></div></div><p class="modal-note">Store: ${esc(d.seller.store_name)} · ${esc(d.seller.country)}</p><h3>Catalog</h3>${d.products.map(p=>`<div class="cart-item"><div><b>${esc(p.name)}</b><p class="modal-note">${money(p.price,p.currency)}</p></div><span>${p.stock_quantity} in stock</span></div>`).join("")}`);
  }catch(e){toast(e.message);}
}
function openSell(){showModal(`<h2>Sell on Enock</h2><p>Individuals and businesses can become C2C or B2C sellers. Seller onboarding is prepared in the backend.</p><div class="form"><input placeholder="Store / seller name"><select><option>Individual — C2C</option><option>Business — B2C</option><option>Brand</option><option>Professional / services</option></select><textarea placeholder="Tell customers about your store"></textarea><button class="primary" onclick="toast('Seller onboarding endpoint is ready for the next workflow step');hideModal()">Continue</button></div>`);}
window.openOrders=openOrders;
document.addEventListener("DOMContentLoaded",()=>{init().catch(e=>console.error(e));});
window.addEventListener("hashchange",()=>{if(location.hash==="#orders")openOrders();});

// Multi-template storefront helpers
function initPage(page) {
  const el = document.getElementById('pageContent');
  if (page === 'marketplace') { if (typeof loadProducts === 'function') loadProducts(); return; }
  if (page === 'login' || page === 'register') return;
  if (!el) return;
  const content = {
    sellers: '<p>Discover verified C2C and B2C stores.</p><a class="primary" href="/seller-center/">Open Seller Center</a>',
    cart: '<p>Your cart is managed through the Enock checkout flow.</p><a class="primary" href="/checkout/">Proceed to checkout</a>',
    wishlist: '<p>Your saved products will appear here.</p>',
    account: '<p>Manage your profile, country, currency and account settings.</p><a class="primary" href="/login/">Sign in</a>',
    orders: '<p>Your orders and delivery status will appear here after sign-in.</p>',
    order_detail: '<p>Order details and payment status will appear here.</p>',
    checkout: '<h2>Secure checkout</h2><p>Choose delivery and continue to payment.</p><a class="primary" href="/payment/">Continue to payment</a>',
    payment: '<h2>Choose payment</h2><div class="feature-grid"><article><h3>MTN MoMo</h3><p>Uganda mobile-money checkout.</p></article><article><h3>Airtel Money</h3><p>Uganda mobile-money checkout.</p></article><article><h3>International cards</h3><p>Processor-ready card payment architecture.</p></article></div>',
    tracking: '<h2>DHL Express tracking</h2><p>Enter your tracking number to retrieve the latest shipment status.</p><form class="form-card" onsubmit="event.preventDefault(); alert(\'Connect DHL credentials to enable live tracking.\')"><label>Tracking number<input required></label><button class="primary">Track shipment</button></form>',
    seller_dashboard: '<h2>Seller Center</h2><p>Manage products, inventory, orders and revenue.</p><div class="feature-grid"><article><h3>Dashboard</h3><a href="/seller-center/products/">Products</a></article><article><h3>Orders</h3><a href="/seller-center/orders/">Seller orders</a></article></div>',
    seller_products: '<h2>Your products</h2><p>Create and manage marketplace listings through the seller API.</p>',
    seller_orders: '<h2>Seller orders</h2><p>Review, process and ship customer orders.</p>',
    returns: '<h2>Returns & refunds</h2><p>Submit and monitor return requests and refund status.</p>'
  };
  el.innerHTML = content[page] || '<p>Page ready.</p>';
}
