"""
tools/fetch_real_data.py - Real photographic dataset collector.

Downloads real Creative Commons photography for Asian Elephants, wildlife, and forest terrain into data/raw_real.
"""

import os
import urllib.request
from PIL import Image, ImageEnhance

def fetch_real_dataset():
    data_dir = 'data/raw_real'
    os.makedirs(data_dir, exist_ok=True)

    urls = {
        'elephant': [
            'https://upload.wikimedia.org/wikipedia/commons/9/98/Elephas_maximus_%28Bandipur%29.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/b/b2/Asian_Elephant_Anaimalai.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/6/63/Elephant_in_Kabini.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/3/37/African_Bush_Elephant.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/6/60/Asian_elephant_in_the_Wild.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/e/e0/Elephant_at_Periyar.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/d/d4/Elephant_At_Night.jpg'
        ],
        'other_animal': [
            'https://upload.wikimedia.org/wikipedia/commons/7/7a/Indian_Gaur.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/8/87/Wild_boar_in_forest.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/4/43/Spotted_deer_in_Nagarhole.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/1/1b/Cattle_in_field.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/7/7e/Indian_bison_gaur.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/5/5e/Wild_boar_adult.jpg'
        ],
        'no_animal': [
            'https://upload.wikimedia.org/wikipedia/commons/4/45/Western_Ghats_Forest.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/a/a4/Night_forest_landscape.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/5/52/Dirt_road_in_forest.jpg',
            'https://upload.wikimedia.org/wikipedia/commons/8/80/Forest_trees_fog.jpg'
        ]
    }

    headers = {'User-Agent': 'GajaAlertBot/1.0 (http://gajaalert.ai; contact@gajaalert.ai)'}

    total_downloaded = 0
    for cls, url_list in urls.items():
        cls_dir = os.path.join(data_dir, cls)
        os.makedirs(cls_dir, exist_ok=True)
        for idx, url in enumerate(url_list):
            fname = f"{cls}_photo_{idx+1:03d}.jpg"
            fpath = os.path.join(cls_dir, fname)
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = resp.read()
                    with open(fpath, 'wb') as f:
                        f.write(data)
                total_downloaded += 1
                print(f"  Downloaded {fname} ({len(data)} bytes)")

                # Generate dark/night variation
                with Image.open(fpath) as img:
                    img_rgb = img.convert('RGB')
                    enhancer = ImageEnhance.Brightness(img_rgb)
                    img_dark = enhancer.enhance(0.35)
                    night_fname = f"{cls}_photo_night_{idx+1:03d}.jpg"
                    night_fpath = os.path.join(cls_dir, night_fname)
                    img_dark.save(night_fpath, quality=90)
                    total_downloaded += 1

            except Exception as e:
                print(f"Warning fetching {url}: {e}")

    # Copy existing smoke samples into raw_real as well to create a diverse combined training set
    smoke_dir = 'data/raw_smoke'
    if os.path.exists(smoke_dir):
        for cls in ['elephant', 'other_animal', 'no_animal']:
            src_c = os.path.join(smoke_dir, cls)
            dst_c = os.path.join(data_dir, cls)
            if os.path.exists(src_c):
                for fn in os.listdir(src_c):
                    sp = os.path.join(src_c, fn)
                    dp = os.path.join(dst_c, f"smoke_{fn}")
                    if os.path.isfile(sp) and not os.path.exists(dp):
                        import shutil
                        shutil.copy2(sp, dp)

    print(f"\n[fetch_real_data] Successfully collected {total_downloaded} photographic samples in {data_dir}")

if __name__ == '__main__':
    fetch_real_dataset()
