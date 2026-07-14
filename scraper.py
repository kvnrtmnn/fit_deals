import requests

# Hilfsfunktion: Bild holen
def get_variant_image(product, variant):
    if variant.get('featured_image') and 'src' in variant['featured_image']:
        return variant['featured_image']['src']
    images = product.get('images', [])
    if images:
        return images[0].get('src')
    return "https://via.placeholder.com/300?text=Kein+Bild"

# Hilfsfunktion: Größe und Farbe trennen
def extract_size_and_color(variant):
    options = [variant.get('option1'), variant.get('option2'), variant.get('option3')]
    options = [o for o in options if o]
    
    # Mapping: ausgeschriebene Größen (z.B. Gymshark) → Abkürzung
    SIZE_MAP = {
        "extra extra extra extra large": "4XL",
        "extra extra extra large": "3XL",
        "extra extra small": "XXS",
        "extra extra large": "XXL",
        "extra small": "XS",
        "extra large": "XL",
        "small": "S",
        "medium": "M",
        "large": "L",
        "one size": "One Size",
        "default title": None,  # Produkte ohne echte Variante → ignorieren
    }
    
    # Erweiterte Liste bekannter Größen
    known_sizes = set(["XXS", "XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL", 
                       "34", "36", "38", "40", "42", "44", "46", "48", "One Size"])
    
    size = "Unbekannt"
    style_info = []
    found_size = False
    
    for opt in options:
        opt_lower = opt.strip().lower()
        
        # 1. Prüfe Langform-Mapping
        if not found_size and opt_lower in SIZE_MAP:
            mapped = SIZE_MAP[opt_lower]
            if mapped is not None:
                size = mapped
                found_size = True
            # None-Mapping (z.B. "Default Title") → als style_info ignorieren
            continue
        
        # 2. Prüfe Kurzform (XS, M, XL, ...)
        if not found_size and (opt in known_sizes or opt.upper() in known_sizes):
            size = opt.upper() if opt.upper() in known_sizes else opt
            found_size = True
        
        # 3. Schuhgrößen (UK/EU/US-Format) → als Größe übernehmen
        elif not found_size and ("UK" in opt or "EU" in opt):
            size = opt
            found_size = True
        else:
            style_info.append(opt)
            
    style_name = " / ".join(style_info) if style_info else "Standard"
    # Fallback: Accessoires o.ä. ohne erkennbare Größe → "One Size"
    if size == "Unbekannt":
        size = "One Size"
    return size, style_name


def fetch_deals(url, shop_name, gender_keywords=None):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Wir sammeln ALLES, was verfügbar ist und Rabatt hat.
    # Gefiltert wird später in der App.
    min_discount_threshold = 1.0 # Mindestens 1% Rabatt, um UVP-Ware rauszuwerfen
    
    grouped_deals = {}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        for product in data['products']:
            # Gender Check (falls gewünscht, z.B. bei Smilo)
            if gender_keywords:
                tags = " ".join(product.get('tags', [])).lower()
                combined = f"{product['title'].lower()} {tags}"
                # Wenn nicht unisex und eines der "Ausschluss-Wörter" drin ist -> weg
                if "unisex" not in combined and any(k in combined for k in gender_keywords):
                    continue

            product_base_url = f"https://{url.split('/')[2]}/products/{product['handle']}"
            
            for variant in product['variants']:
                if not variant.get('available', True): continue

                size, style_name = extract_size_and_color(variant)

                try:
                    price = float(variant['price'])
                    compare = float(variant.get('compare_at_price') or 0)
                    
                    if compare > 0:
                        discount = round((1 - (price / compare)) * 100, 1)
                        if discount >= min_discount_threshold:
                            
                            # Gruppieren nach ID + Farbe + Preis
                            group_key = f"{product['id']}_{style_name}_{price}"
                            
                            if group_key not in grouped_deals:
                                image_url = get_variant_image(product, variant)
                                grouped_deals[group_key] = {
                                    'shop': shop_name,
                                    'title': product['title'],
                                    'style': style_name,
                                    'price': price,
                                    'old_price': compare,
                                    'discount': discount,
                                    'url': f"{product_base_url}?variant={variant['id']}",
                                    'image': image_url,
                                    'sizes': [size]
                                }
                            else:
                                if size not in grouped_deals[group_key]['sizes']:
                                    grouped_deals[group_key]['sizes'].append(size)

                except ValueError: continue
                
    except Exception as e:
        print(f"Fehler bei {shop_name}: {e}")

    results = list(grouped_deals.values())
    for item in results:
        item['sizes'].sort() 
        
    return results

# --- Hauptfunktionen ---
# Wir übergeben hier KEINE Filter mehr, sondern holen alles.

def get_smilodox_deals():
    # Smilodox: Wir filtern hier nur "Damen" raus, weil das meist gewünscht ist.
    # Größen lassen wir alle drin.
    return fetch_deals(
        url="https://smilodox.com/products.json?limit=250",
        shop_name="Smilodox",
        gender_keywords=["damen", "women", "woman", "female"]
    )

def get_oace_deals():
    return fetch_deals(
        url="https://oace.de/products.json?limit=250",
        shop_name="OACE"
    )

def get_more_deals():
    return fetch_deals(
        url="https://morenutrition.de/products.json?limit=250",
        shop_name="More"
    )

def get_teveo_deals():
    return fetch_deals(
        url="https://teveo.com/products.json?limit=250",
        shop_name="Teveo"
    )

def get_oceansapart_deals():
    return fetch_deals(
        url="https://www.oceansapart.com/de-de/products.json?limit=250",
        shop_name="Oceans Apart"
    )

def get_gymshark_deals():
    return fetch_deals(
        url="https://gymshark.com/products.json?limit=250",
        shop_name="Gymshark"
    )

