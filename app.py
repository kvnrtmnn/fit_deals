from flask import Flask, render_template, request, redirect, url_for
from scraper import get_smilodox_deals, get_oace_deals, get_more_deals, get_teveo_deals, get_oceansapart_deals, get_gymshark_deals
import time
import math

app = Flask(__name__)

CACHE_TIMEOUT = 900 
data_cache = {"deals": [], "timestamp": 0}

def get_all_data():
    current_time = time.time()
    if current_time - data_cache["timestamp"] > CACHE_TIMEOUT or not data_cache["deals"]:
        print("Cache abgelaufen. Hole frische Daten...")
        smilo = get_smilodox_deals()
        oace = get_oace_deals()
        more = get_more_deals()
        teveo = get_teveo_deals()
        oceansapart = get_oceansapart_deals()
        gymshark = get_gymshark_deals()
        
        all_deals = smilo + oace + more + teveo + oceansapart + gymshark
        # Standard-Sortierung beim Laden ist Rabatt
        all_deals.sort(key=lambda x: x['discount'], reverse=True)
        
        data_cache["deals"] = all_deals
        data_cache["timestamp"] = current_time
    return data_cache["deals"]

@app.route('/')
def landing_page():
    return render_template('landing.html')

@app.route('/deals')
def deals_page():
    deals = get_all_data()
    
    # 1. Parameter lesen
    store_filter = request.args.get('store', 'all')
    min_discount = request.args.get('min_discount', 0, type=float)
    desired_sizes = request.args.getlist('filter_size')
    
    # NEU: Sortier-Parameter (Standard: 'discount_desc')
    sort_order = request.args.get('sort', 'discount_desc')
    
    filtered_deals = []

    # 2. Filtern
    for deal in deals:
        if store_filter != 'all' and deal['shop'].lower().replace(' ', '') != store_filter.lower().replace(' ', ''):
            continue
        if deal['discount'] < min_discount:
            continue
        if desired_sizes:
            deal_sizes_set = set(deal['sizes'])
            wanted_sizes_set = set(desired_sizes)
            if not deal_sizes_set.intersection(wanted_sizes_set):
                continue
        filtered_deals.append(deal)
    
    # 3. SORTIEREN (Das ist neu)
    if sort_order == 'price_asc':
        # Preis tief -> hoch
        filtered_deals.sort(key=lambda x: x['price'])
    elif sort_order == 'price_desc':
        # Preis hoch -> tief
        filtered_deals.sort(key=lambda x: x['price'], reverse=True)
    elif sort_order == 'name_asc':
        # A-Z (Titel)
        filtered_deals.sort(key=lambda x: x['title'].lower())
    else:
        # Standard: Bester Rabatt zuerst (discount_desc)
        filtered_deals.sort(key=lambda x: x['discount'], reverse=True)

    # 4. Paginierung
    page = request.args.get('page', 1, type=int)
    per_page = 24
    total_deals = len(filtered_deals)
    total_pages = math.ceil(total_deals / per_page)
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    start = (page - 1) * per_page
    end = start + per_page
    current_page_deals = filtered_deals[start:end]
    
    return render_template(
        'index.html', 
        deals=current_page_deals,
        page=page,
        total_pages=total_pages,
        total_deals=total_deals,
        current_store=store_filter,
        current_min_discount=min_discount,
        current_desired_sizes=desired_sizes,
        # WICHTIG: Sortier-Option an Template übergeben, damit es im Dropdown ausgewählt bleibt
        current_sort=sort_order 
    )

@app.route('/refresh')
def refresh():
    data_cache["timestamp"] = 0
    store = request.args.get('store', 'all')
    return redirect(url_for('deals_page', store=store))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
