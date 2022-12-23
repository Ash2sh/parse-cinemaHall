import datetime
from time import sleep

from fake_useragent import UserAgent
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

userAgent = UserAgent()

options = webdriver.ChromeOptions()

options.add_argument(f"user-agent={userAgent.random}")
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_argument("--headless")

s = Service("Path to ChromeDriver")


def get_data(url: str):
    driver = webdriver.Chrome(
        service=s,
        options=options,
    )

    wait = WebDriverWait(driver, 10)
    action = ActionChains(driver)

    info = {}

    driver.get(url=url)
    sleep(2)

    buttons = driver.find_elements(By.CLASS_NAME, "releases-item-schedule")
    for i in buttons:
        try:
            action.move_to_element_with_offset(
                i.find_element(By.CLASS_NAME, "widget-overlay"), 5, 5
            ).click().perform()
            driver.switch_to.frame(driver.find_element(By.CLASS_NAME, "kw-iframe"))
        except Exception:
            continue

        if wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "hall-legend__prices"))
        ):
            movieType = []
            movieHall = []
            moviePrices = []

            seances = driver.find_element(
                By.CLASS_NAME, "hall-schema-popup-seances"
            ).find_elements(By.CLASS_NAME, "seance-item")
            for i in seances:
                i.click()
                if wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "hall-legend__prices"))
                ):
                    movieInfo = driver.find_element(
                        By.CLASS_NAME, "hall-legend__seance-info"
                    ).find_elements(By.TAG_NAME, "span")

                    movieType.append(movieInfo[0].text)
                    movieHall.append(movieInfo[-1].text)

                    moviePriceList = driver.find_element(
                        By.CLASS_NAME, "hall-legend__prices"
                    ).find_elements(By.CLASS_NAME, "hall-legend__item")
                    moviePrices += [
                        int(i.text[:-1]) for i in moviePriceList if i.text != "Занято"
                    ]

            movieName = driver.find_element(
                By.CLASS_NAME, "hall-schema-popup__title"
            ).text
            movieTime = driver.find_element(
                By.CLASS_NAME, "hall-schema-popup-seances"
            ).text.split()
            moviePrice = f"{min(moviePrices)}-{max(moviePrices)}"

            info.update(
                {
                    movieName: {
                        "time": movieTime,
                        "price": moviePrice,
                        "view": list(set(movieType)),
                        "hall": list(set(movieHall)),
                    }
                }
            )

            driver.find_element(By.CLASS_NAME, "popup-close-icon").click()
            driver.switch_to.parent_frame()

    driver.close()

    return info


def create_xml(info: dict):
    page = etree.Element("data")

    for date, movieInfo in info.items():
        date = etree.SubElement(page, "date", attrib={"date": date})

        key = lambda x: datetime.datetime.strptime(x[1].get("time")[0], "%H:%M")
        movieInfo = dict(sorted(movieInfo.items(), key=key))

        for name, i in movieInfo.items():
            elName = etree.SubElement(date, "name", attrib={"name": name})

            for tag, text in i.items():
                tag = etree.SubElement(elName, tag)
                tag.text = ", ".join(text) if type(text) == list else text
    return page


def main():
    date = datetime.datetime.today().date()

    info = {}

    for i in range(7):
        print(i)
        try:
            data = get_data(f"https://cinemahall24.ru/?date={date}")
        except Exception:
            data = get_data(f"https://cinemahall24.ru/?date={date}")

        info.update({str(date): data})

        date += datetime.timedelta(days=1)

    page = create_xml(info)
    etree.ElementTree(page).write(
        "./data/data.xml", xml_declaration=True, pretty_print=True, encoding="utf-8"
    )


if __name__ == "__main__":
    main()
