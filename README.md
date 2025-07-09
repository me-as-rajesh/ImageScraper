How to Use in Google Colab
Open Google Colab: Go to colab.research.google.com and create a new notebook.
Paste the Code: Copy and paste the above code into a code cell.
Run the Code:
The code installs required libraries (requests, beautifulsoup4, selenium, and Chromium WebDriver).
Prompts you to enter a URL (defaults to https://en.wikipedia.org/wiki/Cat if empty).
Scrapes images from the webpage using BeautifulSoup (and optionally selenium for shadow DOM).
Outputs unique image URLs, the page title, and origin.
Downloads up to 5 images to a downloaded_images folder for verification.
Saves the results to image_urls.txt and automatically downloads it.
Check Output:
Console Output: Displays the page title, origin, number of images, and each image URL.
Downloaded Images: Up to 5 images are saved in the downloaded_images folder, visible in the Colab file explorer (left sidebar).
Text File: image_urls.txt contains all results and is downloaded automatically.
Optional Selenium:
The code defaults to use_selenium=False for simplicity, as Wikipedia’s images are static.
Set use_selenium=True to handle shadow DOM or dynamic content (increases runtime due to browser initialization).
