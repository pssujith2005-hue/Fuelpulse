import json
import random
import re
import datetime
from datetime import timedelta
from itertools import chain
from operator import attrgetter
from urllib.parse import quote_plus

# --- Django Core & Utils Imports ---
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import OperationalError, ProgrammingError

# --- Django Auth Imports ---
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User  # Standard Django User

# --- Django Database Imports ---
from django.db.models import Sum, Avg, Q
from django.db.models.functions import TruncMonth

# --- Third-Party Libraries ---
import numpy as np
import pandas as pd
import pytesseract
from PIL import Image
from sklearn.linear_model import LinearRegression
from openai import OpenAI

# --- YOUR PROJECT MODELS (Local Imports) ---
from .models import Vehicle, FuelLog, ExpenseLog, TripLog, MaintenanceLog, NewCar
from .forms import (
    VehicleForm, CustomUserCreationForm, UserUpdateForm, 
    TripLogForm, ExpenseLogForm, CarRecommendationForm,
    TripCalculatorForm, FuelLogForm, NewCarForm
)

# --- 1. EXTENSIVE INDIAN CAR DATABASE ---
BUDGET_CARS = [
    # --- HATCHBACKS ---
    {'make': 'Maruti', 'model': 'Alto K10', 'type': 'Hatchback', 'price': '3.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/1/12/Maruti_Suzuki_Alto_K10_%28third_generation%29_front_view_%2801%29.jpg'},
    {'make': 'Maruti', 'model': 'S-Presso', 'type': 'Hatchback', 'price': '4.26 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/35/Maruti_Suzuki_S-Presso_VXi%2B_front_view.jpg'},
    {'make': 'Renault', 'model': 'Kwid', 'type': 'Hatchback', 'price': '4.69 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/6d/2019_Renault_Kwid_RXT_1.0_Easy-R_%28facelift%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Celerio', 'type': 'Hatchback', 'price': '5.37 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/08/2021_Maruti_Suzuki_Celerio_ZXi%2B_%28India%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Wagon R', 'type': 'Hatchback', 'price': '5.54 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/7/7e/2019_Maruti_Suzuki_WagonR_VXi_1.2_front_view.jpg'},
    {'make': 'Tata', 'model': 'Tiago', 'type': 'Hatchback', 'price': '5.60 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/87/Tata_Tiago_XZ%2B_%28facelift%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Ignis', 'type': 'Hatchback', 'price': '5.84 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/a/a3/Suzuki_Ignis_Hybrid_MF_2022.jpg'},
    {'make': 'Maruti', 'model': 'Swift', 'type': 'Hatchback', 'price': '5.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/07/2024_Suzuki_Swift_Hybrid_MZ_%28Europe%29_front_view_01.jpg'},
    {'make': 'Maruti', 'model': 'Baleno', 'type': 'Hatchback', 'price': '6.66 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/2/23/2022_Maruti_Suzuki_Baleno_Alpha_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Grand i10 Nios', 'type': 'Hatchback', 'price': '5.92 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/5/53/2023_Hyundai_Grand_i10_Nios_Asta_AMT_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'i20', 'type': 'Hatchback', 'price': '7.04 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/a/a2/2020_Hyundai_i20_Asta_%28O%29_1.0_Turbo_DCT_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Altroz', 'type': 'Hatchback', 'price': '6.65 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/34/2020_Tata_Altroz_XZ_1.2_front_view.jpg'},
    {'make': 'Toyota', 'model': 'Glanza', 'type': 'Hatchback', 'price': '6.86 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/d/d4/2022_Toyota_Glanza_V_%28India%29_front_view.jpg'},
    {'make': 'Citroen', 'model': 'C3', 'type': 'Hatchback', 'price': '6.16 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/c/c2/2022_Citro%C3%ABn_C3_Feel_PureTech_82_%28India%29_front_view.jpg'},

    # --- SEDANS ---
    {'make': 'Maruti', 'model': 'Dzire', 'type': 'Sedan', 'price': '6.57 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/1/14/2018_Maruti_Suzuki_Dzire_ZXi_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Ciaz', 'type': 'Sedan', 'price': '9.40 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/2/22/2018_Maruti_Suzuki_Ciaz_Alpha_SHVS_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Aura', 'type': 'Sedan', 'price': '6.49 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/69/2023_Hyundai_Aura_SX_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Verna', 'type': 'Sedan', 'price': '11.00 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/2023_Hyundai_Verna_SX%28O%29_Turbo_DCT_%28India%29_front_view_01.jpg'},
    {'make': 'Tata', 'model': 'Tigor', 'type': 'Sedan', 'price': '6.30 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/7/77/Tata_Tigor_XZ_%28facelift%29_front_view.jpg'},
    {'make': 'Honda', 'model': 'Amaze', 'type': 'Sedan', 'price': '7.20 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/36/Honda_Amaze_%28second_generation%29_%28facelift%29_1.2_VX_CVT_%28India%29_front_view.jpg'},
    {'make': 'Honda', 'model': 'City', 'type': 'Sedan', 'price': '11.82 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/36/Honda_City_%28seventh_generation%29_%28facelift%29_1.5_ZX_CVT_%28India%29_front_view.jpg'},
    {'make': 'Skoda', 'model': 'Slavia', 'type': 'Sedan', 'price': '10.69 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/07/2022_Skoda_Slavia_1.0_TSI_Style_%28India%29_front_view.jpg'},
    {'make': 'Volkswagen', 'model': 'Virtus', 'type': 'Sedan', 'price': '10.89 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/08/2022_Volkswagen_Virtus_GT_Plus_%28India%29_front_view.jpg'},

    # --- SUVs ---
    {'make': 'Maruti', 'model': 'Brezza', 'type': 'SUV', 'price': '8.34 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/05/2022_Maruti_Suzuki_Brezza_ZXi_%28India%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Fronx', 'type': 'SUV', 'price': '7.51 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/4/4b/2023_Maruti_Suzuki_Fronx_Alpha_%28India%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Grand Vitara', 'type': 'SUV', 'price': '10.80 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/08/2022_Maruti_Suzuki_Grand_Vitara_Alpha_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Ertiga', 'type': 'SUV', 'price': '8.69 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/f/f5/2022_Maruti_Suzuki_Ertiga_ZXi%2B_%28India%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'XL6', 'type': 'SUV', 'price': '11.61 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/4/4c/2022_Maruti_Suzuki_XL6_Alpha_%28India%29_front_view.jpg'},
    {'make': 'Maruti', 'model': 'Jimny', 'type': 'SUV', 'price': '12.74 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/82/Suzuki_Jimny_5-door_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Exter', 'type': 'SUV', 'price': '6.13 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/e/e8/2023_Hyundai_Exter_SX%28O%29_Connect_1.2_AMT_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Venue', 'type': 'SUV', 'price': '7.94 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/87/2023_Hyundai_Venue_SX%28O%29_Turbo_IMT_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Creta', 'type': 'SUV', 'price': '11.00 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/c/c2/2024_Hyundai_Creta_SX%28O%29_%28India%29_front_view_03.jpg'},
    {'make': 'Hyundai', 'model': 'Alcazar', 'type': 'SUV', 'price': '16.77 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/2/2b/2021_Hyundai_Alcazar_Signature_2.0_%28India%29_front_view.jpg'},
    {'make': 'Hyundai', 'model': 'Tucson', 'type': 'SUV', 'price': '29.02 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/38/2022_Hyundai_Tucson_2.0_CRDi_4WD_H-Trac_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Punch', 'type': 'SUV', 'price': '6.13 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/6d/Tata_Punch_Creative_AMT_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Nexon', 'type': 'SUV', 'price': '8.15 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/c/cd/2023_Tata_Nexon_Creative_%2B_front_view.jpg'},
    {'make': 'Tata', 'model': 'Harrier', 'type': 'SUV', 'price': '15.49 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/5/5e/2023_Tata_Harrier_Fearless_%2B_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Safari', 'type': 'SUV', 'price': '16.19 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/63/2023_Tata_Safari_Accomplished_%2B_%28India%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'XUV 3XO', 'type': 'SUV', 'price': '7.49 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/2/23/Mahindra_XUV_3XO_2025.jpg'},
    {'make': 'Mahindra', 'model': 'Bolero', 'type': 'SUV', 'price': '9.79 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/84/Mahindra_Bolero_Neo_N10_%28O%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'Thar', 'type': 'SUV', 'price': '11.35 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/f/f6/2020_Mahindra_Thar_LX_Hard_Top_Diesel_%28India%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'Scorpio Classic', 'type': 'SUV', 'price': '13.62 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/8a/2022_Mahindra_Scorpio-N_Z8L_%28India%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'Scorpio N', 'type': 'SUV', 'price': '13.85 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/8/8a/2022_Mahindra_Scorpio-N_Z8L_%28India%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'XUV700', 'type': 'SUV', 'price': '13.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/36/2021_Mahindra_XUV700_AX7_%28India%29_front_view.jpg'},
    {'make': 'Kia', 'model': 'Sonet', 'type': 'SUV', 'price': '7.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Kia_Sonet_%28facelift%29_IMG_8204.jpg'},
    {'make': 'Kia', 'model': 'Seltos', 'type': 'SUV', 'price': '10.90 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/36/Kia_Seltos_%28SP2%2C_facelift%29_IMG_8034.jpg'},
    {'make': 'Kia', 'model': 'Carens', 'type': 'SUV', 'price': '10.52 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/5/54/Kia_Carens_IMG_7013.jpg'},
    {'make': 'Toyota', 'model': 'Rumion', 'type': 'SUV', 'price': '10.44 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/1/1b/2022_Toyota_Rumion_Active_%28Egypt%29_front_view_01.png'},
    {'make': 'Toyota', 'model': 'Hyryder', 'type': 'SUV', 'price': '11.14 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/f/f6/2022_Toyota_Urban_Cruiser_Hyryder_V_Hybrid_%28India%29_front_view.jpg'},
    {'make': 'Toyota', 'model': 'Innova Crysta', 'type': 'SUV', 'price': '19.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/64/2021_Toyota_Kijang_Innova_2.4_V_Luxury_wagon_%28GUN142R%29_front.jpg'},
    {'make': 'Toyota', 'model': 'Fortuner', 'type': 'SUV', 'price': '33.43 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/d/dd/2016_Toyota_Fortuner_%28GUN155R%29_Crusade_wagon_%282016-10-21%29_01.jpg'},
    {'make': 'Honda', 'model': 'Elevate', 'type': 'SUV', 'price': '11.91 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/7/77/Honda_Elevate_IMG_8239.jpg'},
    {'make': 'Renault', 'model': 'Triber', 'type': 'SUV', 'price': '6.00 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/0/07/2019_Renault_Triber_RXZ_%28India%29_front_view.jpg'},
    {'make': 'Renault', 'model': 'Kiger', 'type': 'SUV', 'price': '6.00 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/1/1d/2021_Renault_Kiger_RXZ_Turbo_CVT_%28India%29_front_view.jpg'},
    {'make': 'Nissan', 'model': 'Magnite', 'type': 'SUV', 'price': '6.00 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/4/4e/2021_Nissan_Magnite_XV_Premium_Turbo_%28India%29_front_view.jpg'},
    {'make': 'Citroen', 'model': 'C3 Aircross', 'type': 'SUV', 'price': '9.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/f/f8/2018_Citroen_C3_Aircross_Flair_Puretec_1.2_Front.jpg'},
    {'make': 'MG', 'model': 'Hector', 'type': 'SUV', 'price': '13.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/2/22/MG_Hector_Plus_%28facelift%29_IMG_6562.jpg'},
    {'make': 'MG', 'model': 'Astor', 'type': 'SUV', 'price': '9.98 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/a/ae/MG_ZS_EV_%28facelift%29_IMG_6580.jpg'},
    {'make': 'Skoda', 'model': 'Kushaq', 'type': 'SUV', 'price': '10.89 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/5/52/2021_%C5%A0koda_Kushaq_%28India%29_front_view.png'},
    {'make': 'Volkswagen', 'model': 'Taigun', 'type': 'SUV', 'price': '11.70 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/6/62/2021_Volkswagen_Taigun_1.5_TSI_GT_%28India%29_front_view_02.png'},

    # --- EVs ---
    {'make': 'MG', 'model': 'Comet EV', 'type': 'EV', 'price': '6.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/36/2023_MG_Comet_EV_Plush_%28India%29.png'},
    {'make': 'Tata', 'model': 'Tiago EV', 'type': 'EV', 'price': '7.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/7/7d/Tata_Tiago_EV_XZ%2B_Tech_Lux_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Punch EV', 'type': 'EV', 'price': '10.99 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/c/c5/2024_Tata_Punch.ev_Empowered_%2B_%28India%29_front_view_01.jpg'},
    {'make': 'Citroen', 'model': 'eC3', 'type': 'EV', 'price': '11.61 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/c/c2/2022_Citro%C3%ABn_C3_Feel_PureTech_82_%28India%29_front_view.jpg'},
    {'make': 'Tata', 'model': 'Nexon EV', 'type': 'EV', 'price': '14.49 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/3/32/2023_Tata_Nexon.ev_Empowered_%2B_%28India%29_front_view.jpg'},
    {'make': 'Mahindra', 'model': 'XUV400', 'type': 'EV', 'price': '15.49 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/d/d9/2023_Mahindra_XUV400_EL_%28India%29_front_view.jpg'},
    {'make': 'MG', 'model': 'ZS EV', 'type': 'EV', 'price': '18.98 Lakh', 'img': 'https://upload.wikimedia.org/wikipedia/commons/a/ae/MG_ZS_EV_%28facelift%29_IMG_6580.jpg'},
]


@login_required
def recommend_car(request):
    recommendations = []
    form = CarRecommendationForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        vehicle_type = form.cleaned_data['vehicle_type']
        min_p = form.cleaned_data.get('min_price') or 0
        max_p = form.cleaned_data.get('max_price') or 100000000 

        for i, car in enumerate(BUDGET_CARS, 1):
            car_item = car.copy()
            car_item['id'] = str(i) 
            try:
                # Robustly extract number from "X Lakh" or "X"
                price_str = car_item['price'].replace(' Lakh', '').strip()
                price_val = float(price_str) * 100000
            except (ValueError, KeyError, AttributeError):
                price_val = 0 
                
            if min_p <= price_val <= max_p:
                if vehicle_type == 'Any' or car_item['type'] == vehicle_type:
                    recommendations.append(car_item)

        # Safety wrapper for Database query in case migrations are pending
        try:
            db_query = NewCar.objects.all()
            if vehicle_type != 'Any':
                db_query = db_query.filter(car_type=vehicle_type)
            
            for car in db_query:
                price_val = car.price_lakhs * 100000
                if min_p <= price_val <= max_p:
                    recommendations.append({
                        'id': f"db_{car.id}", 
                        'make': car.make,
                        'model': car.model,
                        'type': car.car_type,
                        'price': f"{car.price_lakhs} Lakh",
                        'img': car.vehicle_image.url if car.vehicle_image else None,
                        'is_db': True
                    })
        except (OperationalError, ProgrammingError):
            # If the database table or column is missing, skip the DB part
            # but still show the hardcoded results.
            pass
        
        # Resilient sorting key
        def get_price_numeric(item):
            try:
                p = item['price'].replace(' Lakh', '').strip()
                return float(p)
            except (ValueError, KeyError, AttributeError):
                return 0

        recommendations.sort(key=get_price_numeric)

    return render(request, 'core/recommend_car.html', {'form': form, 'cars': recommendations, 'search_performed': request.method == 'POST'})

@login_required
def car_detail(request, car_id):
    selected_car = None
    car_id_str = str(car_id) # Ensure it's a string

    # Check if it's a database entry
    if car_id_str.startswith('db_'):
        try:
            db_id = car_id_str.replace('db_', '')
            car_obj = get_object_or_404(NewCar, id=db_id)
            selected_car = {
                'make': car_obj.make, 
                'model': car_obj.model, 
                'type': car_obj.vehicle_type,
                'price': f"{car_obj.price_lakhs} Lakh", 
                'img': car_obj.vehicle_image.url if car_obj.vehicle_image else None,
                'description': car_obj.description or "No description available."
            }
        except Exception:
            pass
    else:
        # It's a static list entry (ID 1, 2, 3...)
        try:
            # Import BUDGET_CARS if not already at the top of the file
            # from .utils import BUDGET_CARS 
            index = int(car_id_str) - 1
            if 0 <= index < len(BUDGET_CARS):
                selected_car = BUDGET_CARS[index]
        except (ValueError, IndexError, NameError):
            pass

    if not selected_car:
        messages.error(request, "Car details not found.")
        return redirect('recommend_car')

    # FIX: Render the template with the car details instead of returning a boolean check
    return render(request, 'core/car_detail.html', {'car': selected_car})

def landing_page(request):
    return render(request, 'core/landing.html')


@login_required
def dashboard(request):
    # 1. Fetch User's Vehicles
    vehicles = Vehicle.objects.filter(owner=request.user)
    
    # 2. Basic Stats Calculations
    vehicle_count = vehicles.count()
    
    now = timezone.now()
    fuel_data = FuelLog.objects.filter(
        driver=request.user,
        date__month=now.month, 
        date__year=now.year
    ).aggregate(Sum('liters_filled'))
    total_fuel = fuel_data['liters_filled__sum'] or 0

    trip_data = TripLog.objects.filter(driver=request.user).aggregate(Sum('distance_km'))
    total_distance = trip_data['distance_km__sum'] or 0

    # =========================================================
    # 3. NOTIFICATION LOGIC (Added)
    # =========================================================
    notifications = []
    today = datetime.date.today()
    warning_period = datetime.timedelta(days=30) # Warn 30 days before

    for v in vehicles:
        # Check Insurance
        if v.insurance_expiry:
            days_left = (v.insurance_expiry - today).days
            if days_left < 0:
                notifications.append({'type': 'danger', 'msg': f"Insurance EXPIRED for {v.model_name}!"})
            elif days_left <= 30:
                notifications.append({'type': 'warning', 'msg': f"Insurance for {v.model_name} expires in {days_left} days."})

        # Check Pollution (PUC)
        if v.pollution_expiry:
            days_left = (v.pollution_expiry - today).days
            if days_left < 0:
                notifications.append({'type': 'danger', 'msg': f"PUC EXPIRED for {v.model_name}!"})
            elif days_left <= 30:
                notifications.append({'type': 'warning', 'msg': f"PUC for {v.model_name} expires in {days_left} days."})

    # =========================================================
    # 4. Valuation Result (Existing Logic)
    # =========================================================
    valuation_result = request.session.pop('valuation_result', None)
    valuation_vehicle = request.session.pop('valuation_vehicle', None)

    context = {
        'vehicles': vehicles,
        'vehicle_count': vehicle_count,
        'total_fuel': round(total_fuel, 1),
        'total_distance': round(total_distance, 1),
        'valuation_result': valuation_result, 
        'valuation_vehicle': valuation_vehicle,
        
        # Pass Notification Data to Template
        'notifications': notifications,          
        'notification_count': len(notifications), 
    }

    return render(request, 'core/dashboard.html', context)
    client = OpenAI(api_key="AIzaSyAqaSxZz876DrtFBnfkqYaj5zVPI4bCnt8") 
# core/views.py
@login_required
def analytics_dashboard(request):
    return render(request, 'core/analytics.html')
@csrf_exempt
def chat_with_ai(request):
    """
    Handles AI Chat requests.
    INJECTS: 
    1. Vehicle Expiry Data (Insurance, PUC, Fitness)
    2. Maintenance Predictions (Oil, Tyre, Service)
    3. Full Expense History
    4. Car Recommendations Data
    5. Action Links (Log Fuel, Log Trip)
    """
    if request.method == "POST":
        try:
            import google.generativeai as genai
            data = json.loads(request.body)
            user_message = data.get('message', '')

            # 2. GET API KEY
            settings_key = getattr(settings, 'GEMINI_API_KEY', None)
            HARDCODED_BACKUP = "AIzaSyAi9Ls-L3NVV-XBCrFpHD0d27aYZbHa2VE"
            api_key = settings_key if settings_key else HARDCODED_BACKUP
            api_key = str(api_key).strip()

            if not api_key or "YOUR_" in api_key:
                return JsonResponse({'reply': "Error: API Key is invalid."}, status=200)

            genai.configure(api_key=api_key)

            # 3. BUILD RICH CONTEXT
            system_context = ""
            today = datetime.date.today()
            
            if request.user.is_authenticated:
                # A. VEHICLE DEEP DIVE
                user_vehicles = Vehicle.objects.filter(owner=request.user, is_active=True)
                
                if user_vehicles.exists():
                    system_context += "USER'S FLEET STATUS:\n"
                    for v in user_vehicles:
                        # --- 1. Maintenance Logic (Replicated from vehicle_stats view) ---
                        if v.category == 'Two Wheeler':
                            intervals = {'oil': 3000, 'tyre': 25000, 'general': 2500}
                        else:
                            intervals = {'oil': 10000, 'tyre': 40000, 'general': 5000}
                        
                        maint_status = []
                        for m_type, interval in intervals.items():
                            last_log = MaintenanceLog.objects.filter(vehicle=v, service_type=m_type).order_by('-date').first()
                            if last_log:
                                last_km = last_log.odometer_reading
                                next_due = last_km + interval
                            else:
                                next_due = (int(v.current_odometer / interval) + 1) * interval
                            
                            remaining = next_due - v.current_odometer
                            status_str = "Overdue" if remaining < 0 else f"in {remaining} km"
                            maint_status.append(f"{m_type.title()} Service due {status_str} (Target: {next_due} km)")

                        # --- 2. Expiry Logic ---
                        expiry_alerts = []
                        if v.insurance_expiry:
                            days = (v.insurance_expiry - today).days
                            expiry_alerts.append(f"Insurance expires: {v.insurance_expiry} ({days} days left)")
                        else: expiry_alerts.append("Insurance: Not Set")
                        
                        if v.pollution_expiry:
                            days = (v.pollution_expiry - today).days
                            expiry_alerts.append(f"PUC expires: {v.pollution_expiry} ({days} days left)")
                        else: expiry_alerts.append("PUC: Not Set")

                        if v.fitness_expiry:
                            days = (v.fitness_expiry - today).days
                            expiry_alerts.append(f"Fitness expires: {v.fitness_expiry} ({days} days left)")

                        # --- 3. Fuel Stats ---
                        avg_data = FuelLog.objects.filter(vehicle=v, calculated_km_per_liter__gt=0).aggregate(Avg('calculated_km_per_liter'))
                        real_mileage = avg_data['calculated_km_per_liter__avg']
                        mileage_display = f"{round(real_mileage, 1)} km/l" if real_mileage else f"{v.target_mileage or 15} km/l (Est)"
                        
                        last_fuel = FuelLog.objects.filter(vehicle=v).order_by('-date').first()
                        last_fuel_price = f"₹{round(last_fuel.total_cost / last_fuel.liters_filled, 2)}/L" if last_fuel and last_fuel.liters_filled else "Unknown"

                        system_context += (
                            f"\nVEHICLE: {v.make} {v.model_name} ({v.fuel_type})\n"
                            f"  - Odometer: {v.current_odometer} km\n"
                            f"  - Mileage: {mileage_display}\n"
                            f"  - Last Known Fuel Price: {last_fuel_price}\n"
                            f"  - Documents: {'; '.join(expiry_alerts)}\n"
                            f"  - Maintenance Predictions: {'; '.join(maint_status)}\n"
                            f"  - LOGGING LINKS: Log Fuel -> /log_fuel/{v.id}/ | Log Trip -> /log_trip/ | Stats -> /vehicle/{v.id}/\n"
                        )
                else:
                    system_context += "User has no vehicles registered.\n"

                # B. GENERAL EXPENSES (Full History)
                expenses = ExpenseLog.objects.filter(user=request.user).order_by('-date')[:15] # Last 15
                total_misc = ExpenseLog.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
                
                system_context += f"\nEXPENSE HISTORY (Total: ₹{total_misc}):\n"
                if expenses.exists():
                    for e in expenses:
                        system_context += f"- {e.date}: {e.expense_type} (₹{e.amount})\n"
                else:
                    system_context += "- No extra expenses recorded.\n"

                # C. CAR RECOMMENDATION CONTEXT
                # We provide a summary of the BUDGET_CARS list so the AI knows what it can suggest
                car_db_sample = ", ".join([f"{c['make']} {c['model']} ({c['price']})" for c in BUDGET_CARS[:20]])
                system_context += f"\nAVAILABLE CAR DATABASE FOR SUGGESTIONS: {car_db_sample} ... and more.\n"

            else:
                system_context += "User is not logged in.\n"

            # 4. SYSTEM PROMPT
            system_instruction = f"""
            You are FuelPulse AI, an intelligent fleet manager.
            
            AUTHORIZED DATA ACCESS:
            {system_context}
            
            YOUR CAPABILITIES:
            1. **Alerts:** Tell the user immediately if Insurance, PUC, or Maintenance is overdue or expiring soon based on the data above.
            2. **Maintenance:** Predict when Oil, Tyre, or General Service is due based on the odometer data provided.
            3. **Fuel Price Prediction:** You cannot predict live market prices, but you MUST use the "Last Known Fuel Price" from the vehicle data to give an estimate. Say "Based on your last refill, petrol is approx..."
            4. **Car Suggestions:** If asked for a car within a budget, suggest from the Database list provided above.
            5. **Logging Actions:** If the user wants to log fuel or a trip, PROVIDE THE EXACT LINK from the vehicle data (e.g., "Click here: /log_fuel/1/").
            6. **Expense History:** You have access to the last 15 expenses. Summarize them if asked.
            
            Keep answers professional, helpful, and concise.
            """

            full_prompt = f"{system_instruction}\n\nUser: {user_message}\nAssistant:"

            # 5. GENERATE RESPONSE (Dynamic Fallback)
            reply_text = None
            
            try:
                # Try Flash first
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return JsonResponse({'reply': response.text})
            except Exception:
                pass 

            # Fallback discovery
            try:
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                available_models.sort(key=lambda x: 'flash' in x, reverse=True)

                for model_name in available_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(full_prompt)
                        if response and response.text:
                            reply_text = response.text
                            break
                    except Exception:
                        continue
            except Exception as e:
                return JsonResponse({'reply': f"AI Error: {str(e)}"}, status=200)

            if reply_text:
                return JsonResponse({'reply': reply_text})
            else:
                return JsonResponse({'reply': "I'm currently unable to process your request. Please check your internet connection or try again later."}, status=200)

        except Exception as e:
            return JsonResponse({'reply': f"System Error: {str(e)}"}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)



# --- STANDARD VIEWS (Unchanged below) ---
@login_required
def add_vehicle(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        
        # 1. Check if valid (Now pass because we made fields optional)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.owner = request.user
            
            # 2. Manually grab the Make/Model from the HTML dropdowns
            # (Because Django form might ignore them if they weren't in its initial choices)
            html_make = request.POST.get('make')
            html_model = request.POST.get('model_name')

            if html_make:
                vehicle.make = html_make
            if html_model:
                vehicle.model_name = html_model
                
            # 3. Handle Price (If missing, default to 1.5 Lakhs or 5 Lakhs)
            if not vehicle.purchase_price:
                vehicle.purchase_price = 150000.00 if "Two Wheeler" in str(vehicle.category) else 500000.00

            vehicle.save()
            
            messages.success(request, "Vehicle saved successfully!")
            return redirect('dashboard')
        else:
            # If it still fails, this prints the exact error to your terminal/console
            print("SAVE FAILED. Errors:", form.errors)
            messages.error(request, "Please check the form inputs.")
    else:
        form = VehicleForm()

    return render(request, 'core/add_vehicle.html', {'form': form})

@login_required
def remove_vehicle(request, vehicle_id):
    # 1. Get the specific vehicle owned by the user
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
    
    # 2. PERMANENTLY DELETE the vehicle and all associated logs (Fuel/Trips)
    vehicle.delete()
    
    # 3. Show success message and go back to dashboard
    messages.success(request, "Vehicle deleted successfully.")
    return redirect('dashboard')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def log_trip(request):
    if request.method == 'POST':
        form = TripLogForm(request.user, request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.driver = request.user
            trip.save()
            return redirect('dashboard')
    else:
        form = TripLogForm(request.user)
    return render(request, 'core/log_trip.html', {'form': form})


@login_required
def log_expense(request):
    if request.method == 'POST':
        form = ExpenseLogForm(request.user, request.POST, request.FILES)
        
        # --- AI OCR LOGIC (Runs before validation to auto-fill) ---
        if 'scan_receipt' in request.POST and request.FILES.get('receipt_image'):
            try:
                # 1. Read Image
                img = Image.open(request.FILES['receipt_image'])
                
                # 2. Extract Text
                # NOTE: Ensure Tesseract is installed on your OS!
                text = pytesseract.image_to_string(img)
                
                # 3. Find Amount (Regex for currency like 500.00)
                amounts = re.findall(r'\d+\.\d{2}', text)
                detected_amount = max(amounts) if amounts else 0
                
                messages.success(request, f"AI detected amount: ₹{detected_amount}")
                
                # Pre-fill form with detected data
                form = ExpenseLogForm(request.user, initial={'amount': detected_amount})
                
            except Exception as e:
                messages.error(request, f"OCR Failed: {str(e)}")
        
        elif form.is_valid():
            # Standard Save Logic
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('dashboard')

    else:
        form = ExpenseLogForm(request.user)
    
    return render(request, 'core/log_expense.html', {'form': form})

# core/views.py
# core/views.py


@login_required
def history(request):
    # 1. Get Filters from URL
    # 'filter_month' will come as "YYYY-MM" (e.g. "2025-12")
    filter_month = request.GET.get('filter_month')
    filter_type = request.GET.get('filter_type') # 'all', 'trip', 'fuel', 'expense'

    # 2. Base Queries
    trips = TripLog.objects.filter(driver=request.user)
    fuels = FuelLog.objects.filter(driver=request.user)
    expenses = ExpenseLog.objects.filter(user=request.user)

    # 3. Apply MONTH Filter (If selected)
    if filter_month:
        try:
            year, month = map(int, filter_month.split('-'))
            
            # Filter all queries by this Month & Year
            trips = trips.filter(date__year=year, date__month=month)
            fuels = fuels.filter(date__year=year, date__month=month) # FuelLog uses DateTime, but Django handles this
            expenses = expenses.filter(date__year=year, date__month=month)
        except ValueError:
            pass # Invalid date format, ignore

    # 4. Apply TYPE Filter (If selected)
    if filter_type == 'trip':
        fuels = FuelLog.objects.none()
        expenses = ExpenseLog.objects.none()
    elif filter_type == 'fuel':
        trips = TripLog.objects.none()
        expenses = ExpenseLog.objects.none()
    elif filter_type == 'expense':
        trips = TripLog.objects.none()
        fuels = FuelLog.objects.none()
    # If 'all' or None, we keep everything

    # 5. Label them for the template
    for t in trips: t.type = 'trip'
    for f in fuels: f.type = 'fuel'
    for e in expenses: e.type = 'expense'

    # 6. Sort Logic (Date normalization)
    def get_sort_date(obj):
        if hasattr(obj.date, 'date'):
            return obj.date.date()
        return obj.date

    timeline = sorted(
        chain(trips, fuels, expenses),
        key=get_sort_date, 
        reverse=True
    )
    
    context = {
        'timeline': timeline,
        'filter_month': filter_month,
        'filter_type': filter_type,
    }
    return render(request, 'core/history.html', context)
@login_required
def reports(request):
    # --- 1. PIE CHART DATA (Expense Distribution) ---
    
    # A. Get total Fuel Cost
    total_fuel_cost = FuelLog.objects.filter(driver=request.user).aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    
    # B. Get other Expenses grouped by Type (Service, Insurance, etc.)
    expense_data = ExpenseLog.objects.filter(user=request.user).values('expense_type').annotate(total=Sum('amount'))
    
    # C. Merge them for the Pie Chart
    pie_labels = ['Fuel'] # Start with Fuel
    pie_data = [float(total_fuel_cost)] # Start with Fuel Cost
    
    for item in expense_data:
        pie_labels.append(item['expense_type'])
        pie_data.append(float(item['total']))

    # --- 2. LINE CHART DATA (Monthly Spending Trend) ---
    
    # A. Group Fuel by Month
    fuel_monthly = FuelLog.objects.filter(driver=request.user)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('total_cost'))\
        .order_by('month')
    
    # B. Group Expenses by Month
    expense_monthly = ExpenseLog.objects.filter(user=request.user)\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'))\
        .order_by('month')

    # C. Merge them into a single Timeline Dictionary
    timeline_dict = {}
    
    # Add Fuel costs to timeline
    for item in fuel_monthly:
        if item['month']:
            m_str = item['month'].strftime('%B %Y') # e.g., "December 2025"
            timeline_dict[m_str] = timeline_dict.get(m_str, 0) + float(item['total'])

    # Add Other Expenses to timeline
    for item in expense_monthly:
        if item['month']:
            m_str = item['month'].strftime('%B %Y')
            timeline_dict[m_str] = timeline_dict.get(m_str, 0) + float(item['total'])

    # D. Separate into Lists for Chart.js (Sorted by Month logic not strictly enforced here but Dict insertion preserves order mostly)
    # For perfect sorting, we would sort keys, but this usually works fine for dashboard views
    line_labels = list(timeline_dict.keys())
    line_data = list(timeline_dict.values())

    # --- 3. CONTEXT ---
    context = {
        # Json dumps are needed so JavaScript can read these lists
        'pie_labels': json.dumps(pie_labels),
        'pie_data': json.dumps(pie_data),
        
        'line_labels': json.dumps(line_labels),
        'line_data': json.dumps(line_data),
        
        # Display Totals in Text
        'total_spent': sum(pie_data), # Grand Total (Fuel + Expenses)
        'fuel_spent': total_fuel_cost,
        'other_expenses': sum(pie_data) - float(total_fuel_cost)
    }
    
    return render(request, 'core/reports.html', context)

@login_required
def trip_calculator(request):
    result = None
    
    if request.method == 'POST':
        form = TripCalculatorForm(request.user, request.POST)
        
        if form.is_valid():
            vehicle = form.cleaned_data['vehicle']
            # Convert inputs to float immediately to prevent errors
            distance = float(form.cleaned_data['distance_km'])
            fuel_price = float(form.cleaned_data['fuel_price'])
            
            # --- 1. AI MILEAGE CALCULATION (Using your History) ---
            # Fetch last 10 logs for THIS vehicle
            history = FuelLog.objects.filter(vehicle=vehicle).order_by('-date')[:10]
            
            real_mileage = 0.0
            if history.exists():
                # Extract valid mileage logs
                valid_logs = [float(log.calculated_km_per_liter) for log in history if log.calculated_km_per_liter > 0]
                if valid_logs:
                    # Calculate Average from your history
                    real_mileage = sum(valid_logs) / len(valid_logs)
            
            # Fallback: If you haven't logged fuel yet, assume 15 km/l
            if real_mileage == 0:
                real_mileage = 15.0 
            
            # --- 2. COST ESTIMATION ---
            # Now we can safely divide because everything is a float
            fuel_needed = distance / real_mileage
            estimated_cost = fuel_needed * fuel_price
            
            result = {
                'vehicle': vehicle,
                'distance': distance,
                'real_mileage': round(real_mileage, 2),
                'fuel_needed': round(fuel_needed, 2),
                'estimated_cost': int(estimated_cost),
                'data_points': len(history) # Shows user how many past logs were used
            }
    else:
        form = TripCalculatorForm(request.user)

    return render(request, 'core/trip_calculator.html', {'form': form, 'result': result})
# In core/views.py




@login_required
def log_fuel(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
    
    if request.method == 'POST':
        form = FuelLogForm(request.POST)
        if form.is_valid():
            fuel_log = form.save(commit=False)
            fuel_log.vehicle = vehicle
            fuel_log.driver = request.user
            
            # --- 1. CALCULATE MILEAGE & COST (Fixed Decimal/Float Error) ---
            distance = fuel_log.odometer_reading - vehicle.current_odometer
            
            if distance > 0:
                # FIX: Convert Decimal fields to float for division
                liters = float(fuel_log.liters_filled)
                cost = float(fuel_log.total_cost)
                
                fuel_log.calculated_km_per_liter = distance / liters
                fuel_log.calculated_cost_per_km = cost / distance
                
                # --- 2. AI ANOMALY DETECTION (Z-Score) ---
                # Check previous logs to see if this mileage is "weird"
                past_logs = FuelLog.objects.filter(vehicle=vehicle).order_by('-date')[:10]
                
                # FIX: Convert database Decimals to floats immediately for Numpy
                mileages = [float(log.calculated_km_per_liter) for log in past_logs if log.calculated_km_per_liter > 0]
                
                if len(mileages) >= 3: # We need at least 3 logs to compare
                    mean = np.mean(mileages)
                    std_dev = np.std(mileages)
                    current_val = float(fuel_log.calculated_km_per_liter)
                    
                    if std_dev > 0:
                        z_score = abs((current_val - mean) / std_dev)
                        if z_score > 2: # Threshold for "Anomaly"
                            messages.warning(request, f"⚠️ AI Alert: Suspicious Mileage ({round(current_val, 2)} km/l). Your average is ~{round(mean, 2)}.")
            else:
                fuel_log.calculated_km_per_liter = 0
                fuel_log.calculated_cost_per_km = 0
            
            # --- 3. UPDATE VEHICLE ODOMETER ---
            if fuel_log.odometer_reading > vehicle.current_odometer:
                vehicle.current_odometer = fuel_log.odometer_reading
                vehicle.save()

            fuel_log.save()
            messages.success(request, "Fuel log added successfully!")
            return redirect('dashboard')
            
    else:
        # This handles the "GET" request (when you first load the page)
        form = FuelLogForm(initial={'date': timezone.now().date()})

    return render(request, 'core/log_fuel.html', {'form': form, 'vehicle': vehicle})

@login_required
def vehicle_stats(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
    
    # --- 1. FETCH FUEL DATA ---
    fuel_logs = FuelLog.objects.filter(vehicle=vehicle)
    total_fuel_cost = fuel_logs.aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    total_liters = fuel_logs.aggregate(Sum('liters_filled'))['liters_filled__sum'] or 0
    avg_mileage_data = fuel_logs.filter(calculated_km_per_liter__gt=0).aggregate(Avg('calculated_km_per_liter'))
    avg_mileage = avg_mileage_data['calculated_km_per_liter__avg'] or 0

    # --- 2. MAINTENANCE LOGIC ---
    
    # A. Define Intervals based on Category
    if vehicle.category == 'Two Wheeler':
        intervals = {'oil': 3000, 'tyre': 25000, 'general': 2500}
    else:
        intervals = {'oil': 10000, 'tyre': 40000, 'general': 5000}

    maintenance_data = {}
    current_odo = vehicle.current_odometer
    
    # B. Calculate Status for Each Type
    for m_type, interval in intervals.items():
        # 1. Fetch the Last Log for this specific type
        last_log = MaintenanceLog.objects.filter(vehicle=vehicle, service_type=m_type).order_by('-date').first()
        
        # 2. Determine Last KM and Last Date
        if last_log:
            last_km = last_log.odometer_reading
            # HERE IS THE FIX: We format the LAST UPDATED date to show on the card
            date_display = last_log.date.strftime('%d %b %Y')
            target_km = last_km + interval
        else:
            last_km = 0
            date_display = "Not Recorded" # Shows if you have never updated it
            # If never serviced, guess the next milestone based on current odometer
            target_km = (int(current_odo / interval) + 1) * interval
        
        remaining_km = target_km - current_odo
        
        # 3. Status Logic (Color coding)
        if remaining_km < 0:
            status = 'Overdue'
        elif remaining_km < (interval * 0.1):
            status = 'Critical'
        elif remaining_km < (interval * 0.2):
            status = 'Warning'
        else:
            status = 'Good'

        maintenance_data[m_type] = {
            'target_km': target_km,
            'remaining_km': remaining_km,
            'date': date_display, # <--- Now holds "Last Updated Date" instead of "Predicted Date"
            'status': status
        }

    # --- 3. CONTEXT ---
    context = {
        'vehicle': vehicle,
        'today': timezone.now().date(),
        'challan_link': "https://echallan.parivahan.gov.in/index/accused-challan",
        'avg_mileage': round(avg_mileage, 2),
        'total_fuel_cost': round(total_fuel_cost, 2),
        'total_liters': round(total_liters, 2),
        'maint': maintenance_data,
        
        # Note: 'next_service_prediction' used to show the date, now it shows last updated. 
        # You might want to remove this variable if you aren't using it elsewhere, 
        # but leaving it safe for now.
        'next_service_prediction': maintenance_data['general']['date'],
        'next_service_km': maintenance_data['general']['target_km']
    }
    
    return render(request, 'core/vehicle_stats.html', context)

@login_required
def update_maintenance(request, vehicle_id):
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        service_type = request.POST.get('service_type')
        date_str = request.POST.get('service_date')
        
        # 1. Get the Odometer reading from the form
        try:
            service_km = int(request.POST.get('service_km'))
        except (ValueError, TypeError):
            # Fallback to current odometer if user leaves it empty (safety)
            service_km = vehicle.current_odometer
        
        # 2. Save the log
        MaintenanceLog.objects.create(
            vehicle=vehicle,
            service_type=service_type,
            date=date_str,
            odometer_reading=service_km  # Save the manual input
        )
        
        messages.success(request, f"{service_type.title()} updated successfully! Next due date recalculated.")
        return redirect('vehicle_stats', vehicle_id=vehicle.id)
    
    return redirect('dashboard')


@login_required
def delete_history_item(request, item_type, item_id):
    # 1. Identify and find the object based on type
    if item_type == 'trip':
        item = get_object_or_404(TripLog, id=item_id, driver=request.user)
    elif item_type == 'fuel':
        item = get_object_or_404(FuelLog, id=item_id, driver=request.user)
        # Optional: You might want to reverse the odometer update here if needed, 
        # but for simplicity, we just delete the log.
    elif item_type == 'expense':
        item = get_object_or_404(ExpenseLog, id=item_id, user=request.user)
    else:
        messages.error(request, "Invalid record type.")
        return redirect('history')

    # 2. Delete it
    item.delete()
    messages.success(request, "Record deleted successfully.")
    
    # 3. Stay on history page
    return redirect('history')

@login_required
def profile(request):
    if request.method == 'POST' and 'username' in request.POST:
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if user_form.is_valid():
            user_form.save()
            # Removed success message - visual feedback is sufficient
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
    
    vehicles = Vehicle.objects.filter(owner=request.user)
    return render(request, 'core/profile.html', {
        'user_form': user_form,
        'vehicles': vehicles
    })


@login_required
def update_vehicle_docs(request, vehicle_id):
    """
    Updates vehicle document expiry dates and ownership type.
    Redirects the user back to the page they initiated the request from.
    """
    if request.method == 'POST':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
        
        # Update fields from POST data
        vehicle.ownership_type = request.POST.get('ownership_type', vehicle.ownership_type)
        
        # Capture date strings from the form
        insurance = request.POST.get('insurance_expiry')
        pollution = request.POST.get('pollution_expiry')
        fitness = request.POST.get('fitness_expiry')
        
        # Update only if dates are provided (to avoid clearing existing dates accidentally)
        if insurance:
            vehicle.insurance_expiry = insurance
        if pollution:
            vehicle.pollution_expiry = pollution
        if fitness:
            vehicle.fitness_expiry = fitness
        
        vehicle.save()
        messages.success(request, f"Documents for {vehicle.license_plate} updated successfully!")
        
        # SMART REDIRECT: Go back to the page the user came from (Stats or Profile)
        # fallback to 'profile' if the referer is missing
        return redirect(request.META.get('HTTP_REFERER', 'profile'))
    
    return redirect('profile')

    

# core/admin_views.py
from django.contrib.auth.decorators import login_required, user_passes_test # <--- You likely added this
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User

# ... other imports ...

# --- ADD THIS HELPER FUNCTION HERE ---
# Add these imports at the top if missing
import datetime
from django.contrib import messages
@login_required
def calculate_asset_value(request):
    if request.method == "POST":
        vehicle_id = request.POST.get('vehicle_id')
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)

        # --- 1. GET FACTORS (Updated for new form) ---
        
        # Ownership Factor
        # 1st: 100%, 2nd: 90%, 3rd: 80%, 4th: 70%, 5th: 60%
        ownership_map = {'1.0': 1.0, '0.9': 0.9, '0.8': 0.8, '0.7': 0.7, '0.6': 0.6}
        ownership_input = request.POST.get('ownership', '1.0')
        ownership_factor = ownership_map.get(ownership_input, 1.0)

        # Condition Factor
        condition_map = {'1.0': 1.0, '0.9': 0.9, '0.75': 0.75}
        condition_input = request.POST.get('condition', '1.0')
        condition_factor = condition_map.get(condition_input, 1.0)

        # Tyres Factor
        tyres_map = {'1.0': 1.0, '0.95': 0.95, '0.90': 0.90}
        tyres_input = request.POST.get('tyres', '1.0')
        tyre_factor = tyres_map.get(tyres_input, 1.0)

        # Maintenance Factor
        # Timely: +5% value, Avg: Normal, Irregular: -15% value
        maint_map = {'1.05': 1.05, '1.0': 1.0, '0.85': 0.85}
        maint_input = request.POST.get('maintenance', '1.0')
        maintenance_factor = maint_map.get(maint_input, 1.0)

        # --- 2. BASE PRICE ---
        base_price = float(vehicle.purchase_price)
        
        # Sanity check for default values
        if base_price == 500000.0 and "Two Wheeler" in str(vehicle.category):
            base_price = 150000.0
        elif base_price == 0:
            base_price = 500000.0

        # --- 3. AGE CALCULATION ---
        current_year = datetime.date.today().year
        p_year = vehicle.purchase_year if vehicle.purchase_year else (current_year - 5)
        age = current_year - p_year
        if age < 0: age = 0
        
        # Depreciation Logic
        if age == 0:
            age_factor = 0.95
        elif age == 1:
            age_factor = 0.80
        else:
            # 20% drop first year, 12% drop subsequent years
            age_factor = 0.80 * (0.88 ** (age - 1))

        # --- 4. "OLD IS GOLD" LOGIC ---
        if age >= 10:
            if condition_factor == 1.0 and maintenance_factor >= 1.0:
                age_factor += 0.05 

        # --- 5. FINAL CALCULATION ---
        final_value = base_price * age_factor * ownership_factor * condition_factor * tyre_factor * maintenance_factor
        
        # Floor value
        if final_value < 5000:
            final_value = 5000

        formatted_value = "{:,.0f}".format(int(final_value))
        
        request.session['valuation_result'] = formatted_value
        request.session['valuation_vehicle'] = f"{vehicle.make} {vehicle.model_name}"
        
        return redirect('dashboard')

    return redirect('dashboard')
def is_admin(user):
    return user.is_active and user.is_superuser

# ... existing views ...

@user_passes_test(is_admin, login_url='admin_login')
def manage_users(request):
    # Fetch all users EXCEPT the admins (to prevent accidental self-deletion)
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'core/admin/manage_users.html', {'users': users})

@user_passes_test(is_admin, login_url='admin_login')
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Flip the status: If True make False, if False make True
    if user.is_active:
        user.is_active = False
        messages.warning(request, f"User {user.username} has been suspended.")
    else:
        user.is_active = True
        messages.success(request, f"User {user.username} has been reactivated.")
    
    user.save()
    return redirect('manage_users')

@user_passes_test(is_admin, login_url='admin_login')
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    
    # Permanently delete
    user.delete()
    messages.error(request, f"User {username} and all their data were permanently deleted.")
    
    return redirect('manage_users')

# --- APPEND THIS TO THE BOTTOM OF core/views.py ---

# In core/views.py - Replace the bottom analytics functions with this:

@login_required
def manage_fleet_targets(request):
    vehicles = Vehicle.objects.filter(owner=request.user)
    # FIXED PATH: Changed 'core/admin/manage_fleet.html' -> 'core/manage_fleet.html'
    return render(request, 'core/manage_fleet.html', {'vehicles': vehicles})

@login_required
def set_targets(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id, owner=request.user)
    
    if request.method == 'POST':
        vehicle.target_mileage = float(request.POST.get('target_mileage', 0))
        vehicle.target_cost_per_km = float(request.POST.get('target_cost', 0))
        vehicle.save()
        messages.success(request, f"Targets updated for {vehicle.make} {vehicle.model_name}")
        return redirect('manage_fleet_targets')

    # FIXED PATH: Changed 'core/admin/set_targets.html' -> 'core/set_targets.html'
    return render(request, 'core/set_targets.html', {'vehicle': vehicle})

@login_required
def tco_report(request):
    vehicles = Vehicle.objects.filter(owner=request.user)
    report_data = []

    for v in vehicles:
        f_cost = FuelLog.objects.filter(vehicle=v).aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        e_cost = ExpenseLog.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
        
        total_km = v.current_odometer
        actual_cpk = (f_cost + e_cost) / total_km if total_km > 0 else 0
        
        report_data.append({
            'vehicle': v,
            'fuel_cost': f_cost,
            'expense_cost': e_cost,
            'total_tco': f_cost + e_cost,
            'actual_cpk': round(actual_cpk, 2)
        })

    # FIXED PATH: Changed 'core/admin/tco_report.html' -> 'core/tco_report.html'
    return render(request, 'core/tco_report.html', {'report': report_data})



def custom_logout_view(request):
    # 1. Check if the user is an admin/superuser BEFORE logging out
    if request.user.is_superuser:
        next_page = '/admin/login/'  # URL for Admin Login
    else:
        next_page = 'login'          # URL Name for User Login (check your urls.py name)

    # 2. Perform the actual logout
    logout(request)

    # 3. Redirect to the determined page
    return redirect(next_page)
@login_required
def what_if_analysis(request):
    vehicles = Vehicle.objects.filter(owner=request.user)
    analysis_data = []
    total_savings = 0

    for v in vehicles:
        actual_fuel_cost = FuelLog.objects.filter(vehicle=v).aggregate(Sum('total_cost'))['total_cost__sum'] or 0
        dist = v.current_odometer 

        if actual_fuel_cost > 0 and dist > 0:
            actual_fuel_float = float(actual_fuel_cost)
            ideal_cost = dist * v.target_cost_per_km
            savings = actual_fuel_float - ideal_cost
            
            if savings < 0: savings = 0
            
            total_savings += savings
            
            analysis_data.append({
                'vehicle': f"{v.make} {v.model_name}",
                'actual': round(actual_fuel_float, 2),
                'ideal': round(ideal_cost, 2),
                'savings': round(savings, 2)
            })

    context = {
        'analysis': analysis_data,
        'fleet_savings': round(total_savings, 2),
        'labels': json.dumps([x['vehicle'] for x in analysis_data]),
        'savings_data': json.dumps([x['savings'] for x in analysis_data])
    }
    # FIXED PATH: Changed 'core/admin/what_if.html' -> 'core/what_if.html'
    return render(request, 'core/what_if.html', context)