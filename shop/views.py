from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils.http import urlencode
from urllib.parse import quote
from .models import Product, Category
from decimal import Decimal


def home(request):
    category_slug = request.GET.get('categoria')
    categories = Category.objects.all()
    if category_slug:
        products = Product.objects.filter(
            available=True, category__slug=category_slug
        )
    else:
        products = Product.objects.filter(available=True)
    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related = Product.objects.filter(
        category=product.category, available=True
    ).exclude(id=product.id)[:4]
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related': related,
    })


@require_POST
def cart_add(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    pid = str(product.id)
    cart[pid] = cart.get(pid, 0) + 1
    request.session['cart'] = cart
    return redirect('shop:cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})
    items = []
    total = Decimal('0')
    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
        except Product.DoesNotExist:
            continue
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


@require_POST
def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('shop:cart_detail')


@require_POST
def cart_update(request, product_id):
    qty = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    if qty > 0:
        cart[str(product_id)] = qty
    else:
        cart.pop(str(product_id), None)
    request.session['cart'] = cart
    return redirect('shop:cart_detail')


# ============ NUEVO: GENERAR MENSAJE DEL CARRITO ============

def _build_order_message(items, total, customer_name=None, customer_note=None):
    """
    Construye el texto con el detalle del carrito.
    Se reutiliza para WhatsApp y para correo.
    """
    store = settings.STORE_NAME
    lines = [f"*Nuevo pedido en {store}* 🛍️", ""]

    if customer_name:
        lines.append(f"👤 *Cliente:* {customer_name}")
        lines.append("")

    lines.append("*Productos:*")
    for item in items:
        p = item['product']
        lines.append(
            f"• {p.name} — {item['quantity']} x ${p.price} = ${item['subtotal']}"
        )

    lines.append("")
    lines.append(f"💰 *TOTAL:* ${total}")
    lines.append("")

    if customer_note:
        lines.append(f"📝 *Nota:* {customer_note}")
        lines.append("")

    lines.append("Gracias por tu compra ✨")
    return "\n".join(lines)


def checkout(request):
    """
    Pantalla para elegir el método de envío del pedido (WhatsApp o correo).
    Recalcula el carrito por seguridad.
    """
    cart = request.session.get('cart', {})
    items = []
    total = Decimal('0')
    for pid, qty in cart.items():
        try:
            product = Product.objects.get(id=pid)
        except Product.DoesNotExist:
            continue
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

    if not items:
        return redirect('shop:cart_detail')

    message = _build_order_message(items, total)

    # WhatsApp: wa.me usa query string ?text=
    whatsapp_url = f"https://wa.me/{settings.WHATSAPP_NUMBER}?{urlencode({'text': message})}"

    # Correo: mailto: con asunto y cuerpo codificados
    subject = f"Nuevo pedido en {settings.STORE_NAME}"
    mailto_url = (
        f"mailto:{settings.STORE_EMAIL}"
        f"?subject={quote(subject)}"
        f"&body={quote(message)}"
    )

    return render(request, 'shop/checkout.html', {
        'items': items,
        'total': total,
        'message': message,
        'whatsapp_url': whatsapp_url,
        'mailto_url': mailto_url,
    })
