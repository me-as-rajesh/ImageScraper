# Install required libraries
!pip install requests beautifulsoup4 selenium
!apt-get update
!apt install -y chromium-chromedriver

import requests
from bs4 import BeautifulSoup
import re
import base64
import urllib.parse
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from google.colab import files
import os

class ImageManager:
    def __init__(self):
        self.image_types = {
            'IMG': 'IMG',
            'TEXT': 'TEXT',
            'LINK': 'LINK',
            'INPUT_IMG': 'INPUT_IMG',
            'BACKGROUND': 'BACKGROUND',
            'DATAURL': 'DATAURL'
        }
        self.img_list = []

    def add_img(self, img_type, src, width=0, height=0):
        """Add an image to the list."""
        if src:
            self.img_list.append({
                'type': img_type,
                'src': src,
                'width': width,
                'height': height
            })

    def get_unique_images_srcs(self):
        """Return unique image URLs."""
        images = self.img_list
        images_str_array = [img['src'] for img in images]
        # Deduplicate while preserving order
        seen = set()
        uniques = [x for x in images_str_array if not (x in seen or seen.add(x))]
        return uniques

    def get_images(self, url, use_selenium=False):
        """Scrape images from the given URL."""
        self.img_list = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            if use_selenium:
                # Set up Selenium
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                time.sleep(2)  # Wait for dynamic content
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                # Fetch HTML with requests
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

            base_url = url

            # Extract <img> tags
            imgs = soup.find_all('img')
            for img in imgs:
                src = img.get('src') or img.get('currentSrc')
                if src:
                    src = urljoin(base_url, src)
                    # Simulate naturalWidth/Height by loading image (optional, resource-intensive)
                    width = int(img.get('width', 0)) or 0
                    height = int(img.get('height', 0)) or 0
                    self.add_img(self.image_types['IMG'], src, width, height)

            # Extract <source> tags (from <picture>)
            sources = soup.find_all('source')
            for source in sources:
                srcset = source.get('srcset')
                if srcset:
                    src = urljoin(base_url, srcset.split(',')[0].strip().split(' ')[0])
                    self.add_img(self.image_types['IMG'], src, 0, 0)

            # Extract <img> with srcset
            srcsets = soup.find_all('img', srcset=True)
            for img in srcsets:
                srcset = img.get('srcset')
                if srcset:
                    for src in srcset.split(','):
                        src = src.strip().split(' ')[0]
                        if src:
                            src = urljoin(base_url, src)
                            self.add_img(self.image_types['IMG'], src, 0, 0)

            # Extract <input type="image">
            inputs = soup.find_all('input', type='image')
            for input_tag in inputs:
                src = input_tag.get('src')
                if src:
                    src = urljoin(base_url, src)
                    self.add_img(self.image_types['INPUT_IMG'], src, 0, 0)

            # Extract <a> tags with image extensions
            links = soup.find_all('a')
            image_extensions = ['.jpg', '.jpeg', '.bmp', '.ico', '.gif', '.png', '.webp', '.svg', '.tif', '.apng', '.jfif', '.pjpeg', '.pjp']
            for link in links:
                href = link.get('href')
                if href and any(href.lower().endswith(ext) for ext in image_extensions):
                    href = urljoin(base_url, href)
                    self.add_img(self.image_types['LINK'], href, 0, 0)

            # Extract <svg> as data URLs
            svgs = soup.find_all('svg')
            for svg in svgs:
                svg_str = str(svg)
                data_url = f"data:image/svg+xml;base64,{base64.b64encode(svg_str.encode('utf-8')).decode('utf-8')}"
                self.add_img(self.image_types['DATAURL'], data_url, 0, 0)

            # Extract background images from CSS
            all_elements = soup.find_all()
            for element in all_elements:
                style = element.get('style', '')
                if style:
                    # Check for background-image and background
                    for prop in ['background-image', 'background']:
                        matches = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style)
                        for src in matches:
                            src = urljoin(base_url, src)
                            self.add_img(self.image_types['BACKGROUND'], src, 0, 0)

            # Extract image URLs from text (innerHTML equivalent)
            body_text = soup.body.get_text() if soup.body else ''
            url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b[-a-zA-Z0-9@:%_\+.~#?//=]*'
            urls = re.findall(url_pattern, body_text)
            for url in urls:
                if any(url.lower().endswith(ext) for ext in image_extensions):
                    self.add_img(self.image_types['LINK'], url, 0, 0)

            # Shadow DOM handling (requires Selenium)
            if use_selenium:
                try:
                    shadow_imgs = driver.execute_script("""
                        function querySelectorAllShadows(selector, element = document.body) {
                            const childShadows = Array.from(element.querySelectorAll('*'))
                                .map(el => el.shadowRoot)
                                .filter(Boolean);
                            const childResults = childShadows.map(child => querySelectorAllShadows(selector, child));
                            const result = Array.from(element.querySelectorAll(selector));
                            return result.concat(childResults.flat());
                        }
                        return querySelectorAllShadows('img').map(img => ({
                            src: img.src || img.currentSrc || '',
                            width: img.width || img.naturalWidth || 0,
                            height: img.height || img.naturalHeight || 0
                        }));
                    """)
                    for img in shadow_imgs:
                        if img['src']:
                            src = urljoin(base_url, img['src'])
                            self.add_img(self.image_types['IMG'], src, img['width'], img.height)
                except Exception as e:
                    print(f"Error processing shadow DOM: {e}")
                driver.quit()

            return {
                'images': self.get_unique_images_srcs(),
                'title': soup.title.string if soup.title else '',
                'isTop': True,  # Simplified, no window.top check in Python
                'origin': urllib.parse.urlparse(url).scheme + '://' + urllib.parse.urlparse(url).netloc
            }

        except Exception as e:
            print(f"Error retrieving images: {e}")
            return {'images': [], 'title': '', 'isTop': True, 'origin': ''}

def download_images(image_urls, max_images=5):
    """Download a limited number of images to verify results."""
    os.makedirs('downloaded_images', exist_ok=True)
    downloaded = 0
    for i, url in enumerate(image_urls):
        if downloaded >= max_images:
            break
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            # Generate a safe filename
            filename = os.path.join('downloaded_images', f"image_{i+1}.{url.split('.')[-1].split('?')[0]}")
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded: {filename}")
            downloaded += 1
        except Exception as e:
            print(f"Error downloading {url}: {e}")

# Main execution
url = input("Enter the webpage URL (e.g., https://en.wikipedia.org/wiki/Cat): ").strip()
if not url:
    url = "https://en.wikipedia.org/wiki/Cat"  # Default URL

# Initialize ImageManager
image_manager = ImageManager()

# Scrape images (use Selenium for shadow DOM if needed)
result = image_manager.get_images(url, use_selenium=False)  # Set to True for shadow DOM

# Output results
print("\nResults:")
print(f"Page Title: {result['title']}")
print(f"Origin: {result['origin']}")
print(f"Number of Unique Images Found: {len(result['images'])}")
print("\nImage URLs:")
for img_url in result['images']:
    print(img_url)

# Download up to 5 images to verify
if result['images']:
    print("\nDownloading up to 5 images...")
    download_images(result['images'])
    print("\nDownloaded images are available in the 'downloaded_images' folder.")
    print("You can view them in the Colab file explorer (left sidebar).")

# Provide option to download results as a text file
with open('image_urls.txt', 'w') as f:
    f.write(f"Page Title: {result['title']}\n")
    f.write(f"Origin: {result['origin']}\n")
    f.write(f"Number of Images: {len(result['images'])}\n\n")
    f.write("Image URLs:\n")
    for url in result['images']:
        f.write(f"{url}\n")
print("\nResults saved to 'image_urls.txt'. Downloading file...")
files.download('image_urls.txt')
