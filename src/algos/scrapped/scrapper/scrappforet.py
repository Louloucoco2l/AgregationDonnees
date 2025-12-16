from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import csv, re, time


options = Options()
options.add_argument("--detach")
driver = webdriver.Chrome(options=options)

URL = "https://www.laforet.com/acheter/rechercher?filter%5Btypes%5D%5B%5D=house&filter%5Btypes%5D%5B%5D=apartment&filter%5Bcities%5D%5B%5D=75056&filter%5Bmax%5D="
driver.get(URL)

# cookies
try:
    WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
    ).click()
except:
    pass

previous_count = -1
while True:
    cards = driver.find_elements(By.CSS_SELECTOR, "article.border-border-gray.relative.flex.overflow-hidden.rounded-xl")
    current_count = len(cards)

    if current_count == previous_count:
        print(f" Fin du chargement — {current_count} annonces détectées.")
        break

    print(f" Annonces chargées : {current_count} — on continue...")
    previous_count = current_count

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.8)  

cards = driver.find_elements(By.CSS_SELECTOR, "article.border-border-gray.relative.flex.overflow-hidden.rounded-xl")

with open("../../data/scrapped/annonces_laforet_paris.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["type", "prix", "surface", "nb_pieces", "localisation", "details"])

    for i, card in enumerate(cards, 1):
        type_bien = prix = surface = nb_pieces = localisation = details = "non disponible"

        # TYPE
        for sel in ["h3.text-primary.font-semibold", "h3", "div.text-primary.font-semibold"]:
            try:
                type_bien = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                break
            except:
                pass

        # PRIX
        for sel in ["span.text-tertiary.font-bold", "div.text-tertiary.font-bold", "span.font-bold.text-right"]:
            try:
                prix = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                break
            except:
                pass

        # LOCALISATION
        for sel in ["span.font-bold.text-gray-600", "span.text-gray-600.font-bold", "div.text-gray-600.font-bold"]:
            try:
                localisation = card.find_element(By.CSS_SELECTOR, sel).text.strip()
                break
            except:
                pass

        # CARACTÉRISTIQUES
        try:
            caracs = card.find_element(By.CSS_SELECTOR, "div.text.flex.flex-wrap").text
        except:
            caracs = card.text

        m = re.search(r"(\d+)\s*(?:m²|m2)", caracs, re.I)
        if m: surface = f"{m.group(1)} m²"

        m = re.search(r"(\d+)\s*pièce", caracs, re.I)
        if m: nb_pieces = f"{m.group(1)} pièces"

        # DÉTAILS
        try:
            details = card.find_element(By.CSS_SELECTOR, "div.text.truncate").text.strip()
        except:
            pass

        print(f"{i}. {type_bien} | {prix} | {surface} | {nb_pieces} | {localisation} | {details}")
        w.writerow([type_bien, prix, surface, nb_pieces, localisation, details])

print("\n Scraping COMPLET terminé.")
driver.quit()
