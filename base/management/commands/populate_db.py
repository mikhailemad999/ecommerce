from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from products.models import Category, Product, ProductSpecification, ProductImage, Review
from orders.models import ShippingCarrier, ShippingMethod, Order, OrderItem, ShippingAddress, ShipmentTracking, TrackingCheckpoint
from users.models import Profile, CustomerAddress
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Populates the database with production-scale sample data (Categories, Products, Specs, Shipping, Tracking, Customer Addresses)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Starting database population...'))

        # 1. Ensure Admin and Demo Customers exist
        admin_user, _ = User.objects.get_or_create(
            username='admin@example.com',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Alexander',
                'last_name': 'Vance',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()
        admin_profile, _ = Profile.objects.get_or_create(user=admin_user)
        admin_profile.phone_number = '+1 (415) 890-1234'
        admin_profile.loyalty_tier = 'Platinum'
        admin_profile.save()

        demo_customer, _ = User.objects.get_or_create(
            username='sophia.chen@example.com',
            defaults={
                'email': 'sophia.chen@example.com',
                'first_name': 'Sophia',
                'last_name': 'Chen',
                'is_staff': False,
            }
        )
        demo_customer.set_password('customer123')
        demo_customer.save()
        cust_profile, _ = Profile.objects.get_or_create(user=demo_customer)
        cust_profile.phone_number = '+1 (212) 555-8742'
        cust_profile.loyalty_tier = 'Gold'
        cust_profile.total_spent = 1450.00
        cust_profile.save()

        # Customer Addresses
        CustomerAddress.objects.get_or_create(
            user=demo_customer,
            title='Penthouse Residence',
            defaults={
                'full_name': 'Sophia Chen',
                'phone': '+1 (212) 555-8742',
                'street_address': '450 Lexington Avenue, Apt 38B',
                'city': 'New York',
                'state_province': 'NY',
                'postal_code': '10017',
                'country': 'United States',
                'is_default': True
            }
        )
        CustomerAddress.objects.get_or_create(
            user=demo_customer,
            title='Tech Design Studio',
            defaults={
                'full_name': 'Sophia Chen',
                'phone': '+1 (212) 555-8742',
                'street_address': '180 Varick Street, Floor 6',
                'city': 'New York',
                'state_province': 'NY',
                'postal_code': '10014',
                'country': 'United States',
                'is_default': False
            }
        )

        self.stdout.write(self.style.SUCCESS('Users & Customer Addresses initialized.'))

        # 2. Shipping Carriers & Shipping Methods
        fedex, _ = ShippingCarrier.objects.get_or_create(
            code='FEDEX',
            defaults={
                'name': 'FedEx Express Worldwide',
                'tracking_url_template': 'https://www.fedex.com/fedextrack/?trknbr={}',
                'contact_phone': '+1 (800) 463-3339',
                'website': 'https://www.fedex.com',
                'is_active': True
            }
        )
        dhl, _ = ShippingCarrier.objects.get_or_create(
            code='DHL',
            defaults={
                'name': 'DHL Express Global',
                'tracking_url_template': 'https://www.dhl.com/en/express/tracking.html?AWB={}',
                'contact_phone': '+1 (800) 225-5345',
                'website': 'https://www.dhl.com',
                'is_active': True
            }
        )
        ups, _ = ShippingCarrier.objects.get_or_create(
            code='UPS',
            defaults={
                'name': 'UPS Next Day Air',
                'tracking_url_template': 'https://www.ups.com/track?tracknum={}',
                'contact_phone': '+1 (800) 742-5877',
                'website': 'https://www.ups.com',
                'is_active': True
            }
        )

        # Shipping Methods
        standard_method, _ = ShippingMethod.objects.get_or_create(
            code='STANDARD',
            defaults={
                'name': 'Standard Ground Delivery',
                'carrier': fedex,
                'description': 'Reliable doorstep ground shipping within 3 to 5 business days.',
                'base_price': 5.00,
                'estimated_days_min': 3,
                'estimated_days_max': 5,
                'free_shipping_threshold': 100.00,
                'is_active': True
            }
        )
        express_method, _ = ShippingMethod.objects.get_or_create(
            code='EXPRESS',
            defaults={
                'name': 'Express Air Courier',
                'carrier': dhl,
                'description': 'Rapid priority air dispatch with dedicated courier tracking (1-2 days).',
                'base_price': 15.00,
                'estimated_days_min': 1,
                'estimated_days_max': 2,
                'free_shipping_threshold': 250.00,
                'is_active': True
            }
        )
        overnight_method, _ = ShippingMethod.objects.get_or_create(
            code='OVERNIGHT',
            defaults={
                'name': 'White-Glove VIP Overnight',
                'carrier': ups,
                'description': 'Guaranteed morning priority delivery with required signature authentication.',
                'base_price': 29.00,
                'estimated_days_min': 1,
                'estimated_days_max': 1,
                'free_shipping_threshold': None,
                'is_active': True
            }
        )
        self.stdout.write(self.style.SUCCESS('Carriers & Shipping Methods initialized.'))

        # 3. Categories
        categories_data = [
            {'name': 'Audio & Sound', 'icon': 'fa-headphones', 'description': 'Audiophile-grade wireless headphones, earbuds, and premium soundbars.'},
            {'name': 'Smartphones', 'icon': 'fa-mobile-screen', 'description': 'Flagship iOS and Android devices with advanced optical zoom and pro chips.'},
            {'name': 'Computing & Laptops', 'icon': 'fa-laptop', 'description': 'High-performance workstations, ultrabooks, and studio creative laptops.'},
            {'name': 'Gaming & Consoles', 'icon': 'fa-gamepad', 'description': 'Next-gen 4K gaming consoles, handhelds, and pro tournament peripherals.'},
            {'name': 'Wearables & Fitness', 'icon': 'fa-stopwatch', 'description': 'Titanium smartwatches, biometric trackers, and endurance sports gear.'},
            {'name': 'Cameras & Drones', 'icon': 'fa-camera', 'description': 'Cinema-grade mirrorless cameras, lenses, and 4K aerial photography drones.'},
            {'name': 'Smart Home & Office', 'icon': 'fa-house-signal', 'description': 'Connected smart displays, ambient smart lighting, and ergonomic setups.'},
        ]

        cat_map = {}
        for c in categories_data:
            obj, _ = Category.objects.get_or_create(
                name=c['name'],
                defaults={'icon': c['icon'], 'description': c['description'], 'is_active': True}
            )
            cat_map[c['name']] = obj

        self.stdout.write(self.style.SUCCESS('Categories initialized.'))

        # 4. Rich Product Catalog (21 Products)
        catalog = [
            # Audio & Sound
            {
                'name': 'AirPods Pro Max (2nd Gen)',
                'sku': 'APP-MAX-001',
                'category_name': 'Audio & Sound',
                'brand': 'Apple',
                'price': 549.99,
                'discount_price': 499.99,
                'countInStock': 18,
                'rating': 4.8,
                'numReviews': 42,
                'image': '/static/images/airpods.jpg',
                'is_featured': True,
                'tags': 'wireless, noise-cancelling, spatial audio, apple, premium',
                'weight_kg': 0.38,
                'description': 'Custom acoustic design paired with H2 computational audio delivers breathtaking high-fidelity sound, industry-leading Active Noise Cancellation, and Personalized Spatial Audio with dynamic head tracking.',
                'specs': [
                    ('Battery Life', 'Up to 30 hours playback'),
                    ('Connectivity', 'Bluetooth 5.3 + USB-C lossless'),
                    ('Noise Cancellation', 'Pro-level Adaptive ANC'),
                    ('Weight', '384.8 grams'),
                    ('Warranty', '2-Year LuxeCommerce Worldwide')
                ]
            },
            {
                'name': 'Sony WH-1000XM5 Wireless Headphones',
                'sku': 'SNY-XM5-BLK',
                'category_name': 'Audio & Sound',
                'brand': 'Sony',
                'price': 399.99,
                'discount_price': 348.00,
                'countInStock': 12,
                'rating': 4.9,
                'numReviews': 68,
                'image': '/static/images/airpods.jpg',
                'is_featured': True,
                'tags': 'sony, wireless, ldac, noise cancelling, travel',
                'weight_kg': 0.25,
                'description': 'With two processors and eight microphones, the WH-1000XM5 headphones elevate noise cancellation to unprecedented clarity. Integrated Auto NC Optimizer and 30-hour battery life ensure all-day comfort.',
                'specs': [
                    ('Battery Life', '30 Hours with Quick Charge (3 min = 3 hrs)'),
                    ('Codecs', 'LDAC, AAC, SBC'),
                    ('Drivers', '30mm Carbon Fiber composite'),
                    ('Microphones', '8 Beamforming mics with AI voice reduction'),
                    ('Warranty', '1-Year Official Manufacturer')
                ]
            },
            {
                'name': 'Bose QuietComfort Ultra Soundbar',
                'sku': 'BSE-QCU-01',
                'category_name': 'Audio & Sound',
                'brand': 'Bose',
                'price': 899.99,
                'discount_price': None,
                'countInStock': 8,
                'rating': 4.7,
                'numReviews': 24,
                'image': '/static/images/echodot.jpg',
                'is_featured': False,
                'tags': 'soundbar, dolby atmos, home theater, bose',
                'weight_kg': 5.80,
                'description': 'Immerse your living space in cinematic Dolby Atmos spatial acoustics. TrueSpace technology intelligently upmixes non-Atmos content for astonishing 3D depth and crystalline movie dialogue.',
                'specs': [
                    ('Audio Format', 'Dolby Atmos, Dolby TrueHD, TrueSpace'),
                    ('Inputs', 'HDMI eARC, Optical, AirPlay 2, Spotify Connect'),
                    ('Voice Control', 'Built-in Amazon Alexa & Google Assistant'),
                    ('Dimensions', '104.5 x 5.8 x 10.7 cm'),
                    ('Warranty', '2-Year Manufacturer')
                ]
            },

            # Smartphones
            {
                'name': 'iPhone 16 Pro Max 512GB Titanium',
                'sku': 'APL-IP16PM-512',
                'category_name': 'Smartphones',
                'brand': 'Apple',
                'price': 1399.99,
                'discount_price': 1299.99,
                'countInStock': 9,
                'rating': 4.9,
                'numReviews': 114,
                'image': '/static/images/iphone.jpg',
                'is_featured': True,
                'tags': 'iphone, flagship, titanium, a18 pro, camera pro',
                'weight_kg': 0.23,
                'description': 'Forged in grade-5 titanium with thinner borders surrounding a 6.9-inch Super Retina XDR display. Powered by the A18 Pro silicon chip with innovative Camera Control, 4K 120 fps Dolby Vision, and all-day battery.',
                'specs': [
                    ('Processor', 'Apple A18 Pro 3nm Silicon'),
                    ('Display', '6.9-inch Super Retina XDR 120Hz ProMotion'),
                    ('Main Camera', '48MP Fusion + 48MP Ultra-Wide + 5x Telephoto'),
                    ('Storage', '512GB NVMe'),
                    ('Build', 'Grade 5 Titanium + Ceramic Shield')
                ]
            },
            {
                'name': 'Samsung Galaxy S25 Ultra 5G',
                'sku': 'SMG-S25U-512',
                'category_name': 'Smartphones',
                'brand': 'Samsung',
                'price': 1299.99,
                'discount_price': 1199.99,
                'countInStock': 14,
                'rating': 4.8,
                'numReviews': 58,
                'image': '/static/images/iphone.jpg',
                'is_featured': True,
                'tags': 'samsung, galaxy, 200mp, snapdragon, s-pen',
                'weight_kg': 0.22,
                'description': 'The definitive Android flagship featuring the Snapdragon 8 Elite platform, embedded S Pen stylus, anti-reflective Gorilla Armor glass, and 200MP Quad Telephoto AI zoom architecture.',
                'specs': [
                    ('Processor', 'Snapdragon 8 Elite for Galaxy'),
                    ('Display', '6.8-inch Dynamic AMOLED 2X 2600 nits'),
                    ('Camera', '200MP Main + 50MP 5x + 50MP Ultra-Wide'),
                    ('Battery', '5000 mAh with 45W Fast Charging'),
                    ('Stylus', 'Embedded Bluetooth S Pen with Air Actions')
                ]
            },
            {
                'name': 'Google Pixel 9 Pro Fold',
                'sku': 'GGL-P9PF-256',
                'category_name': 'Smartphones',
                'brand': 'Google',
                'price': 1799.99,
                'discount_price': None,
                'countInStock': 5,
                'rating': 4.6,
                'numReviews': 19,
                'image': '/static/images/iphone.jpg',
                'is_featured': False,
                'tags': 'pixel, foldable, google, ai, tensor g4',
                'weight_kg': 0.26,
                'description': 'Google second-generation foldable engineered with fluid aerospace hinge mechanics, Super Actua Flex 8-inch inner display, Tensor G4 processor, and 7 years of Pixel OS drops.',
                'specs': [
                    ('Inner Screen', '8.0-inch Super Actua Flex LTPO OLED'),
                    ('Outer Screen', '6.3-inch Actua OLED 120Hz'),
                    ('Processor', 'Google Tensor G4 + Titan M2 security'),
                    ('RAM/Storage', '16GB RAM + 256GB Storage'),
                    ('Durability', 'IPX8 water resistance rating')
                ]
            },

            # Computing & Laptops
            {
                'name': 'MacBook Pro 16" M3 Max Studio',
                'sku': 'APL-MBP16-M3X',
                'category_name': 'Computing & Laptops',
                'brand': 'Apple',
                'price': 2499.99,
                'discount_price': 2299.99,
                'countInStock': 6,
                'rating': 5.0,
                'numReviews': 37,
                'image': '/static/images/iphone.jpg',
                'is_featured': True,
                'tags': 'macbook, m3 max, apple, workstation, 16-inch',
                'weight_kg': 2.15,
                'description': 'The ultimate pro laptop featuring 16-core CPU, 40-core GPU, Liquid Retina XDR screen with 1600 nits peak brightness, hardware-accelerated ray tracing, and unmatched 22-hour battery endurance.',
                'specs': [
                    ('CPU / GPU', 'Apple M3 Max (16 CPU, 40 GPU)'),
                    ('Memory', '48GB Unified Memory'),
                    ('Storage', '1TB High-Speed SSD (7.4 GB/s)'),
                    ('Screen', '16.2-inch Liquid Retina XDR (3456x2234)'),
                    ('Ports', '3x Thunderbolt 4, HDMI, SDXC, MagSafe 3')
                ]
            },
            {
                'name': 'Dell XPS 16 OLED Workstation',
                'sku': 'DEL-XPS16-OLED',
                'category_name': 'Computing & Laptops',
                'brand': 'Dell',
                'price': 1899.99,
                'discount_price': 1749.99,
                'countInStock': 8,
                'rating': 4.6,
                'numReviews': 29,
                'image': '/static/images/iphone.jpg',
                'is_featured': False,
                'tags': 'dell, xps, oled, intel core ultra, rtx',
                'weight_kg': 2.10,
                'description': 'Machined CNC aluminum chassis with seamless glass touchpad and 4K+ InfinityEdge OLED touch display. Equipped with Intel Core Ultra 9 and NVIDIA RTX 4070 Graphics.',
                'specs': [
                    ('Processor', 'Intel Core Ultra 9 185H (16 Cores, 5.1 GHz)'),
                    ('Graphics', 'NVIDIA GeForce RTX 4070 8GB GDDR6'),
                    ('Display', '16.3-inch 4K+ (3840x2400) OLED Touch 120Hz'),
                    ('RAM', '32GB LPDDR5x 7467 MT/s'),
                    ('Storage', '1TB PCIe 4.0 NVMe SSD')
                ]
            },
            {
                'name': 'ASUS ROG Zephyrus G16 Gaming Laptop',
                'sku': 'ASU-ROG-G16',
                'category_name': 'Computing & Laptops',
                'brand': 'ASUS',
                'price': 1999.99,
                'discount_price': None,
                'countInStock': 10,
                'rating': 4.8,
                'numReviews': 45,
                'image': '/static/images/playstation.jpg',
                'is_featured': True,
                'tags': 'asus, rog, gaming laptop, rtx 4080, oled 240hz',
                'weight_kg': 1.85,
                'description': 'An ultra-slim 1.49cm aluminum chassis housing a 2.5K 240Hz ROG Nebula OLED display with G-Sync, Intel Core Ultra 9 AI processor, and vapor chamber cooling architecture.',
                'specs': [
                    ('Processor', 'Intel Core Ultra 9 185H with NPU'),
                    ('Graphics', 'NVIDIA RTX 4080 12GB Laptop GPU (115W)'),
                    ('Display', '16-inch 2.5K (2560x1600) OLED 240Hz 0.2ms'),
                    ('Audio', '6-speaker array with dual force-cancelling woofers'),
                    ('Thickness', '1.49 cm CNC unibody')
                ]
            },

            # Gaming & Consoles
            {
                'name': 'Sony PlayStation 5 Pro 2TB',
                'sku': 'SNY-PS5-PRO',
                'category_name': 'Gaming & Consoles',
                'brand': 'Sony',
                'price': 699.99,
                'discount_price': None,
                'countInStock': 11,
                'rating': 4.9,
                'numReviews': 87,
                'image': '/static/images/playstation.jpg',
                'is_featured': True,
                'tags': 'playstation, ps5 pro, 4k 60fps, ray tracing, 2tb',
                'weight_kg': 3.10,
                'description': 'Experience enhanced graphical clarity with PlayStation Spectral Super Resolution (PSSR), advanced ray tracing, and ultra-high frame rates up to 120 fps on supported 4K displays.',
                'specs': [
                    ('Storage', '2TB Custom Ultra-High Speed NVMe SSD'),
                    ('Graphics Engine', 'Enhanced GPU with 67% more Compute Units'),
                    ('Upscaling', 'PSSR AI-Driven Spectral Resolution'),
                    ('Controller', 'DualSense Wireless with Adaptive Triggers'),
                    ('Network', 'Wi-Fi 7 + Gigabit Ethernet')
                ]
            },
            {
                'name': 'Nintendo Switch OLED Studio Edition',
                'sku': 'NTD-SW-OLED',
                'category_name': 'Gaming & Consoles',
                'brand': 'Nintendo',
                'price': 349.99,
                'discount_price': 319.99,
                'countInStock': 15,
                'rating': 4.7,
                'numReviews': 62,
                'image': '/static/images/playstation.jpg',
                'is_featured': False,
                'tags': 'nintendo, switch, oled, handheld, gaming',
                'weight_kg': 0.42,
                'description': 'Feast your eyes on vivid colors and crisp contrast with a 7-inch OLED screen. Features a wide adjustable kickstand, a dock with a wired LAN port, and 64GB of internal storage.',
                'specs': [
                    ('Screen', '7.0-inch Multi-touch OLED display'),
                    ('Modes', 'TV mode, Tabletop mode, Handheld mode'),
                    ('Storage', '64GB internal + MicroSD expansion up to 2TB'),
                    ('Audio', 'Enhanced onboard stereo speakers'),
                    ('Battery', '4.5 to 9.0 hours gameplay')
                ]
            },
            {
                'name': 'Logitech G PRO X Superlight 2 Gaming Mouse',
                'sku': 'LOG-GPX-SL2',
                'category_name': 'Gaming & Consoles',
                'brand': 'Logitech',
                'price': 159.99,
                'discount_price': 139.99,
                'countInStock': 22,
                'rating': 4.8,
                'numReviews': 53,
                'image': '/static/images/mouse.jpg',
                'is_featured': False,
                'tags': 'logitech, mouse, esports, wireless, 60g',
                'weight_kg': 0.06,
                'description': 'The icon of esports engineered lighter and faster. Weighing only 60 grams with LIGHTFORCE hybrid optical-mechanical switches and the HERO 2 sensor offering 32,000 DPI tracking.',
                'specs': [
                    ('Weight', '60 grams ultra-lightweight'),
                    ('Sensor', 'HERO 2 (100 - 32,000 DPI, 500+ IPS)'),
                    ('Polling Rate', 'Up to 4,000 Hz LIGHTSPEED Wireless'),
                    ('Battery Life', 'Up to 95 hours constant motion'),
                    ('Charging', 'USB-C + POWERPLAY Wireless Compatible')
                ]
            },

            # Wearables & Fitness
            {
                'name': 'Apple Watch Ultra 2 Black Titanium',
                'sku': 'APL-AWU2-BLK',
                'category_name': 'Wearables & Fitness',
                'brand': 'Apple',
                'price': 799.99,
                'discount_price': 749.99,
                'countInStock': 9,
                'rating': 4.9,
                'numReviews': 48,
                'image': '/static/images/airpods.jpg',
                'is_featured': True,
                'tags': 'apple watch, titanium, diving, gps, sports',
                'weight_kg': 0.06,
                'description': 'The ultimate sports and adventure watch crafted with a satin black titanium case, 3000 nits Always-On Retina display, precision dual-frequency GPS, and up to 72 hours in Low Power Mode.',
                'specs': [
                    ('Case', '49mm Aerospace-Grade Titanium with Sapphire Crystal'),
                    ('Brightness', '3000 nits peak display brightness'),
                    ('Water Resistance', '100m water resistant with EN13319 dive gauge'),
                    ('Sensors', 'ECG, Blood Oxygen, Depth Gauge, Water Temperature'),
                    ('Battery', '36 hours standard, up to 72 hours Low Power')
                ]
            },
            {
                'name': 'Garmin Fenix 8 Solar Sapphire 47mm',
                'sku': 'GRM-FNX8-SLR',
                'category_name': 'Wearables & Fitness',
                'brand': 'Garmin',
                'price': 999.99,
                'discount_price': None,
                'countInStock': 7,
                'rating': 4.8,
                'numReviews': 31,
                'image': '/static/images/airpods.jpg',
                'is_featured': False,
                'tags': 'garmin, multisport, solar, titanium, sapphire',
                'weight_kg': 0.07,
                'description': 'Multisport GPS smartwatch built for champions with solar charging lens, leakproof inductive buttons, built-in LED flashlight, and comprehensive endurance coaching metrics.',
                'specs': [
                    ('Battery', 'Up to 28 days in smartwatch mode with solar'),
                    ('Display', '1.3-inch Sunlight-Visible Memory-in-Pixel (MIP)'),
                    ('Mapping', 'Preloaded TopoActive maps with dynamic routing'),
                    ('Microphone & Speaker', 'Voice commands and phone calls on wrist'),
                    ('Bezel', 'DLC Coated Titanium')
                ]
            },

            # Cameras & Drones
            {
                'name': 'Canon EOS R5 Mark II Mirrorless Camera',
                'sku': 'CAN-R5M2-BODY',
                'category_name': 'Cameras & Drones',
                'brand': 'Canon',
                'price': 3999.99,
                'discount_price': 3799.99,
                'countInStock': 4,
                'rating': 4.9,
                'numReviews': 28,
                'image': '/static/images/camera.jpg',
                'is_featured': True,
                'tags': 'canon, mirrorless, 8k raw, 45mp, professional',
                'weight_kg': 0.74,
                'description': 'A creative tour de force with 45MP Back-Illuminated Stacked CMOS sensor, Accelerated Capture engine, 8K 60p RAW internal video, and next-generation Eye Control AF.',
                'specs': [
                    ('Sensor', '45 Megapixel Back-Illuminated Stacked Full-Frame'),
                    ('Video', '8K 60p RAW / 4K 120p 10-bit 4:2:2 without crop'),
                    ('Autofocus', 'Dual Pixel Intelligent AF with Action Priority'),
                    ('Continuous Shooting', 'Up to 30 fps electronic shutter'),
                    ('Stabilization', 'Up to 8.5 stops Coordinated In-Body IS')
                ]
            },
            {
                'name': 'Sony Alpha 7 IV Full-Frame Camera Kit',
                'sku': 'SNY-A7IV-KIT',
                'category_name': 'Cameras & Drones',
                'brand': 'Sony',
                'price': 2498.00,
                'discount_price': 2299.00,
                'countInStock': 6,
                'rating': 4.8,
                'numReviews': 52,
                'image': '/static/images/camera.jpg',
                'is_featured': False,
                'tags': 'sony, alpha, 33mp, 4k 60p, hybrid camera',
                'weight_kg': 0.66,
                'description': 'The groundbreaking hybrid creator camera with 33MP Exmor R back-illuminated sensor, BIONZ XR processing, Real-Time Eye AF for humans/animals/birds, and 10-bit S-Cinetone recording.',
                'specs': [
                    ('Sensor', '33.0MP Full-Frame Exmor R CMOS'),
                    ('ISO Range', '100-51200 (expandable to 50-204800)'),
                    ('Video', '4K 60p 10-bit 4:2:2 All-Intra'),
                    ('Viewfinder', '3.68M-dot Quad-VGA OLED EVF 120fps'),
                    ('Connectivity', 'USB 3.2 Gen 2 10Gbps live streaming')
                ]
            },
            {
                'name': 'DJI Mini 4 Pro Fly More Combo Drone',
                'sku': 'DJI-M4P-FMC',
                'category_name': 'Cameras & Drones',
                'brand': 'DJI',
                'price': 1099.00,
                'discount_price': 999.00,
                'countInStock': 8,
                'rating': 4.9,
                'numReviews': 41,
                'image': '/static/images/camera.jpg',
                'is_featured': True,
                'tags': 'dji, drone, 4k 60fps, omnidirectional, lightweight',
                'weight_kg': 0.249,
                'description': 'Under 249g regulation-free drone boasting omnidirectional obstacle sensing, 4K/60fps HDR true vertical shooting, 20km FHD video transmission, and up to 45 minutes flight time.',
                'specs': [
                    ('Takeoff Weight', '< 249 grams (no FAA registration required)'),
                    ('Camera', '1/1.3-inch CMOS with Dual Native ISO Fusion'),
                    ('Obstacle Sensing', 'Omnidirectional Vision System + 3D ToF'),
                    ('Video Transmission', 'DJI O4 up to 20 km range 1080p 60fps'),
                    ('Flight Time', 'Up to 45 mins with Intelligent Flight Battery Plus')
                ]
            },

            # Smart Home & Office
            {
                'name': 'Amazon Echo Show 10 (3rd Gen) Rotating Smart Display',
                'sku': 'AMZ-ES10-BLK',
                'category_name': 'Smart Home & Office',
                'brand': 'Amazon',
                'price': 249.99,
                'discount_price': 199.99,
                'countInStock': 16,
                'rating': 4.4,
                'numReviews': 36,
                'image': '/static/images/echodot.jpg',
                'is_featured': False,
                'tags': 'amazon, alexa, smart display, smart home, zigbee',
                'weight_kg': 2.56,
                'description': 'Designed to move with you: a 10.1-inch HD smart screen that automatically turns to stay in view during video calls, cooking recipes, and streaming shows with premium directional sound.',
                'specs': [
                    ('Display', '10.1-inch HD Touchscreen with motorized rotation'),
                    ('Camera', '13 MP with auto-framing and motion tracking'),
                    ('Audio', '2.1 system: 2 x 1.0" tweeters + 3.0" woofer'),
                    ('Hub Built-in', 'Zigbee + Matter + Thread smart home hub'),
                    ('Privacy', 'Built-in camera shutter & mic off switch')
                ]
            },
            {
                'name': 'Logitech MX Master 3S Wireless Performance Mouse',
                'sku': 'LOG-MXM3S-GRY',
                'category_name': 'Smart Home & Office',
                'brand': 'Logitech',
                'price': 99.99,
                'discount_price': 89.99,
                'countInStock': 25,
                'rating': 4.9,
                'numReviews': 92,
                'image': '/static/images/mouse.jpg',
                'is_featured': True,
                'tags': 'logitech, productivity, ergonomic, quiet clicks, mac windows',
                'weight_kg': 0.14,
                'description': 'Ergonomic masterpiece equipped with Quiet Click switches, 8,000 DPI any-surface glass tracking, and the MagSpeed electromagnetic scroll wheel capable of scrolling 1,000 lines per second.',
                'specs': [
                    ('Sensor', 'Darkfield High Precision (200 to 8000 DPI)'),
                    ('Scroll Wheel', 'MagSpeed Electromagnetic SmartShift'),
                    ('Battery', '500 mAh Li-Po (Up to 70 days per full charge)'),
                    ('Multi-Device', 'Easy-Switch between 3 computers with Flow'),
                    ('Recharging', 'USB-C fast charging (1 min = 3 hours use)')
                ]
            },
            {
                'name': 'Keychron Q1 Max Wireless Custom Mechanical Keyboard',
                'sku': 'KYC-Q1MAX-75',
                'category_name': 'Smart Home & Office',
                'brand': 'Keychron',
                'price': 219.99,
                'discount_price': None,
                'countInStock': 10,
                'rating': 4.8,
                'numReviews': 27,
                'image': '/static/images/mouse.jpg',
                'is_featured': False,
                'tags': 'keyboard, mechanical, custom, wireless, hot-swappable',
                'weight_kg': 1.82,
                'description': 'Full CNC machined aluminum body with double-gasket acoustic design, 2.4GHz wireless + Bluetooth connectivity, hot-swappable switches, and QMK/VIA key remapping capabilities.',
                'specs': [
                    ('Layout', '75% Compact with CNC Aluminum Rotary Knob'),
                    ('Connectivity', '2.4G (1000Hz polling) + Bluetooth 5.1 + Type-C'),
                    ('Switches', 'Gateron Jupiter Brown (Pre-lubed Tactile)'),
                    ('Acoustics', 'Double-gasket mount with IXPE sound absorbing foam'),
                    ('OS Compatibility', 'Mac, Windows, and Linux layouts included')
                ]
            },
            {
                'name': 'Philips Hue Gradient Lightstrip 2m Base Kit',
                'sku': 'PHL-HUE-GRAD2M',
                'category_name': 'Smart Home & Office',
                'brand': 'Philips',
                'price': 179.99,
                'discount_price': 149.99,
                'countInStock': 14,
                'rating': 4.7,
                'numReviews': 38,
                'image': '/static/images/echodot.jpg',
                'is_featured': False,
                'tags': 'smart lighting, rgb, gradient, homekit, matter',
                'weight_kg': 0.45,
                'description': 'Seamlessly blend multiple vibrant colors of light simultaneously along a flexible 2-meter LED strip. Syncs with screen entertainment, gaming consoles, and music playback.',
                'specs': [
                    ('Length', '2 meters (extendable up to 10 meters)'),
                    ('Lumen Output', '1800 lumens at 4000K'),
                    ('Color Capabilities', '16 million colors with dynamic gradient zones'),
                    ('Ecosystems', 'Apple HomeKit, Google Assistant, Alexa, Matter'),
                    ('Lifetime', '25,000 operational hours')
                ]
            }
        ]

        created_count = 0
        updated_count = 0

        for item in catalog:
            cat_obj = cat_map.get(item['category_name'])
            
            prod, created = Product.objects.update_or_create(
                sku=item['sku'],
                defaults={
                    'user': admin_user,
                    'name': item['name'],
                    'brand': item['brand'],
                    'category': item['category_name'],
                    'category_ref': cat_obj,
                    'price': item['price'],
                    'discount_price': item['discount_price'],
                    'countInStock': item['countInStock'],
                    'rating': item['rating'],
                    'numReviews': item['numReviews'],
                    'image': item['image'],
                    'is_featured': item['is_featured'],
                    'tags': item['tags'],
                    'weight_kg': item['weight_kg'],
                    'description': item['description'],
                    'is_active': True,
                }
            )

            # Specifications
            prod.specifications.all().delete()
            for idx, (spec_name, spec_val) in enumerate(item['specs']):
                ProductSpecification.objects.create(
                    product=prod,
                    name=spec_name,
                    value=spec_val,
                    order=idx
                )

            # Seed sample reviews if empty
            if prod.review_set.count() == 0:
                Review.objects.create(
                    product=prod,
                    user=demo_customer,
                    name='Sophia Chen',
                    rating=5,
                    comment=f'Outstanding performance and immaculate build quality. The {prod.name} exceeded all my expectations.'
                )
                Review.objects.create(
                    product=prod,
                    user=admin_user,
                    name='Marcus Brody',
                    rating=4 if prod.rating < 4.8 else 5,
                    comment='Premium packaging, rapid dispatch, and the precision engineering is immediately apparent.'
                )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Catalog updated: {created_count} new products created, {updated_count} enriched.'))

        # 5. Order Tracking Seed & Synchronization
        all_orders = Order.objects.all()
        tracking_count = 0

        for order in all_orders:
            # Set default shipping method if none
            if not order.shipping_method:
                order.shipping_method = standard_method if (order.totalPrice or 0) < 1000 else express_method
                order.save()

            tracking_num = order.tracking_code or f"LX-{order.id:04d}-{random.randint(10000, 99999)}-US"
            order.tracking_code = tracking_num

            # Determine tracking status based on order fields
            if order.isDelivered:
                status = 'DELIVERED'
            elif order.isPaid:
                status = random.choice(['IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DISPATCHED'])
            else:
                status = 'ORDER_PLACED'

            order.status = 'DELIVERED' if status == 'DELIVERED' else ('SHIPPED' if status in ['IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DISPATCHED'] else ('PAID' if order.isPaid else 'PENDING'))
            order.save()

            shipment, created = ShipmentTracking.objects.get_or_create(
                order=order,
                defaults={
                    'tracking_number': tracking_num,
                    'carrier': fedex if (order.id % 2 == 0) else dhl,
                    'carrier_name': 'FedEx Express Worldwide' if (order.id % 2 == 0) else 'DHL Express Global',
                    'current_status': status,
                    'origin_facility': 'LuxeCommerce Fulfillment Hub, San Jose CA',
                    'destination': f"{order.shippingaddress.city if hasattr(order, 'shippingaddress') and order.shippingaddress else 'San Francisco'}, USA",
                    'estimated_delivery': timezone.now() + timedelta(days=2),
                    'actual_delivery': timezone.now() if order.isDelivered else None,
                    'signature_required': (order.totalPrice or 0) > 500,
                }
            )

            # Checkpoints
            if shipment.checkpoints.count() == 0:
                base_time = order.createdAt or (timezone.now() - timedelta(days=3))
                
                TrackingCheckpoint.objects.create(
                    tracking=shipment,
                    status='ORDER_PLACED',
                    title='Electronic Shipping Info Received',
                    location='LuxeCommerce Hub, San Jose CA',
                    description='Order verified, packaged with security seals and awaiting carrier collection.',
                    timestamp=base_time
                )

                if status in ['DISPATCHED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED']:
                    TrackingCheckpoint.objects.create(
                        tracking=shipment,
                        status='DISPATCHED',
                        title='Picked Up by Carrier',
                        location='San Jose Logistics Gateway, CA',
                        description='Package scanned and departured from initial sort hub.',
                        timestamp=base_time + timedelta(hours=8)
                    )

                if status in ['IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED']:
                    TrackingCheckpoint.objects.create(
                        tracking=shipment,
                        status='IN_TRANSIT',
                        title='Arrived at Destination Sort Center',
                        location='Regional Air Gateway, JFK International, NY',
                        description='Package received in destination territory. Customs and security clearance completed.',
                        timestamp=base_time + timedelta(hours=22)
                    )

                if status in ['OUT_FOR_DELIVERY', 'DELIVERED']:
                    TrackingCheckpoint.objects.create(
                        tracking=shipment,
                        status='OUT_FOR_DELIVERY',
                        title='Out for Doorstep Delivery',
                        location='Local Distribution Depo, Manhattan NY',
                        description='Loaded onto final mile delivery van with courier agent.',
                        timestamp=base_time + timedelta(hours=34)
                    )

                if status == 'DELIVERED':
                    TrackingCheckpoint.objects.create(
                        tracking=shipment,
                        status='DELIVERED',
                        title='Delivered to Recipient',
                        location='Residence Front Door, Manhattan NY',
                        description='Signed and received in pristine condition.',
                        timestamp=base_time + timedelta(hours=38)
                    )

            tracking_count += 1

        self.stdout.write(self.style.SUCCESS(f'Shipment tracking initialized for {tracking_count} orders.'))
        self.stdout.write(self.style.SUCCESS('Successfully populated production-scale database!'))
